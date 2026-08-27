#!/usr/bin/env python3
"""
安装定时清理任务

使用 macOS launchd 配置每天早上 6 点（北京时间）自动清理视频管道目录。

注意：macOS 使用本地时区，如果需要北京时间早上 6 点，需要根据系统时区调整。
"""

import os
import subprocess
import plistlib
from pathlib import Path


# ====== 配置 ======
SCRIPT_PATH = "/Users/ai/.claude/skills/clean-pipeline/scripts/clean.py"
PLIST_NAME = "com.videopipeline.clean.plist"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_PATH = LAUNCH_AGENTS_DIR / PLIST_NAME


# 北京时间早上 6 点对应的 macOS 本地时间（假设系统时区为 UTC+8）
# 如果系统时区不同，需要调整小时数
HOUR = 6
MINUTE = 0


def create_plist(hour=6, minute=0):
    """创建 launchd plist 文件

    Args:
        hour: 执行小时（默认 6）
        minute: 执行分钟（默认 0）
    """
    plist = {
        "Label": "com.videopipeline.clean",
        "ProgramArguments": [
            "/usr/bin/python3",
            SCRIPT_PATH
        ],
        "StartCalendarInterval": {
            "Hour": hour,
            "Minute": minute
        },
        "StandardOutPath": str(Path.home() / "Library" / "Logs" / "videopipeline_clean.log"),
        "StandardErrorPath": str(Path.home() / "Library" / "Logs" / "videopipeline_clean_err.log"),
        "RunAtLoad": False,  # 不在加载时立即运行
    }

    # 确保 LaunchAgents 目录存在
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # 写入 plist 文件
    with open(PLIST_PATH, "wb") as f:
        plistlib.dump(plist, f)

    print(f"✅ plist 文件已创建: {PLIST_PATH}")
    return PLIST_PATH


def load_plist():
    """加载 launchd 任务"""
    try:
        result = subprocess.run(
            ["launchctl", "load", str(PLIST_PATH)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ 定时任务已加载")
            print(f"⏰ 将在每天 {HOUR:02d}:{MINUTE:02d} 自动清理视频管道目录")
            return True
        else:
            print(f"❌ 加载失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False


def unload_plist():
    """卸载 launchd 任务"""
    try:
        result = subprocess.run(
            ["launchctl", "unload", str(PLIST_PATH)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ 定时任务已卸载")
            return True
        else:
            print(f"❌ 卸载失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 卸载失败: {e}")
        return False


def list_jobs():
    """列出所有 videopipeline 相关任务"""
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'videopipeline' in line.lower() or 'com.videopipeline' in line:
                    print(f"  {line}")
    except Exception as e:
        print(f"❌ 列出任务失败: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="安装/卸载定时清理任务")
    parser.add_argument(
        "--install",
        action="store_true",
        help="安装定时任务（每天早上 6 点执行）"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="卸载定时任务"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出相关定时任务"
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=6,
        help="执行小时（默认：6）"
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="执行分钟（默认：0）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("视频管道定时清理任务配置")
    print("=" * 60)

    if args.list:
        print("\n📋 相关定时任务:")
        list_jobs()
    elif args.uninstall:
        print(f"\n🗑️  卸载定时任务...")
        unload_plist()
        # 删除 plist 文件
        if PLIST_PATH.exists():
            PLIST_PATH.unlink()
            print(f"✅ 已删除 plist 文件: {PLIST_PATH}")
    elif args.install:
        print(f"\n📦 安装定时任务...")
        print(f"⏰ 执行时间: 每天 {args.hour:02d}:{args.minute:02d}")
        print(f"📂 清理脚本: {SCRIPT_PATH}")
        print()
        create_plist(args.hour, args.minute)
        load_plist()
        print("\n💡 提示:")
        print("  - 使用 'launchctl list' 查看所有任务")
        print("  - 使用 '--uninstall' 卸载定时任务")
        print("  - 查看日志: ~/Library/Logs/videopipeline_clean.log")
    else:
        print("\n使用方法:")
        print("  --install    安装定时任务")
        print("  --uninstall  卸载定时任务")
        print("  --list       列出相关任务")
        print("  --hour N     设置执行小时（默认 6）")
        print("  --minute N   设置执行分钟（默认 0）")

    print("=" * 60)


if __name__ == "__main__":
    main()
