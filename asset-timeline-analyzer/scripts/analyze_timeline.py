#!/usr/bin/env python3
"""
资产时间轴分析器
基于视频字幕文件（SRT）分析所有资产的时间轴
"""

import os
import sys
import json
import requests
import re
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def read_srt_file(file_path):
    """读取 SRT 字幕文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

def call_deepseek(srt_content):
    """调用 DeepSeek API 分析资产时间轴（基于 SRT 字幕时间戳）"""

    prompt = f'''你是一个专业的币圈和美股行情分析师。请分析以下视频字幕文件（SRT格式），提取所有提到的资产（比特币、以太坊、山寨币、美股等）及其在视频中出现的**具体时间点**。

**字幕内容**：
```
{srt_content}
```

**请按以下 JSON 格式输出分析结果**（不要有其他内容）：

{{
  "asset_timeline": [
    {{
      "time": "字幕时间戳（如 00:00:30,000 --> 00:00:35,000）",
      "time_seconds": "时间秒数（如 30.5）",
      "asset": "资产名称（如比特币、以太坊）",
      "content": "该时间点提到的内容摘要",
      "operation": "操作类型（如分析、价格、建议、买入、卖出、观望等）",
      "price": "提到的价格（如有）"
    }}
  ],
  "summary": {{
    "btc_count": "比特币提及次数",
    "eth_count": "以太坊提及次数",
    "other_count": "其他资产提及次数"
  }}
}}

**分析要求**：
1. 遍历所有字幕行，提取涉及资产的片段
2. 保留**准确的 SRT 时间戳**
3. 记录每个时间点讨论的资产和内容
4. 输出必须是纯 JSON 格式，不要有任何其他文字
'''

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()

        # 提取回复内容
        content = result["choices"][0]["message"]["content"]

        # 尝试解析 JSON
        try:
            # 去除可能的 markdown 代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ DeepSeek 返回的不是有效 JSON: {e}")
            print(f"原始内容: {content}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ DeepSeek API 调用失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def generate_markdown_report(analysis):
    """生成 Markdown 格式的分析报告（按资产分组）"""

    md_lines = []
    md_lines.append("# 📊 资产时间轴分析")
    md_lines.append("")
    md_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append("")

    # 统计信息
    if analysis.get("summary"):
        summary = analysis["summary"]
        md_lines.append("## 📋 提及统计")
        md_lines.append("")
        md_lines.append(f"- 比特币: {summary.get('btc_count', '0')} 次")
        md_lines.append(f"- 以太坊: {summary.get('eth_count', '0')} 次")
        md_lines.append(f"- 其他资产: {summary.get('other_count', '0')} 次")
        md_lines.append("")

    # 按资产分组时间轴
    md_lines.append("## 🎬 资产时间轴")
    md_lines.append("")

    # 按资产分组
    asset_groups = {}
    for item in analysis.get("asset_timeline", []):
        asset = item.get("asset", "未知")
        if asset not in asset_groups:
            asset_groups[asset] = []
        asset_groups[asset].append(item)

    for asset_name, items in asset_groups.items():
        md_lines.append(f"### {asset_name}")
        md_lines.append("")
        md_lines.append("| 时间点 | 时间(秒) | 内容摘要 | 操作 | 价格 |")
        md_lines.append("|--------|----------|----------|------|------|")

        for item in items:
            time = item.get("time", "-")
            time_sec = item.get("time_seconds", "-")
            content = item.get("content", "-")[:40] if item.get("content") else "-"
            operation = item.get("operation", "-")
            price = item.get("price", "-")

            md_lines.append(f"| {time} | {time_sec} | {content} | {operation} | {price} |")

        md_lines.append("")

    return "\n".join(md_lines)

def save_report(markdown_content, output_path):
    """保存报告到文件"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✅ 报告已保存: {output_path}")
    except Exception as e:
        print(f"⚠️  保存报告失败: {e}")

def main():
    # 获取字幕文件路径
    if len(sys.argv) > 1:
        srt_path = sys.argv[1]
    else:
        # 默认读取最新的简体 SRT 文件
        srt_dir = "/Users/ai/Documents/video_pipeline/3daily"
        srt_files = [f for f in os.listdir(srt_dir) if f.startswith("简体") and f.endswith(".srt") and "bak" not in f.lower()]
        if srt_files:
            srt_files.sort(key=lambda x: os.path.getmtime(os.path.join(srt_dir, x)), reverse=True)
            srt_path = os.path.join(srt_dir, srt_files[0])
        else:
            print("❌ 找不到简体 SRT 文件")
            sys.exit(1)

    print(f"📂 读取字幕: {srt_path}")

    # 读取字幕
    srt_content = read_srt_file(srt_path)
    print(f"📝 字幕长度: {len(srt_content)} 字符")

    # 调用 DeepSeek 分析
    print("🤖 正在分析资产时间轴...")
    analysis = call_deepseek(srt_content)

    if not analysis:
        print("❌ 分析失败")
        sys.exit(1)

    timeline_count = len(analysis.get("asset_timeline", []))
    print(f"✅ 分析完成，发现 {timeline_count} 个时间点")

    # 生成报告
    print("📊 生成分析报告...")
    markdown_report = generate_markdown_report(analysis)

    # 显示报告
    print("\n" + "="*80)
    print(markdown_report)
    print("="*80 + "\n")

    # 保存报告
    output_dir = "/Users/ai/Documents/video_pipeline/3daily"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{output_dir}/资产时间轴分析_{timestamp}.md"
    save_report(markdown_report, output_path)

    print("✅ 分析完成")

if __name__ == "__main__":
    main()
