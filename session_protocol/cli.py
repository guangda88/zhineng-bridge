#!/usr/bin/env python3
"""
session_cli — 灵族会话管理CLI

用法:
  python -m session_protocol.cli status          # 全族概览
  python -m session_protocol.cli members          # 成员列表
  python -m session_protocol.cli sessions [成员]  # 会话列表
  python -m session_protocol.cli snapshot <id>    # 查看快照
  python -m session_protocol.cli health [成员]    # 健康检查
  python -m session_protocol.cli save             # 保存智桥上下文
  python -m session_protocol.cli compress         # 压缩智桥上下文
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session_protocol import FamilySessionManager, ZhiBridgeAdapter


def cmd_status(mgr: FamilySessionManager):
    overview = mgr.get_family_overview()
    print(f"\n{'='*50}")
    print(f"  灵族会话管理 — 全族概览")
    print(f"{'='*50}")
    print(f"  成员数:     {overview['members']}")
    print(f"  会话总数:   {overview['sessions']}")
    print(f"  活跃会话:   {overview['active_sessions']}")
    print(f"  快照总数:   {overview['snapshots']}")
    print(f"{'='*50}\n")


def cmd_members(mgr: FamilySessionManager):
    members = mgr.list_members()
    print(f"\n{'='*70}")
    print(f"  {'成员ID':<18} {'名称':<10} {'模式':<8} {'状态':<8} {'最后心跳'}")
    print(f"{'-'*70}")
    for m in members:
        hb = m.get("last_heartbeat") or "—"
        print(f"  {m['member_id']:<18} {m['name']:<10} {m['run_mode']:<8} {m['status']:<8} {hb}")
    print(f"{'='*70}\n")


def cmd_sessions(mgr: FamilySessionManager, member_id: str = None):
    sessions = mgr.list_sessions(member_id)
    if not sessions:
        print("  (无会话)")
        return
    print(f"\n  {'会话ID':<38} {'成员':<16} {'状态':<10} {'工具':<10} {'创建时间'}")
    print(f"  {'-'*95}")
    for s in sessions:
        print(f"  {s['session_id']:<38} {s['member_id']:<16} {s['status']:<10} {s.get('tool_name',''):<10} {s['created_at'][:19]}")
    print()


def cmd_snapshot(mgr: FamilySessionManager, snapshot_id: str):
    snap = mgr.get_snapshot(snapshot_id)
    if not snap:
        print(f"  快照不存在: {snapshot_id}")
        return
    print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2))


def cmd_health(mgr: FamilySessionManager, adapter: ZhiBridgeAdapter, member_id: str = None):
    if member_id and member_id != "ZhiBridge":
        health = mgr.get_member_health(member_id)
        print(json.dumps(health, ensure_ascii=False, indent=2))
    else:
        health = adapter.health_check()
        print(json.dumps(health, ensure_ascii=False, indent=2))


def cmd_save(mgr: FamilySessionManager, adapter: ZhiBridgeAdapter):
    snapshot = mgr.delegate_save("ZhiBridge")
    if snapshot:
        print(f"  已保存快照: {snapshot.snapshot_id}")
    else:
        print("  保存失败")


def cmd_compress(mgr: FamilySessionManager, adapter: ZhiBridgeAdapter):
    snapshot = mgr.delegate_compress("ZhiBridge")
    if snapshot:
        print(f"  已压缩快照: {snapshot.snapshot_id}")
        print(f"  压缩后预算: {json.dumps(snapshot.budget.to_dict(), ensure_ascii=False)}")
    else:
        print("  压缩失败")


def main():
    parser = argparse.ArgumentParser(description="灵族会话管理CLI")
    parser.add_argument("command", choices=["status", "members", "sessions", "snapshot", "health", "save", "compress"])
    parser.add_argument("arg", nargs="?", default=None)
    args = parser.parse_args()

    mgr = FamilySessionManager()
    adapter = ZhiBridgeAdapter()
    mgr.register_protocol("ZhiBridge", adapter)

    if args.command == "status":
        cmd_status(mgr)
    elif args.command == "members":
        cmd_members(mgr)
    elif args.command == "sessions":
        cmd_sessions(mgr, args.arg)
    elif args.command == "snapshot":
        cmd_snapshot(mgr, args.arg)
    elif args.command == "health":
        cmd_health(mgr, adapter, args.arg)
    elif args.command == "save":
        cmd_save(mgr, adapter)
    elif args.command == "compress":
        cmd_compress(mgr, adapter)


if __name__ == "__main__":
    main()
