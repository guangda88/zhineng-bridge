#!/usr/bin/env python3
"""
智桥（Zhineng-bridge）参数优化脚本

使用 LingMinOpt 框架优化智桥的关键性能参数。
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加 LingMinOpt 路径
lingminopt_path = Path(__file__).parent.parent.parent / "LingMinOpt"
sys.path.insert(0, str(lingminopt_path))

from lingminopt.core.searcher import SearchSpace
from lingminopt.core.optimizer import MinimalOptimizer, ExperimentConfig

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from optimization.evaluator import evaluate_websocket_params, evaluate_performance_params
from optimization.variable import create_websocket_search_space, create_performance_search_space


def create_evaluator(params_type: str):
    """
    创建评估函数

    Args:
        params_type: 参数类型（websocket 或 performance）

    Returns:
        评估函数
    """
    def evaluator(params: Dict[str, Any]) -> float:
        # 根据类型选择评估函数
        if params_type == "websocket":
            return evaluate_websocket_params(params)
        elif params_type == "performance":
            return evaluate_performance_params(params)
        else:
            # 默认综合评估
            ws_score = evaluate_websocket_params(params)
            perf_score = evaluate_performance_params(params)
            return ws_score * 0.5 + perf_score * 0.5

    return evaluator


def optimize_websocket_params(iterations: int = 20) -> Dict[str, Any]:
    """
    优化 WebSocket 参数

    Args:
        iterations: 优化迭代次数

    Returns:
        优化结果
    """
    print("\n" + "=" * 70)
    print("优化 WebSocket 参数")
    print("=" * 70 + "\n")

    # 创建搜索空间
    search_space = create_websocket_search_space()
    print(f"✓ 搜索空间创建完成: {len(search_space.parameters)} 个变量\n")

    # 创建评估函数
    evaluator = create_evaluator("websocket")

    # 创建配置
    config = ExperimentConfig(
        max_experiments=iterations,
        direction="maximize",  # 最大化得分
        random_seed=42
    )

    # 创建优化器
    optimizer = MinimalOptimizer(evaluator, search_space, config)

    # 运行优化
    print(f"开始优化（{iterations} 次迭代）...\n")

    result = optimizer.run()
    elapsed_time = result.total_time

    print(f"\n✓ 优化完成，耗时: {elapsed_time:.2f} 秒")
    print(f"✓ 总评估次数: {result.total_experiments}")
    print(f"✓ 最佳得分: {result.best_score:.4f}\n")

    # 打印最佳参数
    print("最佳参数:")
    for key, value in result.best_params.items():
        print(f"  {key}: {value}")

    return {
        "type": "websocket",
        "best_params": result.best_params,
        "best_score": result.best_score,
        "iterations": iterations,
        "evaluation_count": result.total_experiments,
        "elapsed_time": elapsed_time,
        "improvement": result.improvement
    }


def optimize_performance_params(iterations: int = 20) -> Dict[str, Any]:
    """
    优化性能参数

    Args:
        iterations: 优化迭代次数

    Returns:
        优化结果
    """
    print("\n" + "=" * 70)
    print("优化性能参数")
    print("=" * 70 + "\n")

    # 创建搜索空间
    search_space = create_performance_search_space()
    print(f"✓ 搜索空间创建完成: {len(search_space.parameters)} 个变量\n")

    # 创建评估函数
    evaluator = create_evaluator("performance")

    # 创建配置
    config = ExperimentConfig(
        max_experiments=iterations,
        direction="maximize",  # 最大化得分
        random_seed=42
    )

    # 创建优化器
    optimizer = MinimalOptimizer(evaluator, search_space, config)

    # 运行优化
    print(f"开始优化（{iterations} 次迭代）...\n")

    result = optimizer.run()
    elapsed_time = result.total_time

    print(f"\n✓ 优化完成，耗时: {elapsed_time:.2f} 秒")
    print(f"✓ 总评估次数: {result.total_experiments}")
    print(f"✓ 最佳得分: {result.best_score:.4f}\n")

    # 打印最佳参数
    print("最佳参数:")
    for key, value in result.best_params.items():
        print(f"  {key}: {value}")

    return {
        "type": "performance",
        "best_params": result.best_params,
        "best_score": result.best_score,
        "iterations": iterations,
        "evaluation_count": result.total_experiments,
        "elapsed_time": elapsed_time,
        "improvement": result.improvement
    }


def optimize_all(iterations: int = 20) -> Dict[str, Any]:
    """
    优化所有参数

    Args:
        iterations: 每个参数组的优化迭代次数

    Returns:
        优化结果
    """
    print("\n" + "=" * 70)
    print("智桥参数优化")
    print("=" * 70)

    # 优化 WebSocket 参数
    ws_result = optimize_websocket_params(iterations)

    # 优化性能参数
    perf_result = optimize_performance_params(iterations)

    # 汇总结果
    total_score = (ws_result["best_score"] + perf_result["best_score"]) / 2
    total_time = ws_result["elapsed_time"] + perf_result["elapsed_time"]
    total_evaluations = ws_result["evaluation_count"] + perf_result["evaluation_count"]

    print("\n" + "=" * 70)
    print("优化总结")
    print("=" * 70 + "\n")

    print(f"WebSocket 得分: {ws_result['best_score']:.4f}")
    print(f"性能得分: {perf_result['best_score']:.4f}")
    print(f"综合得分: {total_score:.4f}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"总评估次数: {total_evaluations}\n")

    return {
        "websocket": ws_result,
        "performance": perf_result,
        "total_score": total_score,
        "total_time": total_time,
        "total_evaluations": total_evaluations
    }


def save_results(results: Dict[str, Any], output_file: str = None):
    """
    保存优化结果

    Args:
        results: 优化结果
        output_file: 输出文件路径
    """
    if output_file is None:
        output_file = project_root / "optimization_results.json"

    output_path = Path(output_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 优化结果已保存到: {output_path}")


def load_config_file(config_file: str) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典
    """
    config_path = Path(config_file)

    if not config_path.exists():
        print(f"警告: 配置文件不存在: {config_file}")
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="智桥参数优化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/optimize-params.py
  python3 scripts/optimize-params.py --iterations 50
  python3 scripts/optimize-params.py --only websocket
  python3 scripts/optimize-params.py --output results.json
        """
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="优化迭代次数（默认: 20）"
    )

    parser.add_argument(
        "--only",
        type=str,
        choices=["websocket", "performance"],
        help="只优化指定的参数组"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径（默认: optimization_results.json）"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息"
    )

    args = parser.parse_args()

    try:
        # 运行优化
        if args.only == "websocket":
            results = optimize_websocket_params(args.iterations)
        elif args.only == "performance":
            results = optimize_performance_params(args.iterations)
        else:
            results = optimize_all(args.iterations)

        # 保存结果
        save_results(results, args.output)

        print("\n✓ 优化完成！")

        # 返回成功状态
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
