---
name: extract-1.1x-audio
description: 从本地视频文件提取音频并加速到1.1倍，用于火山引擎字幕。自动读取1input文件夹最新视频，或指定视频路径。输出符合火山引擎要求的WAV音频（16k/mono/pcm_s16le）。仅处理音频，不生成字幕、不处理视频画面。触发词：提取音频、加速音频、1.1倍音频
---

# 提取1.1倍音频

## 目标

从本地视频文件中提取音频，并将音频加速到 1.1 倍，用于后续调用火山引擎生成字幕。

**输入**：自动从 `/Users/ai/Documents/video_pipeline/1input/` 读取最新视频（或手动指定路径）
**输出**：加速后的 WAV 音频文件路径

## 使用方法

### 自动模式（推荐）

```bash
python /Users/ai/.claude/skills/extract-1.1x-audio/scripts/extract_audio.py
```

自动处理 `1input` 文件夹中最新的视频文件。

### 手动指定视频

```bash
python /Users/ai/.claude/skills/extract-1.1x-audio/scripts/extract_audio.py <视频路径>
```

### 示例

```bash
# 自动处理最新视频
python /Users/ai/.claude/skills/extract-1.1x-audio/scripts/extract_audio.py

# 手动指定视频
python /Users/ai/.claude/skills/extract-1.1x-audio/scripts/extract_audio.py "/path/to/video.mp4"
```

## 输出规则

### 输入目录（固定）

```
/Users/ai/Documents/video_pipeline/1input/
```

### 输出目录（固定）

```
/Users/ai/Documents/video_pipeline/3daily/audio/
```

### 命名规则（固定）

格式：`<原视频文件名>_YYYYMMDD.wav`

示例：
- `0119比特币行情分析_20260126.wav`
- `0205_20260208.wav`

### 命名规则（固定）

格式：`<原视频文件名>_YYYYMMDD.wav`

示例：
- `0119比特币行情分析_20260126.wav`
- `0207 4_20260207.wav`

## 技术规格

### ffmpeg 路径

```
/opt/homebrew/bin/ffmpeg
```

### 音频处理规则

- **仅对音频做 1.1 倍变速**
- **保持音调不变**（不升调、不降调）
- **不涉及任何视频处理**

### 输出音频格式

| 参数 | 值 | 说明 |
|------|-----|------|
| 格式 | WAV | 波形格式 |
| 编码 | pcm_s16le | 16位小端PCM |
| 采样率 | 16000 Hz | 火山引擎要求 |
| 声道 | 单声道（mono） | 火山引擎要求 |
| 位深 | 16 bit | CD音质 |

## 异常处理

| 错误 | 处理 |
|------|------|
| 视频文件不存在 | 明确报错 "❌ 视频文件不存在" |
| 视频中无音轨 | 明确报错 "❌ 视频中无音轨 (no audio stream)" |
| ffmpeg 执行失败 | 输出关键错误信息 |
| 输出目录不存在 | 自动创建 |

## 明确不做

- ❌ 不生成字幕
- ❌ 不调用火山引擎 API
- ❌ 不处理视频画面（不改 fps、不加片头、不拼接）
- ❌ 不做字幕优化、不做文本处理
- ❌ 不生成多余的中间文件

## 设计原则

- Skill 可被每日重复调用
- 输出文件可直接作为火山引擎字幕输入
- 行为确定、结果稳定、无歧义
