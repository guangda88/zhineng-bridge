#!/usr/bin/env python3
"""
智桥（Zhineng-bridge）发布验证脚本

自动验证发布前的各项检查，确保发布质量。
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ReleaseVerifier:
    """发布验证器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.results: List[Tuple[str, bool, str]] = []
        self.warnings: List[str] = []

    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")

    def print_success(self, message: str):
        """打印成功消息"""
        print(f"{Colors.GREEN}✓{Colors.END} {message}")

    def print_error(self, message: str):
        """打印错误消息"""
        print(f"{Colors.RED}✗{Colors.END} {message}")

    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

    def print_info(self, message: str):
        """打印信息"""
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

    def run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """
        运行命令并返回结果

        Args:
            command: 命令列表
            cwd: 工作目录

        Returns:
            (是否成功, 输出)
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_file_exists(self, filepath: str) -> bool:
        """检查文件是否存在"""
        path = self.project_root / filepath
        return path.exists() and path.is_file()

    def check_version_consistency(self) -> bool:
        """检查版本号一致性"""
        self.print_info("检查版本号一致性...")

        version = None

        # 检查 VERSION 文件
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            with open(version_file) as f:
                version = f.read().strip()
                self.print_success(f"VERSION 文件: {version}")
        else:
            self.print_error("VERSION 文件不存在")
            return False

        # 检查 README.md
        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            content = readme_file.read_text()
            match = re.search(r'Version[:\s]+([0-9]+\.[0-9]+\.[0-9]+)', content, re.IGNORECASE)
            if match:
                readme_version = match.group(1)
                if readme_version == version:
                    self.print_success(f"README.md 版本号: {readme_version}")
                else:
                    self.print_error(f"README.md 版本号不一致: {readme_version} != {version}")
                    return False
            else:
                self.print_warning("README.md 中未找到版本号")

        return True

    def check_documentation(self) -> bool:
        """检查文档完整性"""
        self.print_info("检查文档完整性...")

        required_docs = [
            "README.md",
            "CHANGELOG.md",
            "QUICKSTART.md",
            "USAGE_GUIDE.md",
            "TROUBLESHOOTING.md",
            "RELEASE_CHECKLIST.md"
        ]

        all_exist = True
        for doc in required_docs:
            if self.check_file_exists(doc):
                self.print_success(f"{doc} 存在")
            else:
                self.print_error(f"{doc} 不存在")
                all_exist = False

        return all_exist

    def check_tests(self) -> bool:
        """检查测试"""
        self.print_info("运行测试套件...")

        # 运行单元测试
        success, output = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/unit/", "-v", "--tb=short"
        ])

        if success:
            self.print_success("单元测试通过")
        else:
            self.print_error("单元测试失败")
            print(output)
            return False

        # 运行集成测试
        success, output = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/integration/", "-v", "--tb=short"
        ])

        if success:
            self.print_success("集成测试通过")
        else:
            self.print_error("集成测试失败")
            print(output)
            return False

        # 运行 E2E 测试
        success, output = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/e2e/", "-v", "--tb=short"
        ])

        if success:
            self.print_success("E2E 测试通过")
        else:
            self.print_error("E2E 测试失败")
            print(output)
            return False

        return True

    def check_test_coverage(self) -> bool:
        """检查测试覆盖率"""
        self.print_info("检查测试覆盖率...")

        success, output = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/", "--cov=.", "--cov-report=term-missing",
            "--cov-report=json", "--no-header"
        ])

        if not success:
            self.print_error("覆盖率检查失败")
            return False

        # 解析覆盖率报告
        try:
            with open(self.project_root / "coverage.json") as f:
                coverage_data = json.load(f)
                total_coverage = coverage_data['totals']['percent_covered']

                if total_coverage >= 70:
                    self.print_success(f"测试覆盖率: {total_coverage:.1f}% (目标: >=70%)")
                    return True
                else:
                    self.print_error(f"测试覆盖率不足: {total_coverage:.1f}% (目标: >=70%)")
                    return False
        except Exception as e:
            self.print_error(f"解析覆盖率报告失败: {e}")
            return False

    def check_examples(self) -> bool:
        """检查示例文件"""
        self.print_info("检查示例文件...")

        examples_dir = self.project_root / "examples"
        if not examples_dir.exists():
            self.print_error("examples 目录不存在")
            return False

        required_examples = [
            "examples/basic_usage.py",
            "examples/cursor_config.md",
            "examples/claude_config.md",
            "examples/README.md"
        ]

        all_exist = True
        for example in required_examples:
            if self.check_file_exists(example):
                self.print_success(f"{example} 存在")
            else:
                self.print_error(f"{example} 不存在")
                all_exist = False

        return all_exist

    def check_git_status(self) -> bool:
        """检查 Git 状态"""
        self.print_info("检查 Git 状态...")

        # 检查是否有未提交的更改
        success, output = self.run_command(["git", "status", "--porcelain"])

        if not success:
            self.print_error("Git 状态检查失败")
            return False

        if output.strip():
            self.print_warning("存在未提交的更改:")
            print(output)
            self.warnings.append("存在未提交的更改")
        else:
            self.print_success("工作区干净")

        return True

    def check_build(self) -> bool:
        """检查构建"""
        self.print_info("检查构建...")

        # 检查是否安装了 build
        success, _ = self.run_command([sys.executable, "-m", "build", "--version"])
        if not success:
            self.print_warning("build 未安装，跳过构建检查")
            self.warnings.append("build 未安装，请使用: pip install build")
            return True

        # 尝试构建
        success, output = self.run_command([sys.executable, "-m", "build"])

        if success:
            self.print_success("构建成功")

            # 检查生成的文件
            dist_dir = self.project_root / "dist"
            if dist_dir.exists():
                wheels = list(dist_dir.glob("*.whl"))
                sources = list(dist_dir.glob("*.tar.gz"))

                if wheels:
                    self.print_success(f"Wheel 包: {wheels[0].name}")
                if sources:
                    self.print_success(f"源码包: {sources[0].name}")

            return True
        else:
            self.print_error("构建失败")
            print(output)
            return False

    def check_changelog(self) -> bool:
        """检查 CHANGELOG"""
        self.print_info("检查 CHANGELOG...")

        changelog_file = self.project_root / "CHANGELOG.md"
        if not changelog_file.exists():
            self.print_error("CHANGELOG.md 不存在")
            return False

        content = changelog_file.read_text()

        # 检查是否有未发布的版本
        if "## [Unreleased]" in content:
            self.print_warning("CHANGELOG 中存在 [Unreleased] 章节")
            return True

        # 检查是否有最近版本
        match = re.search(r"## \[([0-9]+\.[0-9]+\.[0-9]+)\]", content)
        if match:
            version = match.group(1)
            self.print_success(f"最新版本: {version}")
        else:
            self.print_warning("CHANGELOG 中未找到版本号")

        return True

    def check_dependencies(self) -> bool:
        """检查依赖"""
        self.print_info("检查依赖...")

        # 检查是否有 requirements.txt
        if not self.check_file_exists("requirements.txt"):
            self.print_warning("requirements.txt 不存在")

        # 检查 PyPI 依赖
        success, output = self.run_command([sys.executable, "-m", "pip", "check"])
        if success:
            self.print_success("依赖检查通过")
        else:
            self.print_error("依赖检查失败")
            print(output)
            return False

        return True

    def check_server_files(self) -> bool:
        """检查服务器文件"""
        self.print_info("检查服务器文件...")

        required_files = [
            "relay-server/server.py",
            "relay-server/start_server.py",
            "phase1/session_manager/session_manager.py",
            "phase1/session_manager/start_manager.py",
        ]

        all_exist = True
        for filepath in required_files:
            if self.check_file_exists(filepath):
                self.print_success(f"{filepath} 存在")
            else:
                self.print_error(f"{filepath} 不存在")
                all_exist = False

        return all_exist

    def check_web_ui(self) -> bool:
        """检查 Web UI"""
        self.print_info("检查 Web UI...")

        ui_files = [
            "web/ui/index.html",
            "web/ui/js/app.js",
            "web/ui/js/client.js",
            "web/ui/css/base.css",
        ]

        all_exist = True
        for filepath in ui_files:
            if self.check_file_exists(filepath):
                self.print_success(f"{filepath} 存在")
            else:
                self.print_error(f"{filepath} 不存在")
                all_exist = False

        return all_exist

    def verify_all(self) -> bool:
        """运行所有验证"""
        self.print_header("智桥发布验证")

        all_passed = True

        # 代码质量检查
        self.print_header("代码质量")
        all_passed &= self.check_server_files()
        all_passed &= self.check_web_ui()
        all_passed &= self.check_dependencies()

        # 测试检查
        self.print_header("测试")
        all_passed &= self.check_tests()
        all_passed &= self.check_test_coverage()

        # 文档检查
        self.print_header("文档")
        all_passed &= self.check_documentation()
        all_passed &= self.check_examples()
        all_passed &= self.check_changelog()

        # 版本管理
        self.print_header("版本管理")
        all_passed &= self.check_version_consistency()

        # Git 状态
        self.print_header("Git 状态")
        self.check_git_status()

        # 构建检查
        self.print_header("构建")
        all_passed &= self.check_build()

        # 总结
        self.print_header("验证总结")

        if all_passed:
            self.print_success("所有关键检查通过！")
            print(f"\n{Colors.BOLD}{Colors.GREEN}✓ 准备发布{Colors.END}\n")
        else:
            self.print_error("部分检查失败，请修复后重试")
            print(f"\n{Colors.BOLD}{Colors.RED}✗ 不准备发布{Colors.END}\n")

        if self.warnings:
            print(f"{Colors.YELLOW}警告:{Colors.END}")
            for warning in self.warnings:
                print(f"  • {warning}")

        return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智桥发布验证脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/verify-publish.py
  python3 scripts/verify-publish.py --project-path /path/to/project
        """
    )

    parser.add_argument(
        "--project-path",
        type=str,
        default=".",
        help="项目根目录路径（默认: 当前目录）"
    )

    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳过测试检查"
    )

    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过构建检查"
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = os.path.abspath(args.project_path)

    if not os.path.exists(project_root):
        print(f"错误: 项目目录不存在: {project_root}")
        sys.exit(1)

    # 创建验证器
    verifier = ReleaseVerifier(project_root)

    # 运行验证
    success = verifier.verify_all()

    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}用户中断{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}错误: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
