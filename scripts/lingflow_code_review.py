#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LingFlow 风格代码审查 - zhineng-bridge 项目
替代 LingFlow code-review 技能的简化版本
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import subprocess
import json


class CodeReviewAuditor:
    """代码审查器 - 8维审查"""

    def __init__(self, target_dir: str = "."):
        self.target_dir = Path(target_dir)
        self.issues = defaultdict(list)
        self.metrics = {
            "files_reviewed": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
        }

    def audit(self) -> Dict[str, Any]:
        """执行完整审查"""
        print("🔍 开始 8 维代码审查...")

        # 查找所有Python文件
        python_files = list(self.target_dir.rglob("*.py"))
        self.metrics["files_reviewed"] = len(python_files)

        print(f"📂 找到 {len(python_files)} 个Python文件")

        for py_file in python_files:
            self._audit_file(py_file)

        # 生成报告
        report = self._generate_report()
        return report

    def _audit_file(self, file_path: Path):
        """审查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.metrics["total_lines"] += len(content.splitlines())

            # 解析AST
            tree = ast.parse(content)

            # 统计
            self.metrics["total_functions"] += len(
                [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            )
            self.metrics["total_classes"] += len(
                [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            )

            # 8维审查
            self._check_code_quality(file_path, content, tree)
            self._check_security(file_path, content, tree)
            self._check_best_practices(file_path, content, tree)
            self._check_naming_conventions(file_path, tree)

        except Exception as e:
            self.issues["parse_errors"].append({
                "file": str(file_path),
                "error": str(e)
            })

    def _check_file_length(self, file_path: Path, content: str):
        """检查文件长度"""
        lines = len(content.splitlines())
        if lines > 500:
            self.issues["code_quality"].append({
                "file": str(file_path),
                "type": "file_too_long",
                "severity": "medium",
                "message": f"文件过长 ({lines} 行)，建议拆分模块",
                "line": lines
            })

    def _check_function_complexity(self, file_path: Path, tree: ast.AST):
        """检查函数复杂度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.issues["code_quality"].append({
                        "file": str(file_path),
                        "type": "function_too_complex",
                        "severity": "medium" if complexity < 15 else "high",
                        "message": f"函数 {node.name} 复杂度过高 ({complexity})，建议重构",
                        "line": node.lineno,
                        "function": node.name,
                        "complexity": complexity
                    })

    def _check_import_order(self, file_path: Path, tree: ast.AST):
        """检查导入顺序"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(("import", node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                imports.append(("from", node.lineno, node.module or ""))

        # 检查导入是否分组
        if imports:
            groups = [imp[0] for imp in imports]
            if len(set(groups)) > 1:
                # 检查是否交替出现
                for i in range(len(groups) - 1):
                    if groups[i] != groups[i + 1] and groups[i] in ["import", "from"]:
                        self.issues["code_quality"].append({
                            "file": str(file_path),
                            "type": "import_order",
                            "severity": "low",
                            "message": f"导入语句顺序不规范 (line {imports[i][1]})",
                            "line": imports[i][1]
                        })
                        break

    def _check_code_quality(self, file_path: Path, content: str, tree: ast.AST):
        """1. 代码质量检查"""
        self._check_file_length(file_path, content)
        self._check_function_complexity(file_path, tree)
        self._check_import_order(file_path, tree)

    def _check_security(self, file_path: Path, content: str, tree: ast.AST):
        """2. 安全性检查"""

        # 检查硬编码的密码/密钥
        password_patterns = [
            r'password\s*=\s*["\']([^"\']+)["\']',
            r'api_key\s*=\s*["\']([^"\']+)["\']',
            r'secret\s*=\s*["\']([^"\']+)["\']',
            r'token\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in password_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                # 排除明显不是真实密钥的值
                if len(value) > 5 and not value.startswith(("${", "os.", "env.")):
                    line_num = content[:match.start()].count('\n') + 1
                    self.issues["security"].append({
                        "file": str(file_path),
                        "type": "hardcoded_secret",
                        "severity": "high",
                        "message": f"发现可能的硬编码密钥/密码",
                        "line": line_num
                    })

        # 检查 eval/exec (使用AST避免误报)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('eval', 'exec'):
                        self.issues["security"].append({
                            "file": str(file_path),
                            "type": "dangerous_function",
                            "severity": "high",
                            "message": f"使用 {node.func.id}() 存在安全风险",
                            "line": node.lineno
                        })

        # 检查 SQL 注入风险
        if re.search(r'execute\s*\(\s*["\'][^"\']*%s', content):
            self.issues["security"].append({
                "file": str(file_path),
                "type": "sql_injection_risk",
                "severity": "high",
                "message": "存在 SQL 注入风险，请使用参数化查询"
            })

    def _check_best_practices(self, file_path: Path, content: str, tree: ast.AST):
        """3. 最佳实践检查"""

        # 检查全局变量
        global_vars = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                global_vars.append(node.names)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # 检查是否在模块级别
                        if node.lineno <= 50:  # 假设导入在文件前50行
                            if target.id.isupper() and target.id not in ["__all__", "__version__"]:
                                global_vars.append([target.id])

        if global_vars and len(global_vars) > 5:
            self.issues["best_practices"].append({
                "file": str(file_path),
                "type": "too_many_globals",
                "severity": "medium",
                "message": f"过多的全局变量 ({len(global_vars)})"
            })

        # 检查 TODO/FIXME 注释
        todo_pattern = r'#\s*(TODO|FIXME|HACK|XXX)\s*'
        for match in re.finditer(todo_pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count('\n') + 1
            self.issues["best_practices"].append({
                "file": str(file_path),
                "type": "todo_comment",
                "severity": "low",
                "message": f"发现 {match.group(1).upper()} 注释",
                "line": line_num
            })

    def _check_naming_conventions(self, file_path: Path, tree: ast.AST):
        """4. 命名规范检查"""

        # 函数命名：snake_case
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    # 排除特殊函数
                    if not node.name.startswith('_'):
                        self.issues["naming"].append({
                            "file": str(file_path),
                            "type": "function_naming",
                            "severity": "low",
                            "message": f"函数名不符合 snake_case 规范: {node.name}",
                            "line": node.lineno
                        })

        # 类命名：PascalCase
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self.issues["naming"].append({
                        "file": str(file_path),
                        "type": "class_naming",
                        "severity": "medium",
                        "message": f"类名不符合 PascalCase 规范: {node.name}",
                        "line": node.lineno
                    })

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _generate_report(self) -> Dict[str, Any]:
        """生成审查报告"""
        total_issues = sum(len(issues) for issues in self.issues.values())
        severity_count = {
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for category, issues in self.issues.items():
            for issue in issues:
                severity = issue.get("severity", "low")
                severity_count[severity] += 1

        return {
            "summary": {
                "files_reviewed": self.metrics["files_reviewed"],
                "total_lines": self.metrics["total_lines"],
                "total_functions": self.metrics["total_functions"],
                "total_classes": self.metrics["total_classes"],
                "total_issues": total_issues,
                "severity_breakdown": severity_count
            },
            "issues_by_category": {
                category: issues
                for category, issues in self.issues.items()
                if issues
            },
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 代码质量
        code_quality_issues = self.issues.get("code_quality", [])
        if code_quality_issues:
            high_complexity = [i for i in code_quality_issues if i.get("severity") == "high"]
            if high_complexity:
                recommendations.append(
                    f"🔴 优先重构 {len(high_complexity)} 个高复杂度函数，"
                    "降低圈复杂度以提高可维护性"
                )

        # 安全性
        security_issues = self.issues.get("security", [])
        if security_issues:
            recommendations.append(
                f"🔴 立即修复 {len(security_issues)} 个安全问题，"
                "特别是硬编码密钥和 SQL 注入风险"
            )

        # 命名规范
        naming_issues = self.issues.get("naming", [])
        if naming_issues:
            recommendations.append(
                f"⚠️  统一命名规范，修复 {len(naming_issues)} 个命名问题"
            )

        # 最佳实践
        best_practice_issues = self.issues.get("best_practices", [])
        if best_practice_issues:
            todo_count = len([i for i in best_practice_issues if i["type"] == "todo_comment"])
            if todo_count > 0:
                recommendations.append(
                    f"💡 清理 {todo_count} 个 TODO/FIXME 注释"
                )

        return recommendations


def print_report(report: Dict[str, Any]):
    """打印格式化报告"""
    print("\n" + "=" * 80)
    print("📊 LingFlow 8维代码审查报告")
    print("=" * 80 + "\n")

    # 摘要
    summary = report["summary"]
    print("📋 审查摘要")
    print("-" * 40)
    print(f"  文件数: {summary['files_reviewed']}")
    print(f"  代码行数: {summary['total_lines']}")
    print(f"  函数数: {summary['total_functions']}")
    print(f"  类数: {summary['total_classes']}")
    print(f"  总问题数: {summary['total_issues']}")
    print(f"  严重问题: {summary['severity_breakdown']['high']}")
    print(f"  中等问题: {summary['severity_breakdown']['medium']}")
    print(f"  轻微问题: {summary['severity_breakdown']['low']}")
    print()

    # 分类问题
    issues_by_category = report["issues_by_category"]
    if issues_by_category:
        print("🔍 问题分类")
        print("-" * 40)

        category_names = {
            "code_quality": "代码质量",
            "security": "安全性",
            "best_practices": "最佳实践",
            "naming": "命名规范",
            "parse_errors": "解析错误"
        }

        for category, issues in sorted(issues_by_category.items()):
            name = category_names.get(category, category)
            count = len(issues)
            severity_breakdown = {}

            for issue in issues:
                severity = issue.get("severity", "low")
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1

            severity_str = ", ".join(
                f"{k}: {v}" for k, v in sorted(severity_breakdown.items())
            )
            print(f"  {name}: {count} ({severity_str})")

        print()

    # 高优先级问题详情
    high_priority_issues = []
    for category, issues in issues_by_category.items():
        for issue in issues:
            if issue.get("severity") == "high":
                high_priority_issues.append((category, issue))

    if high_priority_issues:
        print("🔴 高优先级问题")
        print("-" * 40)
        for i, (category, issue) in enumerate(high_priority_issues[:10], 1):
            print(f"  {i}. [{issue['file']}:{issue.get('line', '?')}]")
            print(f"     {issue['message']}")
        print()

    # 改进建议
    recommendations = report["recommendations"]
    if recommendations:
        print("💡 改进建议")
        print("-" * 40)
        for rec in recommendations:
            print(f"  • {rec}")
        print()

    print("=" * 80)
    print("审查完成")
    print("=" * 80)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LingFlow 代码审查工具")
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="审查目标目录（默认：当前目录）"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="输出格式（默认：text）"
    )
    parser.add_argument(
        "--output",
        help="输出到文件"
    )

    args = parser.parse_args()

    auditor = CodeReviewAuditor(args.target)
    report = auditor.audit()

    if args.format == "json":
        output = json.dumps(report, indent=2, ensure_ascii=False)
    else:
        output = report
        print_report(report)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            if args.format == "json":
                f.write(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                # 重新生成报告文本
                import io
                import contextlib
                f_capture = io.StringIO()
                with contextlib.redirect_stdout(f_capture):
                    print_report(report)
                f.write(f_capture.getvalue())
        print(f"\n✅ 报告已保存到: {args.output}")

    return 0 if report["summary"]["severity_breakdown"]["high"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
