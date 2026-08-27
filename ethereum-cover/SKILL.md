# ethereum-cover: 以太坊封面生成

## 目标

生成以太坊视频的封面图片，不涉及视频剪辑。

**输入**：final.txt（币圈行情分析文稿）
**输出**：以太坊封面图片（PNG）

## 使用方法

### 基本用法（带人工审核）

```bash
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py
```

### 指定封面文字（跳过人工审核）

```bash
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py --cover-text="看通道下破"
```

### 指定背景颜色

```bash
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py green
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py red
```

### 同时指定封面文字和颜色

```bash
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py --cover-text="看通道下破" --color="yellow"
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--cover-text` | 封面文字（5字） | 自动生成 |
| `--color` | 背景颜色（green/red/blue/yellow） | 自动轮换 |
| `--review` | 审核模式（只保存到3daily/covers） | - |
| `--approve` | 审核通过标志，只有此参数存在时才保存到2output | - |

## ⚠️ 重要：审核流程规则

**未经用户审核的封面，绝不允许保存到 2output 目录。**

**正确流程**：
1. 运行脚本生成封面候选和审核封面（保存到 3daily/covers）
2. 用户审核封面候选
3. 用户选择封面文字后，使用 `--approve` 参数生成正式封面
4. 只有带 `--approve` 的封面才保存到 2output

**错误示例**：
- ❌ 直接使用 `--cover-text` 而不加 `--approve` 保存到 2output
- ❌ 未经用户确认就生成正式封面

**正确示例**：
```bash
# 第一步：生成封面候选（仅保存到3daily/covers）
python3 scripts/generate_cover.py

# 第二步：用户审核后，使用--approve生成正式封面
python3 scripts/generate_cover.py --cover-text="等回撤再多" --approve
```

## 处理流程

### 步骤 1：读取文稿

自动从 `/Users/ai/Documents/video_pipeline/3daily/final.txt` 读取最新文稿。

### 步骤 2：获取封面颜色

从 `/Users/ai/Documents/video_pipeline/4fixed/covers/.cover_rotation_state` 读取当天封面颜色，与比特币视频保持一致。

### 步骤 3：生成封面文字和视频标题

调用 DeepSeek 生成：
- **封面文字候选**（3个，每个5字）
- **视频标题**（60-80字）

**内容审核过滤**（仅限 DeepSeek API 调用）：

为避免 DeepSeek API 内容审核误判，提交给 API 的字幕内容会自动替换敏感词：
- `军长` → `分析师`
- `我是军长` → `我是分析师`

**重要**：
- ✅ 此过滤**仅影响提交给 DeepSeek API 的内容**
- ✅ 视频标题、文件命名、终端输出等**仍使用"军长"**
- ✅ 不影响最终生成的任何输出文件

### 步骤 4：人工审核（如果未指定封面文字）

暂停等待用户选择封面文字，然后生成封面图片。

### 步骤 5：生成封面图片

在以太坊专用背景图（`eth_*.png`）上叠加封面文字。

## 输出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 审核封面 | `/Users/ai/Documents/video_pipeline/3daily/covers/{封面文字}MMDD.png` | 默认输出，仅供审核 |
| 正式封面 | `/Users/ai/Documents/video_pipeline/2output/{封面文字}MMDD.png` | **仅在使用 --approve 时生成** |

**⚠️ 重要**：未经用户审核（未使用 `--approve` 参数），封面**只保存到 3daily/covers**，**绝不保存到 2output**。

**命名示例**：`看通道下破0611.png`

## 封面背景图

使用以太坊专用背景图（与比特币不同）：

```
/Users/ai/.claude/skills/ethereum-cover/assets/
├── eth_green.png   # 绿色背景（看涨）
├── eth_red.png     # 红色背景（看跌）
├── eth_blue.png    # 蓝色背景（中性）
└── eth_yellow.png  # 黄色背景（警示）
```

**背景颜色规则**：
- 与比特币视频共用同一轮换状态文件
- 轮换顺序：green → red → blue → yellow → 循环

## 封面文字要求

### 生成规则（调用 DeepSeek）

1. **严格 5 个中文字符**
2. 风格：理性、技术分析、行情判断
3. **禁止使用**：暴涨、暴跌、起飞、机会、必看、震惊、一定、稳赚
4. **禁止使用**：感叹号、表情符号

### 参考风格

- 短期见底没
- 反弹后再跌
- 关注82阻力
- Y浪尾声
- 等待反弹
- 多头抵抗增强
- 空头动能衰竭
- 关注B浪反弹

## 视频标题说明

本 skill **只生成视频标题**，不用于文件命名。

视频标题格式：
- 60-80字
- 不含短标题、日期
- 不含任何括号内容
- 保留所有标点符号
- **末尾不使用句号**（在拼接完整标题时自动去除）

**示例**：
```
以太坊结构跟比特币一样，走双ABC下跌，小级别双锯齿反弹接近阻力位，1760附近压力明显，随时可能破位下行，今天需警惕
```

完整标题（在生成视频时拼接）：
```
MM.DD以太坊价格今日行情：{视频标题}（以太坊合约交易）军长
```

**注意**：视频标题末尾的句号会在拼接时自动去除，确保最终标题格式正确。

## 封面文字审核（强制）⚠️

封面文字必须经过人工审核才能生成封面图片。

### 审核流程

1. 运行脚本，DeepSeek 生成 3 个封面文字候选
2. 显示封面文字候选和视频标题
3. 暂停等待用户选择
4. 用户选择后，生成封面图片

### 重要说明

- ❌ **没有跳过审核的选项**
- ❌ **没有 `--auto` 自动模式**
- ✅ **每个封面都必须经过人工确认**
- ✅ **必须使用 `--cover-text=` 明确指定封面文字**

## 边界说明

**本 Skill 做**：
- 读取 final.txt
- 调用 DeepSeek 生成封面文字候选和视频标题
- 人工审核选择封面文字
- 生成以太坊封面图片
- 轮换背景颜色

**不做**：
- 视频剪辑
- 字幕处理
- 生成视频

## 依赖

- Python 3
- Pillow（图像处理库）
- DeepSeek API

### 安装依赖

```bash
pip3 install Pillow python-dotenv
```

## 环境变量

在 `.env` 文件中设置 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your_api_key_here
```

## 与 ethereum-video 的配合

本 skill 生成的封面图片和视频标题，供 ethereum-video skill 使用：

1. **第一步**：运行 ethereum-cover，生成封面图片和视频标题
2. **第二步**：运行 ethereum-video，使用封面图片和视频标题生成视频

```bash
# 第一步：生成封面
python3 /Users/ai/.claude/skills/ethereum-cover/scripts/generate_cover.py --cover-text="看通道下破"

# 第二步：生成视频
python3 /Users/ai/.claude/skills/ethereum-video/scripts/generate_video.py --cover-path="/path/to/cover.png" --video-title="视频标题"
```
