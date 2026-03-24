#!/usr/bin/env python3
"""
智桥（Zhineng-bridge）双仓库推送脚本

支持同时推送到 GitHub 和 Gitea。
"""

import subprocess
import sys
import argparse
from pathlib import Path


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class DualRepoPusher:
    """双仓库推送器"""

    def __init__(self):
        self.remotes = {
            'origin': 'https://github.com/guangda88/zhineng-bridge.git',
            'gitea': 'http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git'
        }

    def run_command(self, command: list) -> tuple:
        """
        运行命令

        Args:
            command: 命令列表

        Returns:
            (是否成功, 输出)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_git_repo(self) -> bool:
        """检查是否在 Git 仓库中"""
        success, output = self.run_command(['git', 'rev-parse', '--is-inside-work-tree'])
        return success

    def get_current_branch(self) -> str:
        """获取当前分支"""
        success, output = self.run_command(['git', 'symbolic-ref', '--short', 'HEAD'])
        if success:
            return output.strip()
        return None

    def check_remote(self, remote_name: str) -> bool:
        """
        检查远程仓库是否存在

        Args:
            remote_name: 远程仓库名称

        Returns:
            是否存在
        """
        success, output = self.run_command(['git', 'remote', '-v'])
        if success:
            return remote_name in output
        return False

    def add_remote(self, remote_name: str, url: str) -> bool:
        """
        添加远程仓库

        Args:
            remote_name: 远程仓库名称
            url: 仓库 URL

        Returns:
            是否成功
        """
        print(f"{Colors.BLUE}ℹ{Colors.END} 添加远程仓库: {remote_name}")

        success, output = self.run_command(['git', 'remote', 'add', remote_name, url])
        if success:
            print(f"{Colors.GREEN}✓{Colors.END} 远程仓库已添加: {remote_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.END} 添加远程仓库失败: {output}")
            return False

    def setup_remotes(self) -> bool:
        """设置远程仓库"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}配置远程仓库{Colors.END}\n")

        all_setup = True

        for name, url in self.remotes.items():
            if not self.check_remote(name):
                if not self.add_remote(name, url):
                    all_setup = False
            else:
                print(f"{Colors.GREEN}✓{Colors.END} 远程仓库已存在: {name}")

        return all_setup

    def push_to_remote(self, remote_name: str, branch: str = None, push_tags: bool = False) -> bool:
        """
        推送到远程仓库

        Args:
            remote_name: 远程仓库名称
            branch: 分支名称（默认: 当前分支）
            push_tags: 是否推送标签

        Returns:
            是否成功
        """
        if branch is None:
            branch = self.get_current_branch()
            if not branch:
                print(f"{Colors.RED}✗{Colors.END} 无法获取当前分支")
                return False

        print(f"{Colors.BLUE}ℹ{Colors.END} 推送到 {remote_name}: {branch}")

        # 推送分支
        command = ['git', 'push', remote_name, branch]
        success, output = self.run_command(command)

        if success:
            print(f"{Colors.GREEN}✓{Colors.END} 推送成功: {remote_name}/{branch}")
        else:
            print(f"{Colors.RED}✗{Colors.END} 推送失败: {remote_name}")
            print(output)
            return False

        # 推送标签
        if push_tags:
            print(f"{Colors.BLUE}ℹ{Colors.END} 推送标签到 {remote_name}")

            command = ['git', 'push', remote_name, '--tags']
            success, output = self.run_command(command)

            if success:
                print(f"{Colors.GREEN}✓{Colors.END} 标签推送成功: {remote_name}")
            else:
                print(f"{Colors.YELLOW}⚠{Colors.END} 标签推送失败: {remote_name}")
                print(output)

        return True

    def push_all(self, branch: str = None, push_tags: bool = False) -> bool:
        """
        推送到所有远程仓库

        Args:
            branch: 分支名称
            push_tags: 是否推送标签

        Returns:
            是否全部成功
        """
        print(f"\n{Colors.BOLD}{Colors.BLUE}推送到所有仓库{Colors.END}\n")

        all_success = True

        for remote_name in self.remotes.keys():
            if not self.push_to_remote(remote_name, branch, push_tags):
                all_success = False

        return all_success

    def sync_remotes(self) -> bool:
        """同步所有远程仓库"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}同步远程仓库{Colors.END}\n")

        all_success = True

        for remote_name in self.remotes.keys():
            print(f"{Colors.BLUE}ℹ{Colors.END} 从 {remote_name} 拉取更新...")
            success, output = self.run_command(['git', 'fetch', remote_name])
            if success:
                print(f"{Colors.GREEN}✓{Colors.END} {remote_name} 已同步")
            else:
                print(f"{Colors.RED}✗{Colors.END} {remote_name} 同步失败")
                print(output)
                all_success = False

        return all_success

    def show_status(self):
        """显示仓库状态"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}仓库状态{Colors.END}\n")

        # 远程仓库
        print("远程仓库:")
        success, output = self.run_command(['git', 'remote', '-v'])
        if success:
            print(output)

        # 当前分支
        branch = self.get_current_branch()
        if branch:
            print(f"\n当前分支: {branch}")

        # 未提交的更改
        print("\n未提交的更改:")
        success, output = self.run_command(['git', 'status', '--short'])
        if success and output.strip():
            print(output)
        else:
            print("  (无)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智桥双仓库推送工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/push-dual.py push
  python3 scripts/push-dual.py push --branch main --tags
  python3 scripts/push-dual.py setup
  python3 scripts/push-dual.py sync
  python3 scripts/push-dual.py status
        """
    )

    parser.add_argument(
        'command',
        choices=['push', 'setup', 'sync', 'status'],
        help='命令'
    )

    parser.add_argument(
        '--branch',
        type=str,
        default=None,
        help='分支名称（默认: 当前分支）'
    )

    parser.add_argument(
        '--tags',
        action='store_true',
        help='同时推送标签'
    )

    parser.add_argument(
        '--remote',
        type=str,
        default=None,
        choices=['origin', 'gitea'],
        help='仅推送到指定的远程仓库'
    )

    args = parser.parse_args()

    # 检查是否在 Git 仓库中
    pusher = DualRepoPusher()
    if not pusher.check_git_repo():
        print(f"{Colors.RED}✗{Colors.END} 错误: 当前目录不是 Git 仓库")
        sys.exit(1)

    # 执行命令
    try:
        if args.command == 'push':
            if args.remote:
                # 推送到指定仓库
                success = pusher.push_to_remote(args.remote, args.branch, args.tags)
            else:
                # 推送到所有仓库
                success = pusher.push_all(args.branch, args.tags)

            if success:
                print(f"\n{Colors.GREEN}✅{Colors.END} 推送完成")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}❌{Colors.END} 推送失败")
                sys.exit(1)

        elif args.command == 'setup':
            success = pusher.setup_remotes()
            if success:
                print(f"\n{Colors.GREEN}✅{Colors.END} 远程仓库配置完成")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}❌{Colors.END} 远程仓库配置失败")
                sys.exit(1)

        elif args.command == 'sync':
            success = pusher.sync_remotes()
            if success:
                print(f"\n{Colors.GREEN}✅{Colors.END} 同步完成")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}❌{Colors.END} 同步失败")
                sys.exit(1)

        elif args.command == 'status':
            pusher.show_status()
            sys.exit(0)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  用户中断{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌{Colors.END} 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
