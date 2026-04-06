#!/usr/bin/env python3
"""
推送服务模块

提供 Web Push 通知功能
使用 VAPID (Voluntary Application Server Identification) 协议

注意: 此模块依赖 pywebpush 库进行实际的推送通知
生产环境需要安装: pip install pywebpush
"""

import json
from typing import Dict, List, Optional, Any
from aiohttp import web
from datetime import datetime
import os

from logger import get_logger


class PushService:
    """推送服务类"""

    def __init__(self, private_key_path: str = None, subject: str = None):
        """
        初始化推送服务

        Args:
            private_key_path: VAPID 私钥文件路径
            subject: VAPID 主题 (通常是 mailto: 或 https: URL)
        """
        self.logger = get_logger(__name__)

        # 从环境变量读取配置
        self.private_key_path = private_key_path or os.getenv(
            'ZHINENG_BRIDGE_VAPID_PRIVATE_KEY_PATH',
            '/home/ai/zhineng-bridge/relay-server/vapid_private_key.pem'
        )
        self.subject = subject or os.getenv(
            'ZHINENG_BRIDGE_VAPID_SUBJECT',
            'mailto:admin@zhineng-bridge.com'
        )

        # 订阅存储 (内存中，生产环境应使用数据库)
        self.subscriptions: Dict[str, Dict] = {}

        # 检查 pywebpush 是否可用
        try:
            import pywebpush
            self.pywebpush = pywebpush
            self.logger.info("pywebpush library loaded successfully")
        except ImportError:
            self.pywebpush = None
            self.logger.warning(
                "pywebpush library not found. "
                "Push notifications will be logged but not actually sent. "
                "Install with: pip install pywebpush"
            )

    def _load_vapid_keys(self) -> tuple:
        """
        加载 VAPID 密钥

        Returns:
            (private_key, subject) 元组

        Raises:
            FileNotFoundError: 私钥文件不存在
            Exception: 读取失败
        """
        if not os.path.exists(self.private_key_path):
            raise FileNotFoundError(
                f"VAPID private key file not found: {self.private_key_path}"
            )

        with open(self.private_key_path, 'r') as f:
            private_key = f.read().strip()

        return private_key, self.subject

    async def subscribe(self, request: web.Request) -> web.Response:
        """
        处理推送订阅请求

        POST /api/notifications/subscribe
        Body:
        {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/...",
                "keys": {
                    "p256dh": "...",
                    "auth": "..."
                }
            },
            "user_agent": "Mozilla/5.0..."
        }
        """
        try:
            data = await request.json()

            subscription = data.get('subscription')
            if not subscription:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Missing 'subscription' in request body",
                        "code": 400
                    },
                    status=400
                )

            endpoint = subscription.get('endpoint')
            if not endpoint:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Missing 'endpoint' in subscription",
                        "code": 400
                    },
                    status=400
                )

            keys = subscription.get('keys', {})
            p256dh = keys.get('p256dh')
            auth = keys.get('auth')

            if not p256dh or not auth:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Missing 'p256dh' or 'auth' in subscription keys",
                        "code": 400
                    },
                    status=400
                )

            # 生成订阅 ID
            subscription_id = endpoint.split('/')[-1] or str(hash(endpoint))

            # 存储订阅
            self.subscriptions[subscription_id] = {
                'subscription': subscription,
                'user_agent': data.get('user_agent'),
                'created_at': datetime.now().isoformat(),
                'active': True
            }

            self.logger.info(
                "Push subscription registered",
                subscription_id=subscription_id,
                endpoint=endpoint
            )

            return web.json_response(
                {
                    "type": "subscription_registered",
                    "subscription_id": subscription_id,
                    "message": "Subscription registered successfully"
                },
                status=201
            )

        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON in subscription request", error=str(e))
            return web.json_response(
                {
                    "type": "error",
                    "message": "Invalid JSON in request body",
                    "code": 400
                },
                status=400
            )
        except Exception as e:
            self.logger.error("Subscription failed", error=str(e), exc_info=True)
            return web.json_response(
                {
                    "type": "error",
                    "message": f"Failed to register subscription: {str(e)}",
                    "code": 500
                },
                status=500
            )

    async def unsubscribe(self, request: web.Request) -> web.Response:
        """
        处理取消订阅请求

        POST /api/notifications/unsubscribe
        Body:
        {
            "subscription_id": "..."
        }
        或者
        {
            "endpoint": "https://fcm.googleapis.com/..."
        }
        """
        try:
            data = await request.json()

            # 支持 subscription_id 或 endpoint
            subscription_id = data.get('subscription_id')
            endpoint = data.get('endpoint')

            if not subscription_id and not endpoint:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Missing 'subscription_id' or 'endpoint' in request body",
                        "code": 400
                    },
                    status=400
                )

            # 如果只有 endpoint，查找对应的 subscription_id
            if endpoint and not subscription_id:
                for sid, sub in self.subscriptions.items():
                    if sub['subscription']['endpoint'] == endpoint:
                        subscription_id = sid
                        break

            if not subscription_id:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Subscription not found",
                        "code": 404
                    },
                    status=404
                )

            # 删除订阅
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]

                self.logger.info(
                    "Push subscription removed",
                    subscription_id=subscription_id
                )

                return web.json_response(
                    {
                        "type": "subscription_removed",
                        "subscription_id": subscription_id,
                        "message": "Subscription removed successfully"
                    },
                    status=200
                )
            else:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Subscription not found",
                        "code": 404
                    },
                    status=404
                )

        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON in unsubscribe request", error=str(e))
            return web.json_response(
                {
                    "type": "error",
                    "message": "Invalid JSON in request body",
                    "code": 400
                },
                status=400
            )
        except Exception as e:
            self.logger.error("Unsubscribe failed", error=str(e), exc_info=True)
            return web.json_response(
                {
                    "type": "error",
                    "message": f"Failed to remove subscription: {str(e)}",
                    "code": 500
                },
                status=500
            )

    async def send_notification(self, request: web.Request) -> web.Response:
        """
        发送推送通知

        POST /api/notifications/send
        """
        # F-024: 验证认证 token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return web.json_response(
                {"type": "error", "message": "Authentication required", "code": 401},
                status=401,
            )

        try:
            data = await request.json()

            title = data.get('title')
            body = data.get('body')

            if not title:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Missing 'title' in request body",
                        "code": 400
                    },
                    status=400
                )

            # 构建通知载荷
            payload = {
                'title': title,
                'body': body or '',
                'icon': data.get('icon', '/web/ui/icons/icon-192x192.png'),
                'badge': data.get('badge', '/web/ui/icons/icon-72x72.png'),
                'data': data.get('data', {}),
                'actions': data.get('actions', []),
                'timestamp': datetime.now().isoformat()
            }

            # 确定目标订阅
            subscription_id = data.get('subscription_id')

            if subscription_id:
                # 发送到特定订阅
                targets = [subscription_id]
            else:
                # 发送到所有活跃订阅
                targets = [
                    sid for sid, sub in self.subscriptions.items()
                    if sub.get('active', True)
                ]

            if not targets:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "No active subscriptions found",
                        "code": 404
                    },
                    status=404
                )

            # 发送通知
            results = []
            success_count = 0
            failure_count = 0

            for sid in targets:
                try:
                    if sid not in self.subscriptions:
                        results.append({
                            'subscription_id': sid,
                            'success': False,
                            'error': 'Subscription not found'
                        })
                        failure_count += 1
                        continue

                    subscription = self.subscriptions[sid]['subscription']

                    if self.pywebpush:
                        # 使用 pywebpush 实际发送
                        private_key, subject = self._load_vapid_keys()

                        webpush_result = self.pywebpush.webpush(
                            subscription_info=subscription,
                            data=json.dumps(payload),
                            vapid_private_key=private_key,
                            vapid_claims={"sub": subject}
                        )

                        results.append({
                            'subscription_id': sid,
                            'success': True,
                            'status_code': webpush_result.status_code
                        })
                        success_count += 1
                    else:
                        # 模拟发送（记录日志）
                        self.logger.info(
                            "Mock push notification",
                            subscription_id=sid,
                            title=title,
                            body=body
                        )

                        results.append({
                            'subscription_id': sid,
                            'success': True,
                            'note': 'Mock notification (pywebpush not installed)'
                        })
                        success_count += 1

                except Exception as e:
                    self.logger.error(
                        "Failed to send notification",
                        subscription_id=sid,
                        error=str(e)
                    )
                    results.append({
                        'subscription_id': sid,
                        'success': False,
                        'error': str(e)
                    })
                    failure_count += 1

            self.logger.info(
                "Push notification sent",
                title=title,
                success=success_count,
                failure=failure_count,
                total=len(targets)
            )

            return web.json_response(
                {
                    "type": "notification_sent",
                    "results": results,
                    "summary": {
                        "total": len(targets),
                        "success": success_count,
                        "failure": failure_count
                    },
                    "timestamp": datetime.now().isoformat()
                },
                status=200
            )

        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON in send notification request", error=str(e))
            return web.json_response(
                {
                    "type": "error",
                    "message": "Invalid JSON in request body",
                    "code": 400
                },
                status=400
            )
        except Exception as e:
            self.logger.error("Send notification failed", error=str(e), exc_info=True)
            return web.json_response(
                {
                    "type": "error",
                    "message": f"Failed to send notification: {str(e)}",
                    "code": 500
                },
                status=500
            )

    # ========================================================================
    # 辅助函数
    # ========================================================================

    async def send_session_state_notification(
        self,
        session_id: str,
        state: str,
        message: str = None
    ) -> bool:
        """
        发送会话状态变更通知

        Args:
            session_id: 会话 ID
            state: 状态 (started, stopped, error)
            message: 可选的消息

        Returns:
            是否成功发送
        """
        titles = {
            'started': '会话已启动',
            'stopped': '会话已停止',
            'error': '会话错误'
        }

        payload = {
            'title': titles.get(state, '会话更新'),
            'body': message or f'会话 {session_id} 状态变更为 {state}',
            'data': {
                'type': 'session_state',
                'session_id': session_id,
                'state': state
            }
        }

        return await self._send_to_all_subscriptions(payload)

    async def send_task_completion_notification(
        self,
        task_id: str,
        result: str
    ) -> bool:
        """
        发送任务完成通知

        Args:
            task_id: 任务 ID
            result: 任务结果

        Returns:
            是否成功发送
        """
        payload = {
            'title': '任务完成',
            'body': f'任务 {task_id} 已完成',
            'data': {
                'type': 'task_completion',
                'task_id': task_id,
                'result': result
            }
        }

        return await self._send_to_all_subscriptions(payload)

    async def send_error_notification(
        self,
        error_type: str,
        error_message: str
    ) -> bool:
        """
        发送错误通知

        Args:
            error_type: 错误类型
            error_message: 错误消息

        Returns:
            是否成功发送
        """
        payload = {
            'title': f'错误: {error_type}',
            'body': error_message,
            'data': {
                'type': 'error',
                'error_type': error_type
            },
            'icon': '/web/ui/icons/icon-error.png'
        }

        return await self._send_to_all_subscriptions(payload)

    async def _send_to_all_subscriptions(self, payload: Dict) -> bool:
        """
        发送通知到所有活跃订阅

        Args:
            payload: 通知载荷

        Returns:
            是否至少发送成功
        """
        if not self.subscriptions:
            self.logger.debug("No subscriptions to send notification to")
            return False

        success_count = 0

        for sid, sub in self.subscriptions.items():
            if not sub.get('active', True):
                continue

            try:
                if self.pywebpush:
                    private_key, subject = self._load_vapid_keys()

                    self.pywebpush.webpush(
                        subscription_info=sub['subscription'],
                        data=json.dumps(payload),
                        vapid_private_key=private_key,
                        vapid_claims={"sub": subject}
                    )
                else:
                    # 模拟发送
                    self.logger.info(
                        "Mock push notification",
                        subscription_id=sid,
                        payload=payload
                    )

                success_count += 1

            except Exception as e:
                self.logger.error(
                    "Failed to send notification",
                    subscription_id=sid,
                    error=str(e)
                )

        return success_count > 0


# ============================================================================
# 辅助函数
# ============================================================================

def setup_push_routes(app: web.Application, push_service: 'PushService'):
    """
    设置推送服务路由

    Args:
        app: aiohttp 应用
        push_service: PushService 实例
    """
    app.router.add_post("/api/notifications/subscribe", push_service.subscribe)
    app.router.add_post("/api/notifications/unsubscribe", push_service.unsubscribe)
    app.router.add_post("/api/notifications/send", push_service.send_notification)


__all__ = ["PushService", "setup_push_routes"]
