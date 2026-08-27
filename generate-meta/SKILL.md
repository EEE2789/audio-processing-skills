---
name: generate-meta
description: 基于币圈行情分析文稿自动生成各平台标题和简介。从 final.txt 生成适配知乎、微博、油管、B站、Facebook、推特等平台的标题和简介，自动控制字数、添加前后缀、转换繁体，并写入 Excel。全自动运行，无需确认。触发词：生成标题、生成简介、生成元数据、多平台文案
---

# 币圈行情分析 - 多平台标题和简介生成

## 目标

基于币圈行情分析文稿（final.txt），自动生成各平台的标题和简介，并写入 Excel 文件。

**输入**：final.txt（币圈行情分析文稿）
**输出**：视频自动上传.xlsx（包含所有平台的标题和简介）

## 使用方法

### 基本用法（全自动）

```bash
python /Users/ai/.claude/skills/generate-meta/scripts/generate_meta.py /path/to/final.txt
```

### 示例

```bash
# 使用 3daily 文件夹中的 final.txt
python /Users/ai/.claude/skills/generate-meta/scripts/generate_meta.py /Users/ai/Documents/video_pipeline/3daily/final.txt
```

### 处理流程

1. 读取 final.txt
2. 从 Excel 读取平台配置
3. 调用 DeepSeek 生成基础标题和简介（**不含前后缀**）
4. 直接生成（无需确认）
5. 为每个平台添加前后缀
6. 写入 Excel

## 输出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 视频自动上传.xlsx | `/Users/ai/Documents/video_pipeline/2output/视频自动上传.xlsx` | 最终生成的文件 |

## 平台配置（Excel 驱动）

**重要**：平台配置完全由 Excel 文件维护，无需修改代码。

### 配置文件位置

```
/Users/ai/Documents/video_pipeline/4fixed/subtitle_rules/标题和简介要求2026-02-08.xlsx
```

### Excel 表格结构

| 列名 | 说明 | 示例 |
|------|------|------|
| 渠道 | 平台名称 | 知乎、微博、油管繁体 |
| 标题字数限制 | 标题最大字数 | 小于50、小于100 |
| 简介字数限制 | 简介最大字数 | 小于500、小于1000 |
| 标题前缀 | 标题开头内容 | 日期+比特币走势分析： |
| 标题后缀 | 标题结尾内容 | （比特币合约交易）军长 |
| 简介前缀 | 简介开头内容 | 今天比特币走势怎么样... |
| 简介后缀 | 简介结尾内容 | 免责声明、话题标签、链接 |

### 维护配置

直接编辑 Excel 文件即可：

- **调整字数限制**：修改"标题字数限制"和"简介字数限制"列
- **修改前后缀**：编辑对应的"标题前缀/后缀"和"简介前缀/后缀"列
- **调整平台顺序**：在 Excel 中拖动行调整顺序，输出将按此顺序生成
- **新增平台**：在 Excel 中添加新行

### 繁体转换

如果平台名称包含"繁体"或"繁體"，自动启用繁体转换。

### 支持的平台（默认）

| 平台 | 标题限制 | 简介限制 | 特殊处理 |
|------|----------|----------|----------|
| 知乎 | 50字 | 500字 | 话题标签 |
| 微博 | 30字 | 500字 | 话题标签 |
| 油管繁体 | 100字 | 500字 | 繁体转换 + Telegram链接 |
| 油管简体 | 100字 | 500字 | Telegram链接 |
| facebook | 100字 | 500字 | - |
| b站 | 80字 | 500字 | 免责声明+话题标签 |
| 推特 | 80字 | 500字 | $BTC 前缀 |

## 修改 DeepSeek Prompt

编辑 `scripts/generate_meta.py` 中的 `call_deepseek()` 函数：

```python
prompt = f'''你现在是一个币圈比特币和以太坊的行情分析师...
## 输出要求
请严格按以下 JSON 格式输出（不要有其他内容）：
{{
  "title_short": "（30-40字的短标题，用于知乎/微博/推特）",
  "title_long": "（80-100字的长标题，用于油管/B站/Facebook，包含更多细节）",
  "description": "（250-300字的简介，包含分析要点和风险提示）"
}}
'''
```

**注意**：DeepSeek 只生成基础内容，**不包含前后缀**。前后缀由脚本根据 Excel 配置自动添加。

## 环境变量

在 `.env` 文件中设置 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your_api_key_here
```

## 边界说明

**本 Skill 做**：
- 读取 final.txt
- 调用 DeepSeek 生成基础标题和简介（不含前后缀）
- 从 Excel 读取平台配置
- 按平台要求添加前后缀
- 繁体转换
- 写入 Excel（按 Excel 中的平台顺序）

**不做**：
- 音频/视频处理
- 字幕生成
- 视频上传

## 依赖

- Python 3
- openpyxl（Excel 处理）
- DeepSeek API
