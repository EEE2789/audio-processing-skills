---
name: clean-pipeline
description: 清理视频管道目录中的所有文件。使用 find 命令清理 1input、2output、3daily 目录。清理完成后自动发送系统通知。
---

# 视频管道清理工具

## 目标

使用 `find` 命令清理 video_pipeline 目录中的所有文件，清理完成后自动发送系统通知。

## 使用方法

### 基本用法（清理所有目录）

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py
```

执行命令：`find /Users/ai/Documents/video_pipeline/{1input,2output,3daily} -type f -exec rm -f {} +`

### 只清理 1input 目录

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py --input-only
```

### 预览模式（不实际删除）

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py --dry-run
```

### 清理指定目录

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py --dirs /path/to/dir1 /path/to/dir2
```

### 禁用通知

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py --no-notify
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--dirs` | 要清理的目录列表 | 1input, 2output, 3daily |
| `--dry-run` | 预览模式，不实际删除 | - |
| `--input-only` | 只清理 1input 目录 | - |
| `--no-notify` | 不发送系统通知 | - |

## 清理的目录

- `/Users/ai/Documents/video_pipeline/1input/` - 原始视频
- `/Users/ai/Documents/video_pipeline/2output/` - 成品视频
- `/Users/ai/Documents/video_pipeline/3daily/` - 临时文件（字幕、封面、元数据等）

## 清理方式

使用 Unix `find` 命令：
```bash
find /path/to/dir -type f ! -name ".cover_rotation_state" -exec rm -f {} +
```

这会删除目录中的所有文件，**但保留重要状态文件**：
- `.cover_rotation_state` - 封面背景颜色轮换状态（仅 3daily 目录保留）
- ⚠️ **重要**：封面轮换状态已迁移到 `4fixed/covers/.cover_rotation_state`，不会被清理

不删除子目录。

## 使用场景

### 场景1：每日开始前清理

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py
```

清理所有目录的所有文件，为新一天准备。

### 场景2：下载视频前清理

```bash
# 只清理 1input 目录
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py --input-only
```

### 场景3：预览清理

```bash
# 先预览要删除什么
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py --dry-run

# 确认后再执行
python /Users/ai/.claude/skills/clean-pipeline/scripts/clean.py
```

## 注意事项

- 清理操作不可逆，请确保重要文件已备份
- 删除所有文件，请谨慎使用
- 建议先用 `--dry-run` 预览
- 只删除文件，不删除子目录
- **封面轮换状态已迁移到 `4fixed/covers/.cover_rotation_state`，不会被清理影响**
- 清理完成后会自动发送 macOS 系统通知（显示删除文件数量和时间）

## 依赖

- Python 3.6+
- Unix find 命令（macOS/Linux 自带）

---

## 定时清理任务

### 自动定时清理（每天早上 6 点）

使用 macOS launchd 配置定时任务，每天早上 6 点（北京时间）自动清理视频管道目录。

#### 安装定时任务

```bash
# 安装定时任务（默认每天早上 6 点执行）
python /Users/ai/.claude/skills/clean-pipeline/scripts/install_cron.py --install

# 自定义执行时间（如每天早上 7 点 30 分）
python /Users/ai/.claude/skills/clean-pipeline/scripts/install_cron.py --install --hour 7 --minute 30
```

#### 卸载定时任务

```bash
python /Users/ai/.claude/skills/clean-pipeline/scripts/install_cron.py --uninstall
```

#### 查看定时任务

```bash
# 列出相关定时任务
python /Users/ai/.claude/skills/clean-pipeline/scripts/install_cron.py --list

# 查看所有系统定时任务
launchctl list

# 查看清理日志
cat ~/Library/Logs/videopipeline_clean.log
```

#### 定时任务配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 执行时间 | 每天 06:00 | 北京时间早上 6 点 |
| 清理脚本 | clean.py | 清理 1input、2output、3daily |
| 日志文件 | ~/Library/Logs/videopipeline_clean.log | 执行日志 |
| 错误日志 | ~/Library/Logs/videopipeline_clean_err.log | 错误日志 |

#### 工作原理

1. launchd 是 macOS 的定时任务管理器（类似 Linux 的 cron）
2. plist 文件定义了任务的执行时间和命令
3. 任务加载后会在指定时间自动执行
4. 执行日志会记录到 ~/Library/Logs 目录

#### 注意事项

- 定时任务使用系统本地时区，确保系统时区设置正确
- 如果修改系统时区，需要重新安装定时任务
- 清理操作不可逆，确保重要文件已备份
