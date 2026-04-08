#!/usr/bin/env python3
"""
检查代码类型注解和 docstring 覆盖率

扫描指定目录下的 Python 文件，分析：
1. 函数类型注解覆盖率
2. 类 docstring 覆盖率
3. 函数 docstring 覆盖率
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FileStats:
    """文件统计信息"""
    path: str
    classes: int = 0
    classes_with_docstring: int = 0
    functions: int = 0
    functions_with_docstring: int = 0
    functions_with_type_hints: int = 0
    functions_with_return_annotation: int = 0
    functions_with_param_annotations: int = 0
    lines: int = 0


@dataclass
class ModuleStats:
    """模块统计信息"""
    name: str
    files: List[FileStats] = field(default_factory=list)

    @property
    def total_classes(self) -> int:
        return sum(f.classes for f in self.files)

    @property
    def total_functions(self) -> int:
        return sum(f.functions for f in self.files)

    @property
    def docstring_coverage(self) -> float:
        """docstring 覆盖率"""
        total = sum(f.functions for f in self.files)
        with_doc = sum(f.functions_with_docstring for f in self.files)
        return (with_doc / total * 100) if total > 0 else 0

    @property
    def type_hints_coverage(self) -> float:
        """类型注解覆盖率"""
        total = sum(f.functions for f in self.files)
        with_hints = sum(f.functions_with_type_hints for f in self.files)
        return (with_hints / total * 100) if total > 0 else 0

    @property
    def return_annotation_coverage(self) -> float:
        """返回值注解覆盖率"""
        total = sum(f.functions for f in self.files)
        with_return = sum(f.functions_with_return_annotation for f in self.files)
        return (with_return / total * 100) if total > 0 else 0

    @property
    def param_annotation_coverage(self) -> float:
        """参数注解覆盖率"""
        total = sum(f.functions for f in self.files)
        with_params = sum(f.functions_with_param_annotations for f in self.files)
        return (with_params / total * 100) if total > 0 else 0


class CodeChecker(ast.NodeVisitor):
    """代码检查器"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.stats = FileStats(path=filepath)

    def check(self) -> FileStats:
        """检查文件"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            try:
                source = f.read()
                self.stats.lines = len(source.splitlines())
                tree = ast.parse(source, filename=self.filepath)
                self.visit(tree)
            except SyntaxError as e:
                print(f"Warning: Syntax error in {self.filepath}: {e}")
        return self.stats

    def visit_ClassDef(self, node: ast.ClassDef):
        """访问类定义"""
        self.stats.classes += 1
        # 检查类 docstring
        if (node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            self.stats.classes_with_docstring += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        self.stats.functions += 1

        # 检查函数 docstring
        if (node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            self.stats.functions_with_docstring += 1

        # 检查返回值注解
        if node.returns is not None:
            self.stats.functions_with_return_annotation += 1

        # 检查参数注解
        has_param_annotations = any(
            arg.annotation is not None
            for arg in node.args.args
            if arg.arg not in ('self', 'cls')
        )
        if has_param_annotations:
            self.stats.functions_with_param_annotations += 1

        # 检查是否完整类型注解（返回值 + 参数）
        if node.returns is not None and has_param_annotations:
            self.stats.functions_with_type_hints += 1

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """访问异步函数定义"""
        # 复用 FunctionDef 的逻辑
        self.visit_FunctionDef(node)


def scan_directory(directory: str) -> Dict[str, ModuleStats]:
    """扫描目录"""
    modules = defaultdict(lambda: ModuleStats(name=""))

    for root, dirs, files in os.walk(directory):
        # 跳过测试目录、__pycache__ 等
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', 'venv', 'env', 'dist', 'build')]

        for filename in files:
            if not filename.endswith('.py'):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, directory)

            # 跳过 __init__.py 和测试文件
            if filename == '__init__.py' or filename.startswith('test_') or filename.startswith('_test'):
                continue

            checker = CodeChecker(filepath)
            stats = checker.check()

            # 确定模块名称
            module_name = Path(rel_path).parts[0] if len(Path(rel_path).parts) > 1 else "root"
            if module_name not in modules:
                modules[module_name] = ModuleStats(name=module_name)
            modules[module_name].files.append(stats)

    return dict(modules)


def print_report(modules: Dict[str, ModuleStats]):
    """打印报告"""
    print("\n" + "=" * 80)
    print("代码类型注解和 Docstring 覆盖率报告")
    print("=" * 80)

    # 汇总统计
    total_classes = sum(m.total_classes for m in modules.values())
    total_functions = sum(m.total_functions for m in modules.values())
    total_with_docstring = sum(sum(f.functions_with_docstring for f in m.files) for m in modules.values())
    total_with_hints = sum(sum(f.functions_with_type_hints for f in m.files) for m in modules.values())
    total_with_return = sum(sum(f.functions_with_return_annotation for f in m.files) for m in modules.values())
    total_with_params = sum(sum(f.functions_with_param_annotations for f in m.files) for m in modules.values())

    print("\n【汇总统计】")
    print(f"  总类数:     {total_classes}")
    print(f"  总函数数:   {total_functions}")
    print(f"  总代码行数: {sum(sum(f.lines for f in m.files) for m in modules.values())}")

    print("\n【覆盖率】")
    docstring_cov = (total_with_docstring / total_functions * 100) if total_functions > 0 else 0
    hints_cov = (total_with_hints / total_functions * 100) if total_functions > 0 else 0
    return_cov = (total_with_return / total_functions * 100) if total_functions > 0 else 0
    param_cov = (total_with_params / total_functions * 100) if total_functions > 0 else 0

    print(f"  Docstring 覆盖率:    {docstring_cov:.1f}% ({total_with_docstring}/{total_functions})")
    print(f"  类型注解覆盖率:      {hints_cov:.1f}% ({total_with_hints}/{total_functions})")
    print(f"    - 返回值注解:      {return_cov:.1f}% ({total_with_return}/{total_functions})")
    print(f"    - 参数注解:        {param_cov:.1f}% ({total_with_params}/{total_functions})")

    # 按模块统计
    print("\n【模块详情】")
    print(f"{'模块':<20} {'函数':>6} {'Docstring':>12} {'类型注解':>12} {'返回值':>10} {'参数':>10}")
    print("-" * 80)

    for module_name, stats in sorted(modules.items()):
        total_funcs = stats.total_functions
        if total_funcs == 0:
            continue
        with_doc = sum(f.functions_with_docstring for f in stats.files)
        with_hints = sum(f.functions_with_type_hints for f in stats.files)
        with_return = sum(f.functions_with_return_annotation for f in stats.files)
        with_params = sum(f.functions_with_param_annotations for f in stats.files)

        print(f"{module_name:<20} {total_funcs:>6} {with_doc/total_funcs*100:>11.1f}% {with_hints/total_funcs*100:>11.1f}% {with_return/total_funcs*100:>9.1f}% {with_params/total_funcs*100:>9.1f}%")

    # 文件详情
    print("\n【文件详情】")
    all_files = []
    for stats in modules.values():
        all_files.extend(stats.files)

    # 按覆盖率排序
    all_files.sort(key=lambda f: f.functions_with_type_hints / f.functions if f.functions > 0 else 0)

    print(f"{'文件':<50} {'函数':>6} {'Docstring':>12} {'类型注解':>12}")
    print("-" * 80)

    for file_stats in all_files:
        if file_stats.functions == 0:
            continue
        rel_path = os.path.relpath(file_stats.path)
        if len(rel_path) > 50:
            rel_path = "..." + rel_path[-47:]

        doc_cov = file_stats.functions_with_docstring / file_stats.functions * 100
        type_cov = file_stats.functions_with_type_hints / file_stats.functions * 100

        print(f"{rel_path:<50} {file_stats.functions:>6} {doc_cov:>11.1f}% {type_cov:>11.1f}%")

    # 改进建议
    print("\n【改进建议】")
    if docstring_cov < 80:
        print("  ⚠ Docstring 覆盖率低于 80%，建议为所有公共 API 添加 docstring")
    if hints_cov < 70:
        print("  ⚠ 类型注解覆盖率低于 70%，建议为新代码添加类型注解")
    if return_cov < 80:
        print("  ⚠ 返回值注解覆盖率较低，建议为函数添加返回值类型")
    if param_cov < 70:
        print("  ⚠ 参数注解覆盖率较低，建议为函数参数添加类型注解")

    if docstring_cov >= 80 and hints_cov >= 70:
        print("  ✅ 代码质量良好，继续保持！")

    print("\n" + "=" * 80)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # 默认扫描 relay-server 目录
        script_dir = Path(__file__).parent.parent
        directory = str(script_dir / "relay-server")

    if not os.path.exists(directory):
        print(f"Error: 目录不存在: {directory}")
        sys.exit(1)

    print(f"扫描目录: {directory}")
    modules = scan_directory(directory)
    print_report(modules)


if __name__ == "__main__":
    main()
