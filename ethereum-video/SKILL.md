# ethereum-video: 以太坊视频剪辑

## 目标

从币圈行情视频中提取以太坊相关内容片段，拼接成独立的以太坊视频。

**输入**：Video4（或原始视频）+ 简体字幕 + 封面图片 + 视频标题
**输出**：以太坊视频（带封面和字幕）

## 使用方法

### 基本用法

```bash
python3 /Users/ai/.claude/skills/ethereum-video/scripts/generate_video.py \
  --cover-path="/path/to/cover.png" \
  --video-title="视频标题"
```

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `--cover-path` | 封面图片路径 | ✅ 必需 |
| `--video-title` | 视频标题（60-80字） | ✅ 必需 |

## 处理流程

### 步骤 1：检查 Video4

优先使用 Video4（已含字幕），如果不存在则使用原始视频。

### 步骤 2：读取字幕文件

从 `/Users/ai/Documents/video_pipeline/3daily/简体MMDD.srt` 读取字幕。

### 步骤 3：识别以太坊片段

**关键词**：
- `以太坊`
- `以太`
- `eth`（不区分大小写）

**识别规则**：
- 字幕内容包含任一关键词，该片段即为以太坊相关
- 记录该字幕的起始和结束时间
- 合并相邻或重叠的时间段

### 步骤 4：保留开头介绍（默认）

**默认**：保留开头介绍，从视频开始到"我是军长"结尾

### 步骤 5：提取视频片段

从 Video4 裁剪对应片段：
- 开头介绍片段（00:00 到"我是军长"结束）
- 以太坊片段（从"我们看一下以太坊"到视频结束）

### 步骤 6：拼接视频片段

将所有片段按时间顺序拼接：
1. 开头介绍片段
2. 以太坊片段

### 步骤 7：拼接封面和视频

- 前置 0.2 秒封面
- 拼接完整的以太坊内容
- 字幕已烧录在 Video4 中，无需额外处理

### 步骤 8：编码输出

- CRF 15，PRESET veryfast
- 音频 320k
- 输出：`2output/{视频标题}.mp4`

## 输入输出

### 输入

| 项目 | 路径 | 说明 |
|------|------|------|
| Video4 | `/Users/ai/Documents/video_pipeline/2output/4字幕*.mp4` | 自动检测最新 |
| 字幕文件 | `/Users/ai/Documents/video_pipeline/3daily/简体MMDD.srt` | 自动检测最新 |
| 封面图片 | `--cover-path` 参数 | 指定路径 |
| 视频标题 | `--video-title` 参数 | 60-80字 |

### 输出

| 文件 | 位置 | 说明 |
|------|------|------|
| 以太坊视频 | `/Users/ai/Documents/video_pipeline/2output/{视频标题}.mp4` | 1.1倍速，带封面和字幕 |

**视频文件命名规则**：
```
{日期}以太坊价格今日行情：{视频标题}（以太坊合约交易）军长
```

**示例**：
```
06.11以太坊价格今日行情：以太坊结构跟比特币一样，走双ABC下跌，小级别双锯齿反弹接近阻力位，1760附近压力明显，随时可能破位下行，今天需警惕（以太坊合约交易）军长
```

## 视频规格

| 参数 | 值 |
|------|-----|
| 视频编码 | libx264 |
| 像素格式 | yuv420p |
| Profile | high |
| Level | 4.2 |
| CRF | 15 |
| Preset | veryfast |
| 音频编码 | AAC |
| 音频码率 | 320k |

## 完成后必须动作

生成以太坊视频时，**必须完成以下 3 项**：

### 1. 告知截取时间信息

- 视频生成完成后，**必须列出截取时间信息**：
  - 开头介绍：Xs - Xs
  - 以太坊片段：Xs - Xs
  - 跳过的内容：Xs - Xs（X秒）

### 2. 发送完整视频标题

标题格式：`MM.DD以太坊价格今日行情：{完整标题内容}（以太坊合约交易）军长`

注意：
- 文件名因字节长度限制（200字节）可能被截断，脚本会额外输出 `📌 完整标题:`（未被截断的原始标题）
- 发给用户时必须拼接完整前后缀

### 3. 输出视频文件路径

输出完整的视频文件路径，方便用户查找。

## 边界说明

**本 Skill 做**：
- 读取字幕文件
- 找到以太坊内容
- 检查 Video4 是否存在
- 提取开头介绍 + 以太坊内容
- 拼接封面和视频
- 输出最终视频文件

**不做**：
- 生成封面图片（由 ethereum-cover 负责）
- 生成视频标题（由 ethereum-cover 调用 DeepSeek）
- 生成 Video4（由 video4-processing 负责）

## 依赖

- Python 3
- ffmpeg（路径：`/opt/homebrew/bin/ffmpeg`）
- Video4（或原始视频）
- 简体字幕文件
- 封面图片（由 ethereum-cover 生成）

## 与 ethereum-cover 的配合

本 skill 依赖 ethereum-cover 生成的封面图片和视频标题：

1. **第一步**：运行 ethereum-cover，生成封面图片和视频标题
2. **第二步**：运行 ethereum-video，使用封面图片和视频标题生成视频

```bash
# 第一步：生成封面和标题
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py --cover-text="看通道下破"

# 第二步：生成视频（使用第一步的输出）
python3 /Users/ai/.claude/skills/ethereum-video/scripts/generate_video.py \
  --cover-path="/Users/ai/Documents/video_pipeline/3daily/covers/看通道下破0611.png" \
  --video-title="以太坊结构跟比特币一样，走双ABC下跌，小级别双锯齿反弹接近阻力位，1760附近压力明显，随时可能破位下行，今天需警惕"
```

## 注意事项

- 优先使用 Video4（已含字幕和 1.1 倍速）
- **默认保留开头介绍**（到"我是军长"结尾）
- 封面图片由 ethereum-cover 生成
- 视频标题由 ethereum-cover 生成
- 如果 Video4 不存在，会提示用户先生成 Video4
- 文件名会被截断到 200 字节（文件系统限制）
