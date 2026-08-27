---
name: video2-processing
description: Video2简体｜行情视频简体版（1.1x 去重 + 结尾提示）。基于原始视频生成 Video2 成品视频，包含结尾拼接与文字提示，用于简体渠道分发。触发词：生成视频2、生成简体视频、video2、简体视频、生成全部视频、全部视频
---

# Video2 简体｜行情视频简体版（1.1x 去重 + 结尾提示）

## 目标

基于【原始视频】生成 Video2 成品视频。Video2 用于简体渠道分发，包含结尾拼接与文字提示。

**核心原则**：
- ✅ 1.1 倍速播放（音画同步）
- ✅ 轻度去重处理
- ✅ 文字提示「结尾有惊喜」
- ✅ 结尾拼接 outro_fix.mp4
- ✅ 标准编码参数
- ❌ 不烧录字幕
- ❌ 不加封面
- ❌ 不基于 Video1（直接基于原始视频）

## ⚠️ 重要说明（必须遵守）

- Video2 **不是**基于 Video1
- Video2 直接基于【原始视频】
- Video1 / Video2 / Video3 三者：
  - 播放速率完全一致（1.1x）
  - 时间轴完全一致
  - 以确保共用同一套字幕文件时不会错位

## 使用方法

### 自动模式（推荐）

自动处理 `/Users/ai/Documents/video_pipeline/1input/` 中最新的视频文件：

```bash
python /Users/ai/.claude/skills/video2-processing/scripts/process_video.py
```

### 手动指定视频

```bash
python /Users/ai/.claude/skills/video2-processing/scripts/process_video.py /path/to/video.mp4
```

## 输入输出

### 输入

- **目录**：`/Users/ai/Documents/video_pipeline/1input/`
- **格式**：mp4, mov, avi, mkv, flv, wmv, m4v
- **规则**：自动选择最新视频，或命令行指定

### 结尾素材（固定）

- **文件**：`/Users/ai/Documents/video_pipeline/4fixed/assets/outro_fix.mp4`
- **说明**：该结尾视频已提前处理为与主视频参数一致

### 输出

- **目录**：`/Users/ai/Documents/video_pipeline/2output/`
- **命名**：`2简体MMDD.mp4`（如 `2简体0209.mp4`）
- **规格**：详见下方

## 处理规则

### 1. 播放速度

- 视频与音频整体统一加速为 **1.1 倍**
- 使用 `setpts=0.909*PTS` 和 `atempo=1.1`
- 仅改变播放速率，**不改变音调**
- 保证音画严格同步

### 2. 去重处理

对视频内容进行轻度去重处理，规避平台重复内容识别：

- **饱和度轻微调整**：`eq=saturation=1.02`
- **禁止**：裁剪画面
- **禁止**：加边框、水印、滤镜
- **禁止**：画面翻转、镜像

### 3. 文字提示（仅提示，不是字幕）

- 在主视频播放约第 20 秒左右
- 左下角显示白色文字：`「结尾有惊喜」`
- 显示时间约 3 秒
- 字体清晰、不抢画面
- 该文字为画面提示，不属于字幕

### 4. 结尾拼接

- 在主视频结束后
- 无缝拼接 `outro_fix.mp4`
- 音频与视频一并拼接
- 拼接后整体时间轴连续

### 5. 画面与帧率

| 参数 | 值 |
|------|-----|
| 帧率 | 29.97 fps |
| 分辨率 | 保持原视频尺寸 |
| 比例 | 不拉伸、不裁切 |

### 6. 编码参数（固定）

| 参数 | 值 |
|------|-----|
| 视频编码 | libx264 |
| 像素格式 | yuv420p |
| Profile | high |
| Level | 4.2 |
| CRF | 15 |
| Preset | medium |
| FastStart | 启用 |

### 7. 音频处理

| 参数 | 值 |
|------|-----|
| 音频编码 | AAC |
| 音频码率 | 192k |
| 处理 | 随视频 1.1 倍速 |

## 明确禁止事项

- ❌ 不生成独立音频文件
- ❌ 不调用字幕文件
- ❌ 不烧录字幕
- ❌ 不加封面
- ❌ 不修改结尾视频内容
- ❌ 不改变命名规则

## 一致性要求（非常重要）

Video1、Video2、Video3 将共用同一套字幕，字幕基于 1.1 倍速音频生成。

因此 **Video2 的时间轴必须完全准确**，确保与字幕严格同步。

## 重要注意事项

**多个视频处理必须串行执行**：

当需要生成 Video1、Video2、Video3 等多个视频时，**必须串行执行**（一个完成后再执行下一个），**禁止并行处理**。

**原因**：
- 视频编码是 CPU/内存密集型任务
- 并行处理会导致资源竞争，降低编码质量
- 可能导致视频帧率不稳定、编码参数混乱

**正确做法**：
```bash
# ✅ 正确：串行执行
python video1-processing/scripts/process_video.py
# 等待完成后再执行
python video2-processing/scripts/process_video.py
# 等待完成后再执行
python video3-processing/scripts/process_video.py
```

**错误做法**：
```bash
# ❌ 错误：并行执行（在后台同时运行）
python video1-processing/scripts/process_video.py &
python video2-processing/scripts/process_video.py &
python video3-processing/scripts/process_video.py &
```

## 依赖

- Python 3
- ffmpeg（路径：`/opt/homebrew/bin/ffmpeg`）
- 结尾素材：`/Users/ai/Documents/video_pipeline/4fixed/assets/outro_fix.mp4`

## 一句话目标

生成一个基于原始视频的 1.1 倍速简体行情视频，带结尾提示与结尾拼接，用于简体渠道发布。
