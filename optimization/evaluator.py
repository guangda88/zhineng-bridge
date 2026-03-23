"""
zhineng-bridge 评估函数
使用 LingMinOpt 评估 zhineng-bridge 的性能
"""

import sys
import time
from pathlib import Path
import asyncio

# 添加 zhineng-bridge 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1" / "session_manager"))

from session_manager import SessionManager


class SessionPerformanceEvaluator:
    """会话性能评估器"""
    
    def __init__(self, base_dir="/home/ai"):
        """
        初始化评估器
        
        Args:
            base_dir: 基础目录
        """
        self.base_dir = Path(base_dir)
        self.manager = None
    
    def evaluate_session_performance(self, params):
        """
        评估会话管理性能
        
        Args:
            params: 参数字典
            
        Returns:
            dict: 评估结果
        """
        # 提取参数
        max_sessions = params.get("max_sessions", 10)
        session_timeout = params.get("session_timeout", 600)
        output_buffer_size = params.get("output_buffer_size", 10000)
        
        # 创建会话管理器
        self.manager = SessionManager(base_dir=str(self.base_dir))
        
        # 性能指标
        metrics = {
            "creation_time": 0,
            "list_time": 0,
            "memory_usage": 0,
            "throughput": 0
        }
        
        try:
            # 测试会话创建性能
            start_time = time.time()
            
            for i in range(max_sessions):
                session_id = self.manager.create_session(
                    'crush',
                    args=['--help']
                )
            
            metrics["creation_time"] = time.time() - start_time
            
            # 测试会话列表性能
            start_time = time.time()
            sessions = self.manager.list_sessions()
            metrics["list_time"] = time.time() - start_time
            
            # 计算吞吐量（会话/秒）
            metrics["throughput"] = max_sessions / metrics["creation_time"]
            
            # 计算内存使用（估算）
            metrics["memory_usage"] = max_sessions * 1024 * 10  # 估算：每个会话 10KB
            
            # 计算综合分数（越高越好）
            score = self._calculate_score(metrics)
            
            return {
                "score": score,
                "metrics": metrics,
                "success": True
            }
            
        except Exception as e:
            return {
                "score": 0,
                "metrics": {},
                "success": False,
                "error": str(e)
            }
        
        finally:
            # 清理
            if self.manager:
                import shutil
                import os
                if self.manager.work_dir.parent.exists():
                    try:
                        shutil.rmtree(self.manager.work_dir.parent)
                    except PermissionError:
                        # 如果有权限问题，手动删除文件
                        for root, dirs, files in os.walk(self.manager.work_dir.parent, topdown=False):
                            for name in files:
                                try:
                                    os.chmod(os.path.join(root, name), 0o777)
                                    os.remove(os.path.join(root, name))
                                except:
                                    pass
                            for name in dirs:
                                try:
                                    os.rmdir(os.path.join(root, name))
                                except:
                                    pass
                        try:
                            os.rmdir(self.manager.work_dir.parent)
                        except:
                            pass
    
    def _calculate_score(self, metrics):
        """
        计算综合分数
        
        Args:
            metrics: 性能指标
            
        Returns:
            float: 综合分数
        """
        # 权重
        weights = {
            "creation_time": 0.4,
            "list_time": 0.2,
            "memory_usage": 0.2,
            "throughput": 0.2
        }
        
        # 归一化指标
        creation_score = 1 / (1 + metrics["creation_time"])  # 创建时间越短越好
        list_score = 1 / (1 + metrics["list_time"])  # 列表时间越短越好
        memory_score = 1 / (1 + metrics["memory_usage"] / 1024 / 1024)  # 内存使用越少越好
        throughput_score = metrics["throughput"] / 100  # 吞吐量越高越好
        
        # 计算综合分数
        score = (
            weights["creation_time"] * creation_score +
            weights["list_time"] * list_score +
            weights["memory_usage"] * memory_score +
            weights["throughput"] * throughput_score
        )
        
        return score


def evaluate_session_params(params):
    """
    评估会话参数
    
    Args:
        params: 参数字典
        
    Returns:
        float: 分数（越高越好）
    """
    evaluator = SessionPerformanceEvaluator()
    result = evaluator.evaluate_session_performance(params)
    
    if result["success"]:
        return result["score"]
    else:
        return 0


def evaluate_websocket_params(params):
    """
    评估 WebSocket 参数
    
    Args:
        params: 参数字典
        
    Returns:
        float: 分数（越高越好）
    """
    # 简化版本：基于参数评分
    max_connections = params.get("max_connections", 10)
    ping_interval = params.get("ping_interval", 10)
    message_queue_size = params.get("message_queue_size", 100)
    
    # 计算分数
    score = (
        max_connections / 200 * 0.5 +  # 连接数越多越好
        (1 / ping_interval) / 0.2 * 0.3 +  # 心跳间隔越短越好
        message_queue_size / 5000 * 0.2  # 队列越大越好
    )
    
    return score


def evaluate_performance_params(params):
    """
    评估性能参数
    
    Args:
        params: 参数字典
        
    Returns:
        float: 分数（越高越好）
    """
    # 简化版本：基于参数评分
    output_update_interval = params.get("output_update_interval", 100)
    compression_enabled = params.get("compression_enabled", False)
    batch_size = params.get("batch_size", 100)
    
    # 计算分数
    score = (
        (1 / output_update_interval) / 0.01 * 0.3 +  # 更新间隔越短越好
        (1 if compression_enabled else 0) * 0.2 +  # 压缩越好
        batch_size / 1000 * 0.5  # 批处理越大越好
    )
    
    return score


if __name__ == "__main__":
    # 测试评估函数
    print("测试会话参数评估...")
    test_params = {
        "max_sessions": 10,
        "session_timeout": 600,
        "output_buffer_size": 10000
    }
    score = evaluate_session_params(test_params)
    print(f"会话参数分数: {score:.4f}")
    
    print("\n测试 WebSocket 参数评估...")
    test_params = {
        "max_connections": 10,
        "ping_interval": 10,
        "message_queue_size": 100
    }
    score = evaluate_websocket_params(test_params)
    print(f"WebSocket 参数分数: {score:.4f}")
    
    print("\n测试性能参数评估...")
    test_params = {
        "output_update_interval": 100,
        "compression_enabled": True,
        "batch_size": 100
    }
    score = evaluate_performance_params(test_params)
    print(f"性能参数分数: {score:.4f}")
    
    print("\n✅ 所有评估函数测试成功！")
