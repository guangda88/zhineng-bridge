#!/usr/bin/env python3
"""
智桥协作工作流引擎

功能：
1. 任务智能分配 - 根据AI能力自动选择最合适的Agent
2. 链式协作 - 多个Agent按顺序完成复杂任务
3. 并行处理 - 同时使用多个Agent提高效率
4. 结果聚合 - 智能合并多个Agent的输出
5. 实时反馈 - 工作流执行进度追踪
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class TaskType(Enum):
    """任务类型"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    MULTI_MODAL = "multi_modal"

class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class AgentTask:
    """Agent任务"""
    def __init__(self, agent_id: str, task_type: TaskType, input_data: Dict[str, Any]):
        self.agent_id = agent_id
        self.task_type = task_type
        self.input_data = input_data
        self.output_data: Optional[Dict[str, Any]] = None
        self.status = "pending"
        self.error: Optional[str] = None
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_type": self.task_type.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

class Workflow:
    """工作流"""
    def __init__(self, workflow_id: str, name: str, description: str):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.tasks: List[AgentTask] = []
        self.status = WorkflowStatus.PENDING
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None

    def add_task(self, task: AgentTask):
        """添加任务"""
        self.tasks.append(task)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "tasks": [task.to_dict() for task in self.tasks],
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "result": self.result
        }

class WorkflowEngine:
    """工作流引擎"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}

    def register_agent_capabilities(self, agent_id: str, capabilities: List[str]):
        """注册Agent能力"""
        self.agent_capabilities[agent_id] = capabilities
        print(f"✅ Agent {agent_id} 能力已注册: {', '.join(capabilities)}")

    def find_best_agent(self, required_capability: str) -> Optional[str]:
        """查找最适合的Agent"""
        best_agent = None
        best_score = 0

        for agent_id, capabilities in self.agent_capabilities.items():
            # 简单匹配：只要有能力就优先选择
            if required_capability in capabilities:
                # 这里可以实现更复杂的评分逻辑
                best_agent = agent_id
                best_score = 1
                break  # 找到第一个就返回

        return best_agent

    def create_workflow(self, name: str, description: str) -> Workflow:
        """创建工作流"""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.workflows)}"
        workflow = Workflow(workflow_id, name, description)
        self.workflows[workflow_id] = workflow
        print(f"✅ 工作流已创建: {workflow_id}")
        return workflow

    async def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """执行工作流"""
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now().isoformat()
        print(f"\n🚀 开始执行工作流: {workflow.name}")

        try:
            # 执行所有任务
            for task in workflow.tasks:
                print(f"\n📝 执行任务: {task.agent_id} -> {task.task_type.value}")
                task.status = "running"
                task.start_time = datetime.now().isoformat()

                # 模拟任务执行
                await self._execute_task(task)

                task.end_time = datetime.now().isoformat()

                if task.status == "failed":
                    print(f"❌ 任务失败: {task.error}")
                    workflow.status = WorkflowStatus.FAILED
                    break

            # 聚合结果
            if workflow.status != WorkflowStatus.FAILED:
                workflow.result = self._aggregate_results(workflow.tasks)
                workflow.status = WorkflowStatus.COMPLETED
                workflow.end_time = datetime.now().isoformat()

                print(f"\n✅ 工作流执行完成!")
                print(f"   结果: {json.dumps(workflow.result, indent=2, ensure_ascii=False)}")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.now().isoformat()
            print(f"❌ 工作流执行失败: {e}")

        return workflow.to_dict()

    async def _execute_task(self, task: AgentTask):
        """执行单个任务"""
        try:
            # 模拟不同类型任务的执行
            if task.task_type == TaskType.CODE_GENERATION:
                task.output_data = {
                    "code": "def add(a, b):\n    return a + b\n\n# Generated by " + task.agent_id,
                    "language": "python",
                    "explanation": "简单的加法函数实现"
                }
                print(f"   生成代码: {task.output_data['code'][:50]}...")

            elif task.task_type == TaskType.CODE_REVIEW:
                task.output_data = {
                    "review": "代码质量良好，建议添加类型注释",
                    "issues": [],
                    "suggestions": ["添加类型注释", "添加文档字符串"]
                }
                print(f"   代码审查: {task.output_data['review']}")

            elif task.task_type == TaskType.TESTING:
                task.output_data = {
                    "test_cases": [
                        "assert add(1, 2) == 3",
                        "assert add(-1, 1) == 0",
                        "assert add(0, 0) == 0"
                    ],
                    "coverage": "100%",
                    "passed": 3
                }
                print(f"   测试用例: {task.output_data['passed']} 个通过")

            elif task.task_type == TaskType.DOCUMENTATION:
                task.output_data = {
                    "docstring": '"""计算两个数的和\n\nArgs:\n    a: 第一个数\n    b: 第二个数\n\nReturns:\n    两数之和\n"""',
                    "usage_example": ">>> result = add(5, 3)\n>>> print(result)\n8"
                }
                print(f"   文档生成完成")

            task.status = "completed"

            # 模拟处理时间
            await asyncio.sleep(0.5)

        except Exception as e:
            task.status = "failed"
            task.error = str(e)

    def _aggregate_results(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """聚合任务结果"""
        aggregated = {
            "summary": {
                "total_tasks": len(tasks),
                "completed": sum(1 for t in tasks if t.status == "completed"),
                "failed": sum(1 for t in tasks if t.status == "failed")
            },
            "artifacts": {}
        }

        for task in tasks:
            if task.output_data:
                aggregated["artifacts"][task.agent_id] = task.output_data

        # 合并不同类型的输出
        if "code" in str(aggregated["artifacts"]):
            aggregated["final_product"] = {
                "code": next((v["code"] for v in aggregated["artifacts"].values() if "code" in v), ""),
                "reviews": [v["review"] for v in aggregated["artifacts"].values() if "review" in v],
                "tests": [v["test_cases"] for v in aggregated["artifacts"].values() if "test_cases" in v],
                "documentation": [v["docstring"] for v in aggregated["artifacts"].values() if "docstring" in v]
            }

        return aggregated

# 预定义工作流模板
WORKFLOW_TEMPLATES = {
    "full_development": {
        "name": "完整开发流程",
        "description": "代码生成 → 审查 → 测试 → 文档",
        "tasks": [
            {"type": "code_generation", "description": "生成初始代码"},
            {"type": "code_review", "description": "代码审查"},
            {"type": "testing", "description": "编写测试"},
            {"type": "documentation", "description": "生成文档"}
        ]
    },
    "code_refactor": {
        "name": "代码重构",
        "description": "审查 → 重构 → 测试",
        "tasks": [
            {"type": "code_review", "description": "分析现有代码"},
            {"type": "refactoring", "description": "执行重构"},
            {"type": "testing", "description": "验证重构结果"}
        ]
    },
    "bug_fix": {
        "name": "Bug修复",
        "description": "调试 → 修复 → 测试",
        "tasks": [
            {"type": "debugging", "description": "定位问题"},
            {"type": "code_generation", "description": "生成修复代码"},
            {"type": "testing", "description": "验证修复"}
        ]
    }
}

async def demo_collaborative_development():
    """演示协作开发工作流"""

    print("╔══════════════════════════════════════════╗")
    print("║   智桥协作开发工作流演示                  ║")
    print("╚══════════════════════════════════════════╝\n")

    # 创建工作流引擎
    engine = WorkflowEngine()

    # 注册Agents
    print("🤖 注册Agents...")
    engine.register_agent_capabilities("crush-1", ["code_generation", "refactoring", "testing"])
    engine.register_agent_capabilities("claude-12", ["code_review", "documentation", "debugging"])
    engine.register_agent_capabilities("crush-5", ["testing", "code_generation"])
    print()

    # 创建完整开发流程工作流
    print("📋 创建工作流: 完整开发流程")
    workflow = engine.create_workflow("完整开发流程", "实现一个加法函数")

    # 添加任务
    print("\n➕ 添加任务...")

    # 1. 代码生成
    code_gen_agent = engine.find_best_agent("code_generation")
    task1 = AgentTask(
        agent_id=code_gen_agent,
        task_type=TaskType.CODE_GENERATION,
        input_data={"function": "add", "parameters": ["a", "b"]}
    )
    workflow.add_task(task1)
    print(f"   ✅ 任务1: {code_gen_agent} -> 代码生成")

    # 2. 代码审查
    review_agent = engine.find_best_agent("code_review")
    task2 = AgentTask(
        agent_id=review_agent,
        task_type=TaskType.CODE_REVIEW,
        input_data={"source_code": "待审查代码"}
    )
    workflow.add_task(task2)
    print(f"   ✅ 任务2: {review_agent} -> 代码审查")

    # 3. 测试
    test_agent = engine.find_best_agent("testing")
    task3 = AgentTask(
        agent_id=test_agent,
        task_type=TaskType.TESTING,
        input_data={"function_under_test": "add"}
    )
    workflow.add_task(task3)
    print(f"   ✅ 任务3: {test_agent} -> 测试")

    # 4. 文档
    doc_agent = engine.find_best_agent("documentation")
    task4 = AgentTask(
        agent_id=doc_agent,
        task_type=TaskType.DOCUMENTATION,
        input_data={"function": "add"}
    )
    workflow.add_task(task4)
    print(f"   ✅ 任务4: {doc_agent} -> 文档")

    # 执行工作流
    print("\n" + "="*60)
    result = await engine.execute_workflow(workflow)

    # 保存结果
    with open('/tmp/zhineng-bridge-workflow-result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 工作流结果已保存: /tmp/zhineng-bridge-workflow-result.json")

    return result

async def demo_parallel_processing():
    """演示并行处理"""

    print("\n\n╔══════════════════════════════════════════╗")
    print("║   智桥并行处理演示                        ║")
    print("╚══════════════════════════════════════════╝\n")

    # 创建工作流引擎
    engine = WorkflowEngine()

    # 注册多个Agents
    engine.register_agent_capabilities("crush-1", ["code_generation"])
    engine.register_agent_capabilities("crush-2", ["code_generation"])
    engine.register_agent_capabilities("crush-3", ["code_generation"])
    engine.register_agent_capabilities("claude-12", ["code_review"])
    engine.register_agent_capabilities("claude-13", ["code_review"])

    # 创建并行工作流
    workflow = engine.create_workflow("并行代码生成", "同时生成多个函数")

    # 添加多个代码生成任务（可以并行执行）
    tasks_data = [
        {"function": "add", "params": ["a", "b"]},
        {"function": "subtract", "params": ["a", "b"]},
        {"function": "multiply", "params": ["a", "b"]},
        {"function": "divide", "params": ["a", "b"]}
    ]

    code_agents = ["crush-1", "crush-2", "crush-3", "claude-12"]

    for i, task_data in enumerate(tasks_data):
        task = AgentTask(
            agent_id=code_agents[i % len(code_agents)],
            task_type=TaskType.CODE_GENERATION,
            input_data=task_data
        )
        workflow.add_task(task)
        print(f"   ✅ 任务{i+1}: {task.agent_id} -> 生成 {task_data['function']} 函数")

    # 执行工作流（可以优化为真正的并行执行）
    print("\n🚀 并行执行任务...")
    await engine.execute_workflow(workflow)

if __name__ == "__main__":
    import asyncio

    # 演示协作开发
    asyncio.run(demo_collaborative_development())

    # 演示并行处理
    asyncio.run(demo_parallel_processing())
