# short-video: 币圈行情短视频自动剪辑

从横版行情视频 + SRT 字幕自动生成 9:16 竖版短视频（BTC/ETH），用于 YouTube Shorts / TikTok / Reels 分发。

## 触发词

短视频、剪辑短视频、生成短视频、短视频选段、short-video

## 流程概述

```
Video1（无字幕1.1倍速横版视频） + 简体SRT
  → DeepSeek LLM 选段（BTC/ETH，0-2条）
  → 程序侧校验（格式/时长/币种/边界）
  → FFmpeg 合成 1080x1920 竖版视频
  → 输出到 2output/
```

## 使用方式

### 自动模式（推荐）

自动检测最新的 Video1 和简体 SRT：

```bash
python3 ~/.claude/skills/short-video/main.py
```

### 指定文件

```bash
python3 ~/.claude/skills/short-video/main.py --video <video_path> --srt <srt_path> --output-dir <dir>
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--video` | Video1 路径 | 自动检测 2output/1繁体*.mp4 |
| `--srt` | 简体 SRT 路径 | 自动检测 3daily/简体*.srt |
| `--output-dir` | 输出目录 | 2output/ |

## 文件结构

```
~/.claude/skills/short-video/
├── SKILL.md            # 本文件
├── models.py           # 数据类型定义（ClipCandidate, ValidationResult）
├── timecode.py         # 时间码解析 + 视频时长获取
├── validator.py        # LLM 输出校验（硬错误/软错误/警告）
├── retry_prompt.py     # 重试提示词生成
├── llm_select.py       # DeepSeek LLM 选段调用
├── ffmpeg_template.py  # 模板参数 + filter graph 生成
├── render_clip.py      # FFmpeg 渲染单条短视频
└── main.py             # 串联全流程
```

## 输出规格

- 分辨率：1080x1920（9:16）
- 编码：H.264 + AAC
- 帧率：30fps
- 像素格式：yuv420p
- 命名：`YYYY-MM-DD_BTC_HHMMSS.mp4` 或 `YYYY-MM-DD_ETH_HHMMSS.mp4`

## 版式布局（三块比例式）

画布 1080x1920 按高度分为三块，各块内容在块内垂直居中：

```
┌──────────────────────────────┐ y=0      ─┐
│       第一块 30% (576px)      │           │ 顶部信息块
│                              │           │
│     标题 #FFB020 72px         │ y=162    │
│     核心提醒 #FFB020 76px     │ y=262    │ Title + Top Hook
│                              │           │ 块内居中
├──────────────────────────────┤ y=576    ─┤
│       第二块 40% (768px)      │           │ 中间内容块
│                              │           │
│     横版视频 1080x608         │ y=622    │
│                              │           │ Video + Subtitle
│     字幕 white 45px           │ y=1252   │ 块内居中
│                              │           │
├──────────────────────────────┤ y=1344   ─┤
│       第三块 30% (576px)      │           │ 底部提示块
│                              │           │
│  ┌────────────────────────┐  │           │
│  │ 黄底条 #F7C948         │  │ y=1589    │
│  │ 风险提醒 #111 62px     │  │ y=1450    │ 上移避开平台UI遮罩
│  └────────────────────────┘  │           │
│                              │           │
└──────────────────────────────┘ y=1920   ─┘
```

### 核心参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `title_y` | 162 | 标题 Y 坐标，块1居中 |
| `title_font_size` | 72 | 标题字号 |
| `top_hook_y` | 262 | 核心提醒 Y 坐标 |
| `top_hook_font_size` | 76 | 核心提醒字号 |
| `video_y` | 622 | 视频 Y 坐标，块2居中 |
| `subtitle y` | 1252 | 字幕 Y（视频下方 22px） |
| `subtitle_font_size` | 45 | 字幕字号 |
| `subtitle_border_width` | 6 | 字幕描边 |
| `bottom_warning_y` | 1450 | 风险提醒 Y 坐标，上移以避开平台UI遮罩 |
| `bottom_warning_font_size` | 62 | 风险提醒字号 |
| 字体文件 | Hiragino Sans GB.ttc | 统一使用 |

### 颜色方案

| 元素 | 颜色 | 说明 |
|------|------|------|
| Title | `#FFB020` | 金黄，与 Top hook 统一 |
| Top hook | `#FFB020` | 金黄，与 Title 统一 |
| 字幕 | white + black border | 白字黑边 |
| 底部黄条 | `#F7C948` | 黄色背景条 |
| 底部文字 | `#111111` | 深色字在黄条上 |
| 画布背景 | `#0B0D12` | 深色 |

### Top hook 换行规则

使用 `_wrap_hook()` 函数，强制 2 行：
- 优先在逗号处拆分（中文逗号 `，` 或英文逗号 `,`）
- 每行最多 8 字符
- 无逗号时从中点拆分
- 去除尾部标点

### 字幕渲染

- 使用 FFmpeg drawtext 逐条渲染（非 ASS）
- 每条字幕通过 `enable='between(t,start,end)'` 控制显示时间
- 无独立字幕带，字幕直接叠加在视频下方

## 依赖

- Python 3.9+
- FFmpeg 8.0+ (`/opt/homebrew/bin/ffmpeg`)
- DeepSeek API Key (`~/.claude/skills/ethereum-extract/.env`)
- requests 库

## Timeline 文件维护（重要）

`assets_timeline.json` 是短视频选段的关键依赖，记录每个币种分析的时间范围。

**位置**：`/Users/ai/Documents/video_pipeline/3daily/assets_timeline.json`

### 结构说明

```json
{
  "date": "YYYY-MM-DD",
  "intro": {"start_time": "00:00:00,000", "end_time": "00:00:04,660"},
  "assets": [
    {
      "name": "比特币",
      "start_time": "00:00:04,880",
      "end_time": "00:02:23,920",
      "start_ms": 4880,
      "end_ms": 143920,
      "duration_ms": 139040
    },
    {
      "name": "以太坊",
      "start_time": "00:02:23,920",
      "end_time": "00:03:44,440",
      "start_ms": 143920,
      "end_ms": 224440,
      "duration_ms": 80520
    }
  ]
}
```

### 确定时间范围的方法

**查找过渡句**：
```bash
grep -A1 "这个是比特币\|我们再来看一下以太坊\|来看一下以太坊" 3daily/简体*.srt
```

- BTC 结束时间 = "我们再来看一下以太坊" 的开始时间
- ETH 开始时间 = 同一时间点
- ETH 结束时间 = 最后一条字幕的结束时间

### 常见问题与修复

**问题**：短视频时长过短（< 20秒）

**原因**：timeline 中币种时间范围标记不完整，LLM 只看到被截断的字幕内容。

**检查方法**：
1. 查看 LLM 输出的 `duration_seconds`
2. 如果 < 20秒，检查 timeline 文件中对应币种的 `duration_ms`
3. BTC 通常应有 60-140 秒，ETH 通常应有 30-80 秒

**修复步骤**：
1. 查找过渡句确定正确的结束时间
2. 更新 `assets_timeline.json` 中对应币种的 `end_time` 和 `end_ms`
3. 重新运行 `main.py`

### 维护规则

1. **每次生成视频后检查 timeline**：确保时间范围完整覆盖该币种的所有分析内容
2. **删除重复条目**：同一币种只能有一个条目，删除旧的/短的版本
3. **时间连续性**：BTC 的 `end_ms` 应等于 ETH 的 `start_ms`

## 注意事项

- LLM 可能输出 0 条结果（不适合做短视频时）
- 校验失败最多自动重试 2 次
- Title 和 Top hook 统一使用 `#FFB020` 金黄色，风格一致
- Top hook 强制 2 行换行（`_wrap_hook()`，逗号优先拆分，每行 ≤8 字）
- 字幕使用 drawtext 逐条渲染，无独立字幕带
- 底部警告使用黄色背景条 + 深色文字
- 三块比例布局 30%/40%/30%，各块内容块内垂直居中
- BTC 主题色 `#F7931A`，ETH 主题色 `#627EEA`
- 设计文档位于 `~/Documents/Obsidian Vault/3.军长视频/短视频/`
- **Timeline 错误会导致短视频过短**：生成短视频前务必检查 timeline 文件
- **BTC 过短（< 60秒）通常意味着 timeline 标记不完整**
