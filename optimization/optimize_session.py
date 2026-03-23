#!/usr/bin/env python3
"""
zhineng-bridge 会话管理优化
使用 LingMinOpt 优化会话管理参数
"""

import sys
import json
from pathlib import Path

# 添加 LingMinOpt 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "LingMinOpt"))

from lingminopt import MinimalOptimizer, ExperimentConfig
from variable import create_session_search_space
from evaluator import evaluate_session_params


def main():
    """主函数"""
    print("🚀 开始优化 zhineng-bridge 会话管理参数...")
    print()
    
    # 加载配置
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # 创建搜索空间
    search_space = create_session_search_space()
    print(f"📋 搜索空间: {len(search_space.variables)} 个变量")
    for var in search_space.variables:
        print(f"   - {var.name}: {var.description}")
    print()
    
    # 创建实验配置
    exp_config = ExperimentConfig(
        max_experiments=config["max_experiments"],
        improvement_threshold=config["improvement_threshold"],
        time_budget=config["time_budget"],
        search_strategy=config["search_strategy"]
    )
    print(f"⚙️  实验配置:")
    print(f"   - 最大实验数: {exp_config.max_experiments}")
    print(f"   - 改进阈值: {exp_config.improvement_threshold}")
    print(f"   - 时间预算: {exp_config.time_budget} 秒")
    print(f"   - 搜索策略: {exp_config.search_strategy}")
    print()
    
    # 创建优化器
    optimizer = MinimalOptimizer(
        evaluate=evaluate_session_params,
        search_space=search_space,
        config=exp_config
    )
    
    # 运行优化
    print("🔬 开始优化实验...")
    result = optimizer.run()
    print()
    
    # 显示结果
    print("✅ 优化完成！")
    print()
    print("📊 优化结果:")
    print(f"   最佳分数: {result.best_score:.4f}")
    print(f"   最佳参数:")
    for key, value in result.best_params.items():
        print(f"     - {key}: {value}")
    print()
    print(f"   总实验数: {result.total_experiments}")
    print(f"   总时间: {result.total_time:.2f} 秒")
    print(f"   改进幅度: {result.improvement:.4f}")
    print()
    
    # 保存结果
    with open("optimization_results.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    
    print("💾 结果已保存到 optimization_results.json")


if __name__ == "__main__":
    main()
