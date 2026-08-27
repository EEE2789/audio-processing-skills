---
name: telegram-download
description: 从云服务器 43.167.173.8 手动拉取最新 Telegram 视频到本地。当用户说下载视频、下载、拉取视频、同步视频时应使用本 skill。
---

# Telegram 视频下载

## 目标

从云服务器 `43.167.173.8:/root/videos/` 手动拉取最新 Telegram 视频到本地目录。

## 优先级

处理“下载视频 / 下载 / 拉取视频 / 同步视频”这类请求时，默认优先使用云服务器手动拉取方案：

1. 首选：从 `43.167.173.8:/root/videos/` 手动拉取到本地
2. 不要使用任何 Telethon 本地直连下载方案

不要主动要求用户去创建 Telegram 应用，也不要回退到历史本地直连流程。

## 使用方法

### 手动从云服务器拉取最新视频

适合高时效场景。看到新视频后，直接手动执行一次即可，不需要等待定时任务。

这是当前默认推荐方案。

```bash
bash /Users/ai/.claude/skills/telegram-download/scripts/pull_latest_videos.sh
```

可选指定本地目录：

```bash
bash /Users/ai/.claude/skills/telegram-download/scripts/pull_latest_videos.sh /path/to/local/dir
```

如果不想每次输入密码，可以先设置：

```bash
export TG_VIDEO_SERVER_PASSWORD='服务器密码'
bash /Users/ai/.claude/skills/telegram-download/scripts/pull_latest_videos.sh
```

如果后续你想配置 SSH 免密，再使用：

```bash
bash /Users/ai/.claude/skills/telegram-download/scripts/setup_ssh.sh
```

## 工作流程

1. 云服务器上的 bot 将视频下载到 `/root/videos/`
2. 本地手动执行 `pull_latest_videos.sh`
3. 脚本通过 `expect + rsync` 拉取新增 `.mp4`
4. 已存在的本地文件会自动跳过

## 配置说明

### 云服务器手动拉取默认路径

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| TG_VIDEO_SERVER_IP | 云服务器地址 | 43.167.173.8 |
| TG_VIDEO_SERVER_USER | 登录用户 | root |
| TG_VIDEO_REMOTE_DIR | 服务器视频目录 | /root/videos |
| TG_VIDEO_LOCAL_DIR | 本地下载目录 | /Users/ai/Documents/video_downloads |

## 注意事项

1. 当前唯一推荐方案是“云服务器 bot 下载 + 本地手动拉取”
2. 本地目录默认是 `/Users/ai/Documents/video_downloads`
3. 云服务器目录默认是 `/root/videos`
4. 下载前请确保本地目标目录有足够空间
5. Claude 侧唯一主入口脚本是 `pull_latest_videos.sh`
