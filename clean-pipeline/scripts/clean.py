#!/usr/bin/env python3
"""
视频管道清理工具

使用 find 命令清理 video_pipeline 目录中的所有文件。
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ====== 配置 ======
DEFAULT_CLEAN_DIRS = [
    "/Users/ai/Documents/video_pipeline/1input",
    "/Users/ai/Documents/video_pipeline/2output",
    "/Users/ai/Documents/video_pipeline/3daily",
]


def clean_with_find(directories, dry_run=False):
    """使用 find 命令清理指定目录中的文件

    Args:
        directories: 要清理的目录列表
        dry_run: 预览模式，不实际删除

    Returns:
        (删除的文件数, 释放的空间字节数)
    """
    total_files = 0
    total_size = 0

    for directory in directories:
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"⚠️  目录不存在，跳过: {directory}")
            continue

        if not dir_path.is_dir():
            print(f"⚠️  路径不是目录，跳过: {directory}")
            continue

        print(f"\n📁 清理目录: {directory}")

        # 使用 find 命令统计
        if dry_run:
            # 预览模式：只统计，不删除
            cmd = ["find", str(dir_path), "-type", "f", "-exec", "ls", "-lh", "{}", ";"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                files = [l for l in lines if l.strip()]
                for f in files:
                    print(f"  [预览] {f}")
                print(f"  ℹ️  共 {len(files)} 个文件")
                total_files += len(files)
            except Exception as e:
                print(f"  ✗ 统计失败: {e}")
        else:
            # 实际删除
            # 保留重要文件：封面轮换状态文件
            preserve_files = [".cover_rotation_state"]
            preserve条件 = " ".join([f'! -name "{f}"' for f in preserve_files])

            cmd = ["find", str(dir_path), "-type", "f"] + preserve条件.split() + ["-exec", "rm", "-f", "{}", ";"]
            try:
                # 先统计要删除的文件（排除保留文件）
                count_cmd = ["find", str(dir_path), "-type", "f"] + preserve条件.split()
                count_result = subprocess.run(count_cmd, capture_output=True, text=True)
                files = count_result.stdout.strip().split('\n') if count_result.stdout.strip() else []
                files = [f for f in files if f.strip()]
                file_count = len(files)

                # 执行删除
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(f"  ✓ 已删除 {file_count} 个文件")
                total_files += file_count
            except Exception as e:
                print(f"  ✗ 删除失败: {e}")

    return total_files, total_size


def send_notification(title, message):
    """发送 macOS 系统通知

    Args:
        title: 通知标题
        message: 通知内容
    """
    try:
        # 使用 osascript 发送通知
        script = f'display notification "{message}" with title "{title}" sound name "Glass"'
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception as e:
        # 如果通知失败，不影响清理结果
        pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description="视频管道清理工具")
    parser.add_argument(
        "--dirs",
        nargs="*",
        default=DEFAULT_CLEAN_DIRS,
        help="要清理的目录（默认：1input, 2output, 3daily）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不实际删除文件"
    )
    parser.add_argument(
        "--input-only",
        action="store_true",
        help="只清理 1input 目录"
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="不发送系统通知"
    )

    args = parser.parse_args()

    # 确定要清理的目录
    if args.input_only:
        dirs_to_clean = [DEFAULT_CLEAN_DIRS[0]]
    else:
        dirs_to_clean = args.dirs

    print("=" * 60)
    print("视频管道清理工具")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  预览模式 - 不会实际删除文件")

    print(f"\n📋 清理目录: {', '.join(dirs_to_clean)}")
    print(f"📋 清理方式: find -type f -exec rm -f {{}} +")

    # 执行清理
    print("\n" + "=" * 60)
    total_files, _ = clean_with_find(dirs_to_clean, args.dry_run)

    # 输出汇总
    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"📊 预览结果: 共 {total_files} 个文件")
    else:
        print(f"✅ 清理完成: 共删除 {total_files} 个文件")

        # 发送系统通知（仅在非预览模式且删除了文件时）
        if not args.no_notify and total_files > 0:
            time_str = datetime.now().strftime("%H:%M")
            send_notification(
                "视频管道清理完成",
                f"已删除 {total_files} 个文件 ({time_str})"
            )
    print("=" * 60)


if __name__ == "__main__":
    main()
