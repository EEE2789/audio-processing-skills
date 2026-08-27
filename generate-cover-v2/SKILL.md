---
name: generate-cover-v2
description: YouTube 比特币行情分析视频封面生成。基于字幕 TXT 文档生成标题，使用已存在的背景模板图生成简体/繁体两套封面。支持自动模式（--auto）跳过人工审核。背景图为只读品牌资产，不生成背景、不调用文生图 API。支持指定背景颜色（green/red/blue/yellow）或自动轮换。触发词：生成封面、封面生成、youtube封面、封面图
---

# YouTube 封面生成 v2 - 币圈行情分析

## 目标

基于视频字幕生成的 TXT 文档，生成视频封面标题，并使用"已存在的背景模板图"生成简体与繁体两套 YouTube 封面图。

**核心原则**：
- ✅ 使用已存在的背景模板图
- ❌ 不生成背景图
- ❌ 不调用文生图 API
- ✅ 背景图为"只读品牌资产"

## 使用方法

### 基本用法（带人工审核）

```bash
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py
```

### 自动模式（跳过人工审核）

```bash
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py --auto
```

### 指定文稿

```bash
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py /path/to/subtitle.txt
```

### 指定标题（⚠️ 必须使用等号格式）

```bash
# 正确格式：使用 --title=标题 （注意等号，无空格）
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py --auto --title=反抽加空单

# 错误格式：使用空格分隔会导致参数被忽略
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py --auto --title "反抽加空单"  # ❌ 错误！
```

**重要提示**：
- `--title=xxx` 是唯一支持的格式
- `--title "xxx"` 会导致标题参数被忽略，脚本会使用 AI 生成的标题

### 指定背景颜色

```bash
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py green
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py red
```

### 指定日期

```bash
python /Users/ai/.claude/skills/generate-cover-v2/scripts/generate_cover.py 20260208
```

## 交互流程

**自动模式（--auto）**：
1. **读取文稿** - 自动读取 `final.txt` 或指定路径
2. **生成标题** - DeepSeek 生成 3 个标题候选
3. **自动选择** - 自动使用第 1 个候选标题
4. **选择背景** - 根据参数指定或自动轮换选择背景图
5. **生成封面** - 生成简体 + 繁体两套封面
6. **保存输出** - 保存到 `3daily/covers/` 目录

**人工审核模式（默认）**：
1. **读取文稿** - 自动读取 `final.txt` 或指定路径
2. **生成标题** - DeepSeek 生成 3 个标题候选（5字为主，最多6字）
3. **人工审核** - ⏸️ **等待用户选择 1/2/3 或输入自定义标题**
4. **选择背景** - 根据参数指定或自动轮换选择背景图
5. **生成封面** - 生成简体 + 繁体两套封面
6. **保存输出** - 保存到 `3daily/covers/` 目录

## 背景图资产说明（非常重要）

### 背景图位置

所有封面背景图已提前制作完成，存放于 `assets` 目录：

```
/Users/ai/.claude/skills/generate-cover-v2/assets/
├── background_green.png
├── background_red.png
├── background_blue.png
└── background_yellow.png
```

### Skill 的职责

- ✅ 根据参数或轮换规则，从 assets 中选择背景图
- ✅ 在背景图上叠加标题文字
- ❌ **不生成背景图**
- ❌ **不修改背景颜色、布局、元素**
- ❌ **不调整 Logo、固定文案位置**

**背景图为"只读品牌资产"**

### 背景图选择规则

**4 种颜色对应固定文件**：
- `green` - 绿色背景（看涨）
- `red` - 红色背景（看跌）
- `blue` - 蓝色背景（中性）
- `yellow` - 黄色背景（警示）

**选择方式**：
1. **人工指定**：命令行传入颜色参数（如 `green`）
2. **自动轮换**：若未指定，按 green → red → blue → yellow → 循环

### ⚠️ 重要：按最新记录而非日期轮换

**规则变更（2026-03-19）**：
- 封面背景颜色**按最新生成的视频记录轮换**，而非按日历日期
- 如果某天没有制作视频，该日期的背景色不占用轮换位置
- 下一次制作视频时，继续使用上一次视频的背景色的下一个颜色

**示例**：
- 3月17日：green（有视频）
- 3月18日：（无视频，跳过）
- 3月19日：red（继续 3月17日的下一个颜色）

**代码实现**：
- 读取 `.cover_rotation_state` 文件的**最后一条记录**
- 获取最后一条记录的颜色，按轮换顺序确定下一个颜色
- 不要依赖当前日历日期计算颜色

### 如何查询历史背景色

**背景色轮换状态文件位置**：
```
/Users/ai/Documents/video_pipeline/4fixed/covers/.cover_rotation_state
```

**查询命令**：
```bash
cat /Users/ai/Documents/video_pipeline/4fixed/covers/.cover_rotation_state
```

**输出示例**：
```json
{
  "2026-03-09": "red",
  "2026-03-10": "blue",
  "2026-03-11": "yellow"
}
```

根据历史记录和轮换顺序（green → red → blue → yellow），可推算今天应该使用的背景色。

## 标题生成规则（调用 DeepSeek）

### 生成要求

1. 根据字幕 TXT 内容，生成「3 个候选标题（简体中文）」
2. 标题要求：
   - 以 5 个字为主（最多 6 个字）
   - 偏交易、行情、走势判断
   - 不使用营销、夸张、诱导性词汇
   - 不出现违规金融承诺类表述
3. 输出为简体标题候选列表

### 参考风格

- 短期见底没
- 反弹后再跌
- 关注82阻力
- Y浪尾声
- 等待反弹
- 多头抵抗增强
- 空头动能衰竭
- 关注B浪反弹

### 禁止词汇

**禁止使用**：暴涨、暴跌、起飞、机会、必看、震惊、一定、稳赚
**禁止使用**：感叹号、表情符号、营销词汇

## 人工审核 + 可编辑流程

### 审核步骤

1. Skill 暂停，等待人工操作
2. 人工可执行两种操作之一：
   - 从 3 个候选标题中选择 1 个
   - 输入自定义标题（4-6个字）
3. 人工修改规则：
   - 字数不得超过 6 个字
   - 不得脱离原字幕语义
   - 不得引入营销、情绪化或夸大表述
4. 最终确认 1 个「简体最终标题」

### 强制要求

**未完成此步骤，不得继续生成封面。**

## 简繁处理规则

1. 仅对「最终确认的简体标题」进行繁体转换
2. 繁体标题仅用于生成繁体封面
3. 简体与繁体封面：
   - 使用同一张背景图
   - 仅标题文字不同

### 简繁转换映射

内置币圈专用转换规则：
- 比特币 → 比特幣
- 机会 → 機會
- 买 → 買
- 卖 → 賣
- 图 → 圖
- 线 → 線
- 等...

## 标题文字绘制规则

### 位置

画面中部偏左（与模板一致）
- 水平位置：左侧 15%
- 垂直位置：居中

### 字体与风格

- 干净、专业、金融风格
- 中文字体优先级：苹方 → 黑体 → 正黑 → 微软雅黑

### 字号与颜色

- 5字：140px
- 6字：120px
- 白色文字
- 轻微阴影（黑色半透明，偏移4px）

### 布局

不自动换行，整体居中展示

## 输出文件

### 文件位置

`/Users/ai/Documents/video_pipeline/3daily/covers/`

### 文件命名

- `cover_YYYYMMDD_simplified.png` - 简体封面
- `cover_YYYYMMDD_traditional.png` - 繁体封面

### 命名示例

- `cover_20260208_simplified.png`
- `cover_20260208_traditional.png`

## 环境变量

在 `.env` 文件中设置 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your_api_key_here
```

## 边界说明

**本 Skill 做**：
- 读取字幕文稿
- 调用 DeepSeek 生成标题候选
- 强制等待人工审核选择
- 从 assets 选择已存在的背景图
- 在背景图上叠加标题文字
- 按颜色轮换或人工指定选择背景
- 生成简体 + 繁体双版本封面

**不做**：
- 生成背景图
- 修改背景颜色、布局、元素
- 调整 Logo、固定文案位置
- 调用文生图 API
- 自动跳过人工审核

## 依赖

- Python 3
- Pillow（图像处理库）
- DeepSeek API

### 安装依赖

```bash
pip3 install Pillow
```

## 背景图准备

首次使用前，请确保将以下背景图放置到 `assets` 目录：

```
/Users/ai/.claude/skills/generate-cover-v2/assets/
├── background_green.png   # 绿色背景（看涨）
├── background_red.png     # 红色背景（看跌）
├── background_blue.png    # 蓝色背景（中性）
└── background_yellow.png  # 黄色背景（警示）
```

**建议尺寸**：1280 × 720（标准 YouTube 16:9）

---

## 错误反省记录

### 2026-03-11：`--title` 参数格式错误

**错误场景**：
用户要求生成标题为"反抽加空单"的封面。

**错误操作**：
```bash
python generate_cover.py --auto --title "反抽加空单"
```

**问题原因**：
- 脚本只识别 `--title=xxx` 格式（等号连接）
- `--title "xxx"` 格式会被解析为两个独立参数，导致标题被忽略
- 结果：脚本使用了 AI 生成的标题而非用户指定的标题

**正确操作**：
```bash
python generate_cover.py --auto --title="反抽加空单"
```

**教训**：
1. 传递用户指定标题时，必须使用 `--title=标题` 格式（等号，无空格）
2. 执行后检查输出中的 `📝 使用指定标题:` 确认标题是否被正确使用
3. 不要假设参数格式，第一次执行时验证输出是否符合预期

### 2026-03-25：DeepSeek 标题生成失败（显示系统默认标题）

**错误场景**：
封面生成时一直显示系统默认标题（"短期见底没"、"关注阻力位"、"等待反弹中"），而不是 DeepSeek AI 生成的标题。

**问题原因**：
1. DeepSeek API 正常工作，但返回的标题通常是 **6-7 个字**（如："三浪主升在即"、"结构清晰待涨"）
2. **原始解析逻辑**：只接受正好 5 个字的标题，超过 5 字的全部过滤
3. **结果**：标题列表为空，回退到系统默认备用标题
4. **空格处理 bug**：标题提取后有前导空格，`lstrip` 没有去除空格，导致字数统计错误

**修复方案**：

1. **优化 Prompt**：
   - 要求生成 **5-7 个标题候选**（增加容错）
   - 强调"**必须是完整的 5 字表述，不能截断**"
   - 提供更多正确/错误示例

2. **优化解析逻辑**：
   ```python
   # 修改前：只接受 5 字，超过 5 字会截取
   if 5 <= len(title) <= 8:
       if len(title) > 5:
           title = title[:5]  # 截取（不可取！）
       titles.append(title)

   # 修改后：只接受正好 5 字，不允许截取
   title = title.strip(' )）').strip()  # 彻底去除空格
   if len(title) == 5:
       titles_with_length.append((title, len(title)))

   # 按字数排序，选择最少的 3 个
   titles_with_length.sort(key=lambda x: x[1])
   titles = [t[0] for t in titles_with_length[:3]]
   ```

**测试结果**：
- DeepSeek 成功生成 7 个 5 字标题
- 脚本自动选择前 3 个

**教训**：
1. **不允许截取标题**：截取后表述不完整（如："结构清晰待"）
2. **生成更多候选**：从 5-7 个中挑选最好的 3 个
3. **彻底去除空格**：使用 `strip(' )）').strip()` 而不是只 `lstrip()`
4. **参考记录**：`/Users/ai/.claude/memory/cover_title_fix_20260325.md`

### 2026-03-27：用户选择标题后重新生成候选导致标题不一致

**错误场景**：
用户从显示的 3 个候选标题中选择了第 3 个"短空等新底"，但最终生成的封面使用了"小级走新跌"。

**问题原因**：
1. **原始逻辑**：用户选择后，脚本会重新调用 DeepSeek 生成新的候选列表
2. DeepSeek API 每次返回的候选都不同（AI 生成的不确定性）
3. 用户基于第一次看到的列表选择，但脚本使用第二次生成的列表
4. 结果：用户选择的标题和实际使用的标题不一致

**修复方案**：

1. **提前生成候选**：将标题候选生成移到用户选择之前
2. **锁定候选列表**：用户选择时使用已生成的候选，不再重新生成
3. **条件生成**：只在需要时生成候选（指定标题模式跳过生成）

```python
# 修改前：每次都重新生成
print("\n请选择一个标题：")
# ... 用户输入
if choice in ['1', '2', '3']:
    titles = call_deepseek_for_titles(content)  # 重新生成！
    selected_title = titles[int(choice) - 1]

# 修改后：提前生成并锁定
titles = call_deepseek_for_titles(content)  # 只生成一次
print("【标题候选】")
for i, title in enumerate(titles, 1):
    print(f"{i}. {title}")
# ... 用户输入
if choice in ['1', '2', '3']:
    selected_title = titles[int(choice) - 1]  # 使用已生成的列表
```

**测试结果**：
- 用户看到的候选和实际使用的候选完全一致
- 避免了因重新生成导致的混乱

**教训**：
1. **用户交互前生成**：候选内容必须在用户看到前生成并锁定
2. **避免重复调用 AI**：AI 生成具有不确定性，不要重复调用
3. **明确反馈**：生成后立即显示，用户选择直接使用
4. **参考记录**：`/Users/ai/.claude/memory/cover_selection_fix_20260327.md`
