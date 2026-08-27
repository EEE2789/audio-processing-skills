#!/usr/bin/env python3
"""
备份管理器 - 创建描述性备份文件
"""

import shutil
from datetime import datetime
from pathlib import Path


def create_backup(file_path, count, status, description=""):
    """
    创建描述性备份文件
    
    Args:
        file_path: 原文件路径
        count: 字幕条数
        status: 状态描述（如：正确、偏移24秒、缺失53条）
        description: 额外描述（可选）
    """
    
    file_path = Path(file_path)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_path.name}.bak.{count}条.{status}.{timestamp}"
    
    if description:
        backup_name += f".{description}"
    
    backup_name += file_path.suffix
    
    backup_path = file_path.parent / backup_name
    
    # 创建备份
    shutil.copy(file_path, backup_path)
    
    print(f"✅ 备份已创建: {backup_path.name}")
    
    return backup_path


def list_backups(file_path):
    """列出所有备份文件"""
    
    file_path = Path(file_path)
    parent_dir = file_path.parent
    
    # 查找所有备份文件
    backups = []
    for file in parent_dir.iterdir():
        if file.name.startswith(file_path.name + '.bak.'):
            backups.append(file)
    
    # 按修改时间排序
    backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    print(f"\n📁 备份文件列表 ({len(backups)} 个):")
    for backup in backups:
        # 解析备份文件名
        parts = backup.name.split('.')
        info = ' '.join(parts[len(file_path.name.split('.')):])
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"   {backup.name}")
        print(f"      信息: {info}")
        print(f"      修改: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python backup_manager.py <文件.srt> [条数] [状态] [描述]")
        print("示例: python backup_manager.py 简体0721.srt 125 正确")
        print("示例: python backup_manager.py 简体0721.srt 72 缺失53条 匹配失败")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if len(sys.argv) >= 4:
        count = int(sys.argv[2])
        status = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        create_backup(file_path, count, status, description)
    else:
        list_backups(file_path)
