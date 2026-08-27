---
name: video3-processing
description: Video3字幕｜行情视频字幕版（1.1x + 2秒简体封面 + 烧录字幕 + 去重）。基于原始视频生成 Video3 成品视频，为带字幕版本，用于公开视频平台发布。触发词：生成视频3、生成字幕视频、video3、字幕视频、生成全部视频、全部视频
---

# Video3 字幕｜行情视频字幕版（1.1x + 2秒简体封面 + 烧录字幕）

## 目标

基于【原始视频】生成 Video3 成品视频。Video3 为带字幕版本，用于公开视频平台发布。

**核心原则**：
- ✅ 1.1 倍速播放（音画同步）
- ✅ 轻度去重处理
- ✅ 前置 0.2 秒简体封面
- ✅ 烧录字幕（硬字幕）
- ✅ 字幕时间轴延后 0.2 秒（匹配封面）
- ❌ 不依赖 Video1 / Video2
- ❌ 不生成软字幕

## ⚠️ 重要说明（必须遵守）

- Video3 直接基于【原始视频】
- 不依赖 Video1 / Video2
- 播放速率、时间轴必须与字幕文件完全一致
- SRT 是基于 1.1 倍速音频生成的，视频也必须是 1.1 倍速

---

## ⚠️ 字幕来源要求（关键）

**Video3 烧录的字幕必须基于用户审核后的 draft.txt 生成。**

**正确的工作流程**：
1. 音频 → 火山引擎 ASR → **原始识别**（包含大量错误，如"一探访"）
2. 原始识别 → **draft.txt**（供用户审核）
3. **用户人工审核修改 draft.txt** ← 关键步骤！
4. **根据审核后的 draft.txt 生成字幕（SRT）** ← 使用这个字幕！
5. Video3 烧录**审核后的字幕** ← 不是原始识别的字幕

**错误示例**：
- ❌ 直接使用原始 ASR 识别的字幕（包含错误）
- ❌ 修改了 draft.txt 但没有重新生成字幕
- ❌ 使用旧版本的字幕文件

**正确做法**：
- ✅ draft.txt 审核修改后，立即重新生成字幕
- ✅ 确认字幕文件是基于最新的 draft.txt
- ✅ 然后才生成 Video3

**验证方法**：
```bash
# 检查字幕内容是否与 draft.txt 一致
grep "以太坊" /Users/ai/Documents/video_pipeline/3daily/简体0805.srt
grep "以太坊" /Users/ai/Documents/video_pipeline/3daily/draft.txt
```

---

## 使用方法

### 自动模式（推荐）

自动处理 `/Users/ai/Documents/video_pipeline/1input/` 中最新的视频文件：

```bash
python /Users/ai/.claude/skills/video3-processing/scripts/process_video.py
```

### 手动指定视频和字幕

```bash
python /Users/ai/.claude/skills/video3-processing/scripts/process_video.py /path/to/video.mp4 /path/to/subtitle.srt
```

### 手动指定封面

```bash
python /Users/ai/.claude/skills/video3-processing/scripts/process_video.py video.mp4 sub.srt /path/to/cover.png
```

## 输入输出

### 输入

| 项目 | 路径 | 说明 |
|------|------|------|
| 原始视频 | `/Users/ai/Documents/video_pipeline/1input/` | mp4, mov, avi, mkv, flv, wmv, m4v |
| 字幕文件 | `/Users/ai/Documents/video_pipeline/3daily/` | `简体MMDD.srt`，与 Video1/Video2 共用 |
| 简体封面 | `/Users/ai/Documents/video_pipeline/3daily/covers/` | `cover_YYYYMMDD_simplified.png` |

### 输出

- **目录**：`/Users/ai/Documents/video_pipeline/2output/`
- **命名**：`3字幕_MMDD.mp4`（如 `3字幕_0209.mp4`）

## 处理流程

### 步骤 1：整体 1.1 倍速

- 视频 + 音频统一加速为 1.1 倍
- 不改变音调
- 保证音画同步
- 时间轴必须与 SRT 完全匹配

### 步骤 2：独立去重

- 在不影响画面的前提下做轻度去重
- 仅允许轻微饱和度调整
- 禁止裁剪、滤镜、水印、缩放

### 步骤 3：拼接简体封面

- 在视频最前面拼接一张封面
- 封面显示时长：0.2 秒
- 封面无音频
- 主视频音频从第 0.2 秒开始
- 拼接后的视频时间轴整体后移 0.2 秒

### 步骤 4：字幕时间轴处理（关键）

- 因为前面加了 0.2 秒封面
- 所有字幕时间轴必须整体【延后 0.2 秒】
- 不允许字幕提前
- 不允许字幕与画面错位

### 步骤 5：烧录字幕

- 使用 ffmpeg 的 subtitles 滤镜（libass）
- 字幕样式要求：
  - 字体：苹方
  - 字体颜色：白色
  - 字体大小：26
  - 字幕居中偏下
  - 黄色背景（`BackColour=&H0000FFFF&`）
  - 可读性优先
- 不加载外挂字体文件
- 不生成软字幕，只做硬字幕烧录

### 步骤 6：编码参数（固定）

| 参数 | 值 |
|------|-----|
| 视频编码 | libx264 |
| 像素格式 | yuv420p |
| Profile | high |
| Level | 4.2 |
| CRF | 15 |
| Preset | medium |
| FastStart | 启用 |

### 步骤 7：音频处理

- 使用原视频音频
- 已 1.1 倍速
- AAC
- 192 kbps

## 明确禁止事项

- ❌ 不重新生成音频
- ❌ 不生成 txt
- ❌ 不生成中间 mp4 文件
- ❌ 不调用 Video1 / Video2
- ❌ 不改变字幕内容
- ❌ 不修改字幕断句

## 一致性要求（非常重要）

Video1 / Video2 / Video3：
- 播放速率一致（1.1x）
- 音画时间轴一致
- 仅 Video3 因封面整体延后 0.2 秒字幕

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

## 完成后必须动作

- Python 3
- ffmpeg（路径：`/opt/homebrew/bin/ffmpeg`）
- 简体字幕文件（`简体MMDD.srt`）
- 简体封面图片（PNG）

## 一句话目标

生成一个基于原始视频的 1.1 倍速字幕版行情视频，前置 0.2 秒简体封面，字幕准确对齐，用于公开视频平台发布。

## 完成后必须动作

生成成功后，**必须把完整标题发送给用户**。标题从 Excel 读取（油管简体标题），脚本会自动输出 `📌 Video3 标题: ...`，执行后将该标题原文发给用户。
