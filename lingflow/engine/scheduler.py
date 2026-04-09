"""
DAG Scheduler — 有向无环图调度器

解析 DAG、执行节点、收集结果、处理错误。
"""

import asyncio
import importlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from lingflow.engine.flow import Flow, FlowStatus, NodeStatus

logger = logging.getLogger(__name__)


class DAGScheduler:
    def __init__(self, max_concurrent: int = 4):
        self._max_concurrent = max_concurrent
        self._running: Dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, flow: Flow, context: Optional[Dict[str, Any]] = None) -> Flow:
        ctx = context or {}
        errors = flow.validate()
        if errors:
            flow.status = FlowStatus.FAILED
            flow.metadata["validation_errors"] = errors
            return flow

        flow.status = FlowStatus.RUNNING
        flow.started_at = datetime.now()

        entry_nodes = flow.get_entry_nodes()
        completed: Dict[str, Dict[str, Any]] = {}
        failed_nodes: set = set()
        running_nodes: set = set()

        ready = set(entry_nodes)
        all_done = False

        while not all_done:
            if not ready and not running_nodes:
                break

            tasks = []
            for nid in list(ready):
                if nid in failed_nodes or any(
                    p in failed_nodes for p in flow.get_predecessors(nid)
                ):
                    flow.nodes[nid].status = NodeStatus.SKIPPED
                    ready.discard(nid)
                    continue

                running_nodes.add(nid)
                ready.discard(nid)
                task = asyncio.create_task(self._execute_node(flow, nid, ctx, completed))
                tasks.append((nid, task))

            if not tasks:
                remaining = ready | running_nodes
                if remaining:
                    for nid in remaining:
                        flow.nodes[nid].status = NodeStatus.SKIPPED
                    ready.clear()
                    running_nodes.clear()
                break

            done_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

            for (nid, _), result in zip(tasks, done_results):
                running_nodes.discard(nid)
                if isinstance(result, Exception):
                    flow.nodes[nid].status = NodeStatus.FAILED
                    flow.nodes[nid].error = str(result)
                    failed_nodes.add(nid)
                    logger.error(f"Node {nid} failed: {result}")
                else:
                    flow.nodes[nid].status = NodeStatus.SUCCESS
                    completed[nid] = result or {}
                    for succ in flow.get_successors(nid):
                        preds = flow.get_predecessors(succ)
                        if all(p in completed for p in preds):
                            ready.add(succ)

            all_done = not ready and not running_nodes

        flow.finished_at = datetime.now()
        flow.results = completed

        if failed_nodes:
            flow.status = FlowStatus.FAILED
        else:
            flow.status = FlowStatus.SUCCESS
            flow.updated_at = datetime.now()

        logger.info(f"Flow {flow.flow_id} finished: {flow.status.value}")
        return flow

    async def _execute_node(
        self,
        flow: Flow,
        node_id: str,
        context: Dict[str, Any],
        completed: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        node = flow.nodes[node_id]
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.now()

        predecessor_outputs = {}
        for pred_id in flow.get_predecessors(node_id):
            predecessor_outputs[pred_id] = completed.get(pred_id, {})

        node_ctx = {
            **context,
            "predecessor_outputs": predecessor_outputs,
            "node_config": node.config,
            "flow_id": flow.flow_id,
        }

        async with self._semaphore:
            try:
                if node.handler:
                    if asyncio.iscoroutinefunction(node.handler):
                        result = await node.handler(node_ctx)
                    else:
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, node.handler, node_ctx
                        )
                elif node.handler_path:
                    result = await self._call_handler(node.handler_path, node_ctx)
                else:
                    result = {"status": "skipped", "reason": "no handler"}
            finally:
                node.finished_at = datetime.now()

        node.outputs = result or {}
        return node.outputs

    async def _call_handler(self, handler_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        module_path, func_name = handler_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        if asyncio.iscoroutinefunction(handler):
            return await handler(context)
        return handler(context)

    def cancel(self, flow_id: str) -> bool:
        task = self._running.get(flow_id)
        if task and not task.done():
            task.cancel()
            return True
        return False
