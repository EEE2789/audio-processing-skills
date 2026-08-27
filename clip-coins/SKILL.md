# clip-coins: 币种/股票独立视频剪辑

## 目标

基于 Video4 和资产时间轴（`assets_timeline.json`），自动剪辑每个币种/股票的独立视频。

**剪辑规则**：
- 开头介绍（从 `assets_timeline.json` 读取）
- 该币种/股票的独立内容
- 无封面
- 保留字幕（Video4 已烧录字幕）

**输入**：
- Video4（`2output/4字幕MMDD.mp4`）
- 资产时间轴（`3daily/assets_timeline.json`）

**输出**：
- 每个币种/股票的独立视频（`2output/MMDD{币种名称}.mp4`）

---

## 使用方法

### 自动模式（推荐）

自动读取最新的 Video4 和资产时间轴：

```bash
python /Users/ai/.claude/skills/clip-coins/scripts/clip_coins.py
```

### 指定文件

```bash
python /Users/ai/.claude/skills/clip-coins/scripts/clip_coins.py /path/to/video4.mp4 /path/to/timeline.json
```

### 示例

```bash
# 自动模式
python ~/.claude/skills/clip-coins/scripts/clip_coins.py

# 指定文件
python ~/.claude/skills/clip-coins/scripts/clip_coins.py \
  /Users/ai/Documents/video_pipeline/2output/4字幕0613.mp4 \
  /Users/ai/Documents/video_pipeline/3daily/assets_timeline.json
```

---

## 处理流程

### 步骤 1：读取资产时间轴

从 `assets_timeline.json` 读取：
- 开头介绍时间范围（`start_ms`, `end_ms`）
- 所有资产列表（比特币除外）
- 每个资产的完整时间范围（`start_ms`, `end_ms`, `duration_ms`）

### 步骤 2：跳过比特币

比特币是主视频内容，跳过不剪辑。

### 步骤 3：读取币种时间范围

- 从 JSON 直接读取每个币种的开始时间和结束时间
- 不再需要计算结束时间（analyze-assets skill 已计算）
- 结束时间 = 下一个资产的开始时间（或视频总时长）

### 步骤 4：提取视频片段

对于每个币种（比特币除外）：
1. **提取开头介绍**：`intro_start` 到 `intro_end`
2. **提取币种内容**：`coin_start` 到 `coin_end`（从 JSON 读取）
3. **拼接片段**：开头介绍 + 币种内容

### 步骤 5：编码输出

- 使用与 Video4 一致的编码参数
- 输出到 `2output/` 目录
- 命名格式：`MMDD{币种名称}.mp4`

---

## 输出示例

假设 `assets_timeline.json` 包含：

```json
{
  "date": "2026-06-13",
  "intro": {
    "start_time": "00:00:00,000",
    "start_ms": 0,
    "end_time": "00:00:05,980",
    "end_ms": 5980,
    "description": "开头自我介绍"
  },
  "assets": [
    {
      "name": "比特币",
      "start_time": "00:00:06,200",
      "end_time": "00:01:18,960",
      "start_ms": 6200,
      "end_ms": 78960,
      "duration_ms": 72760,
      "description": "在 00:00:06,200 - 00:01:18,960"
    },
    {
      "name": "黄金",
      "start_time": "00:01:21,840",
      "end_time": "00:03:02,440",
      "start_ms": 81840,
      "end_ms": 182440,
      "duration_ms": 100600,
      "description": "在 00:01:21,840 - 00:03:02,440"
    },
    {
      "name": "以太坊",
      "start_time": "00:03:02,440",
      "end_time": "00:05:47,360",
      "start_ms": 182440,
      "end_ms": 347360,
      "duration_ms": 164920,
      "description": "在 00:03:02,440 - 00:05:47,360"
    },
    {
      "name": "XLM",
      "start_time": "00:05:47,360",
      "end_time": "00:06:02,180",
      "start_ms": 347360,
      "end_ms": 362180,
      "duration_ms": 14820,
      "description": "在 00:05:47,360 - 00:06:02,180"
    }
  ],
  "total_count": 4
}
```

输出视频：
1. **0613黄金.mp4** = 开头介绍(0-5.98s) + 黄金内容(1:21.84s - 3:02.44s)
2. **0613以太坊.mp4** = 开头介绍(0-5.98s) + 以太坊内容(3:02.44s - 5:47.36s)
3. **0613XLM.mp4** = 开头介绍(0-5.98s) + XLM内容(5:47.36s - 6:02.18s)

**不输出**：0613比特币.mp4（跳过）

---

## 输入输出

### 输入

| 项目 | 路径 | 说明 |
|------|------|------|
| Video4 | `/Users/ai/Documents/video_pipeline/2output/4字幕MMDD.mp4` | 自动读取最新 |
| 资产时间轴 | `/Users/ai/Documents/video_pipeline/3daily/assets_timeline.json` | 自动读取 |

### 输出

| 文件 | 位置 | 说明 |
|------|------|------|
| 币种视频 | `/Users/ai/Documents/video_pipeline/2output/MMDD{币种名称}.mp4` | 每个币种一个视频 |

### 编码参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 视频编码 | libx264 | 与 Video4 一致 |
| 像素格式 | yuv420p | 标准格式 |
| Profile | high | 高质量 |
| Level | 4.2 | 兼容性 |
| CRF | 15 | 高质量 |
| Preset | veryfast | 快速编码 |
| 音频编码 | aac | 标准音频 |

---

## 技术细节

### 时间范围读取

直接从 assets_timeline.json 读取完整的时间范围（不再计算）：

```python
# 开头介绍（从 JSON 读取）
intro_start = intro_data['start_ms'] / 1000
intro_end = intro_data['end_ms'] / 1000

# 币种内容（从 JSON 读取，包含结束时间）
coin_start = assets[N]['start_ms'] / 1000
coin_end = assets[N]['end_ms'] / 1000

# 计算时长（可选）
duration_s = coin_end - coin_start
```

**优势**：
- 不再需要调用 FFmpeg 获取视频总时长
- 不需要计算下一个资产的开始时间
- analyze-assets 已完成所有时间计算
- JSON 中的时间范围更准确

### FFmpeg 命令

**提取开头介绍**：
```bash
ffmpeg -i video4.mp4 -ss 0 -t 5.98 -c:v libx264 -c:a aac intro.mp4
```

**提取币种内容**：
```bash
ffmpeg -i video4.mp4 -ss 81.84 -to 182.44 -c:v libx264 -c:a aac coin.mp4
```

**拼接视频**：
```bash
ffmpeg -f concat -i filelist.txt -c copy output.mp4
```

或一次性完成：
```bash
ffmpeg -i video4.mp4 \
  -ss 0 -t 5.98 \
  -ss 81.84 -to 182.44 \
  -filter_complex "[0:v] [0:a] concat=n=2:v=1:a=0[v] [a]" \
  -map "[v]" -map "[a]" \
  output.mp4
```

---

## 依赖

- Python 3
- FFmpeg (`/opt/homebrew/bin/ffmpeg`)
- Video4（已存在）
- assets_timeline.json（已存在）

---

## 注意事项

1. **自动检测资产时间轴**：
   - 脚本会自动检查 `assets_timeline.json` 是否存在且最新
   - 如果文件不存在或比最新字幕文件旧，会提示重新运行 analyze-assets
   - 避免重复分析，提高效率

2. **Video4 必须存在**：剪辑基于 Video4，如果没有需要先生成

3. **比特币被跳过**：比特币是主视频内容，不单独剪辑

4. **无封面**：剪辑的视频不添加封面，直接使用 Video4 的内容

5. **字幕已烧录**：Video4 已包含字幕，剪辑后的视频自动包含字幕

6. **时间范围智能检测**：
   - 自动比较字幕文件和 JSON 文件的修改时间
   - 如果字幕更新了，会自动提示重新分析资产时间轴

---

## 错误处理

| 错误 | 处理 |
|------|------|
| Video4 不存在 | 提示错误，建议先生成 Video4 |
| assets_timeline.json 不存在或过期 | 提示重新运行 analyze-assets，并提供完整命令 |
| 资产列表为空 | 提示无币种可剪辑 |
| FFmpeg 失败 | 输出错误信息，检查视频文件 |

**智能检测逻辑**：
- 自动比较字幕文件和 JSON 文件的修改时间
- 如果字幕更新了，自动提示重新分析，避免使用过期数据
- 只有在必要时才要求重新运行 analyze-assets

---

## 文件组织规则

**重要**：只有正式发布版视频才能放在 `2output/` 文件夹，中间剪辑文件必须放在 `3daily/` 文件夹。

### 文件夹用途

| 文件夹 | 用途 | 内容 |
|------|------|------|
| `2output/` | 正式发布版 | 最终发布给用户的视频 |
| `3daily/` | 中间文件 | 剪辑过程中的片段文件、临时文件 |

### 币种视频剪辑文件分类

**中间剪辑片段**（放在 `3daily/`）：
- `{币种}_intro_MMDD.mp4` - 开头自我介绍片段
- `{币种}_content_MMDD.mp4` - 币种内容片段

**正式发布版**（放在 `2output/`）：
- `MMDD{币种}.mp4` - 剪辑拼接后的币种视频（由 coin-metadata 重命名为标准格式）

### 剪辑流程

1. 剪辑开头片段 → `3daily/{币种}_intro_MMDD.mp4`
2. 剪辑内容片段 → `3daily/{币种}_content_MMDD.mp4`
3. 拼接两个片段 → `2output/MMDD{币种}.mp4`
4. 生成元数据 → `2output/MM.DD{币种}价格今日行情...mp4`

### 错误示例

❌ **错误**：将剪辑片段直接放到 `2output/`
```
2output/eth_intro_0721.mp4     # 错误！这是中间文件
2output/eth_content_0721.mp4   # 错误！这是中间文件
```

✅ **正确**：将剪辑片段放到 `3daily/`，拼接后的正式版放到 `2output/`
```
3daily/eth_intro_0721.mp4      # 正确！中间文件
3daily/eth_content_0721.mp4    # 正确！中间文件
2output/以太坊0721.mp4          # 正确！正式版（会被 coin-metadata 重命名）
```

---

## 一句话目标

基于 Video4 和资产时间轴，自动剪辑每个币种（除比特币外）的独立视频，包含开头介绍和币种内容。
