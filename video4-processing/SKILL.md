---
name: video4-processing
description: Video4 剪辑用｜行情视频1.1倍速+字幕（无封面）。基于原始视频生成1.1倍速、带简体字幕烧录的视频，仅用于以太坊视频的剪辑源。无封面，字幕不延后。触发词：生成视频4、video4、剪辑用视频、生成剪辑源
---

# Video4 剪辑用｜行情视频 1.1倍速 + 字幕（无封面）

## 目标

基于原始视频生成 Video4，**仅作为以太坊视频的剪辑源**。

**核心原则**：
- ✅ 1.1 倍速播放（音画同步）
- ✅ 简体字幕烧录（与 Video3 格式一致）
- ✅ 轻度去重处理
- ✅ 标准编码参数
- ❌ **无封面**
- ❌ **字幕不延后**
- ❌ 不拼接片头片尾
- ❌ **不用于 Video1/Video2/Video3**（它们各自独立生成）

---

## ⚠️ 字幕来源要求（关键）

**Video4 烧录的字幕必须基于用户审核后的 draft.txt 生成。**

**正确的工作流程**：
1. 音频 → 火山引擎 ASR → **原始识别**（包含大量错误，如"一探访"）
2. 原始识别 → **draft.txt**（供用户审核）
3. **用户人工审核修改 draft.txt** ← 关键步骤！
4. **根据审核后的 draft.txt 生成字幕（SRT）** ← 使用这个字幕！
5. Video4 烧录**审核后的字幕** ← 不是原始识别的字幕

**错误示例**：
- ❌ 直接使用原始 ASR 识别的字幕（包含错误）
- ❌ 修改了 draft.txt 但没有重新生成字幕
- ❌ 使用旧版本的字幕文件

**正确做法**：
- ✅ draft.txt 审核修改后，立即重新生成字幕
- ✅ 确认字幕文件是基于最新的 draft.txt
- ✅ 然后才生成 Video4

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
python /Users/ai/.claude/skills/video4-processing/scripts/process_video.py
```

### 手动指定视频和字幕

```bash
python /Users/ai/.claude/skills/video4-processing/scripts/process_video.py /path/to/video.mp4 /path/to/subtitle.srt
```

## 输入输出

### 输入

| 项目 | 路径 | 说明 |
|------|------|------|
| 原视频 | `/Users/ai/Documents/video_pipeline/1input/` | mp4, mov, avi, mkv, flv, wmv, m4v |
| 字幕文件 | `/Users/ai/Documents/video_pipeline/3daily/` | `简体MMDD.srt`，**必须基于审核后的 draft.txt 生成** |

**⚠️ 重要**：字幕文件必须根据 `draft.txt`（用户审核修改后）生成。如果发现字幕内容错误（如"一探访"→"以太坊"），必须修正 `draft.txt` 后重新生成字幕，然后再生成 Video4。

### 输出

| 文件 | 位置 | 说明 |
|------|------|------|
| Video4 | `/Users/ai/Documents/video_pipeline/2output/4字幕MMDD.mp4` | 1.1倍速 + 字幕，无封面 |

## 处理规则

### 1. 播放速度

- 视频与音频整体统一加速为 **1.1 倍**
- 使用 `setpts=0.909*PTS` 和 `atempo=1.1`
- 仅改变播放速率，**不改变音调**
- 保证音画严格同步

### 2. 去重处理

- **轻微裁剪 + 锐化**：`crop=iw*0.99:ih*0.99` + `unsharp=3:3:0.3`
- **禁止**：加边框、水印、滤镜
- **禁止**：画面翻转、镜像

### 3. 字幕烧录

- 字幕样式与 Video3 **完全一致**：
  - 字体：苹方-中号
  - 字号：22
  - 颜色：白色不透明文字
  - 背景：灰色半透明背景
  - 位置：居中偏下
- **字幕时间轴不延后**（与原视频一致）
- **硬字幕烧录**

### 4. 编码参数（固定）

| 参数 | 值 |
|------|-----|
| 视频编码 | libx264 |
| 像素格式 | yuv420p |
| Profile | high |
| Level | 4.2 |
| CRF | 15 |
| Preset | slow |
| FastStart | 启用 |

### 5. 音频处理

| 参数 | 值 |
|------|-----|
| 音频编码 | AAC |
| 音频码率 | 320k |
| 处理 | 随视频 1.1 倍速 |

## Video4 的用途

**Video4 仅用于以太坊视频剪辑**：
- 截取开头介绍（00:00 到"我是军长"结束）
- 截取以太坊内容（从"我们再看一下以太坊"开始）
- 拼接以太坊封面

**Video1/Video2/Video3 各自独立生成**，不依赖 Video4。

## 明确禁止事项

- ❌ 不加封面
- ❌ 字幕不延后
- ❌ 不拼接片头或片尾
- ❌ 不生成独立音频文件

## 与 Video3 的区别

| 特性 | Video3 | Video4 |
|------|--------|--------|
| 封面 | 有（0.2秒比特币封面） | **无** |
| 字幕时间轴 | **延后 0.2 秒** | **不延后** |
| 用途 | 油管发布（比特币视频） | 以太坊视频剪辑源 |

## 重要注意事项

**多个视频处理必须串行执行**：

当需要生成 Video1、Video2、Video3、Video4 等多个视频时，**必须串行执行**（一个完成后再执行下一个），**禁止并行处理**。

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
# 等待完成后再执行
python video4-processing/scripts/process_video.py
```

**错误做法**：
```bash
# ❌ 错误：并行执行（在后台同时运行）
python video1-processing/scripts/process_video.py &
python video2-processing/scripts/process_video.py &
python video3-processing/scripts/process_video.py &
python video4-processing/scripts/process_video.py &
```

## 依赖

- Python 3
- ffmpeg（路径：`/opt/homebrew/bin/ffmpeg`）
- 简体字幕文件（`简体MMDD.srt`）

## 一句话目标

生成一个 1.1 倍速、带简体字幕烧录、无封面、字幕不延后的视频，作为以太坊视频的剪辑源。
