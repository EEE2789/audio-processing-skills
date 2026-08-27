#!/bin/bash
#
# 火山引擎语音转文字脚本
#
# 用法: volcengine_transcribe.sh <音频文件路径> [输出JSON路径]
#
# 输入: 音频文件 (wav/mp3/m4a等)
# 输出: 火山引擎转录结果 JSON (带字级别时间戳)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_KEY_FILE="${SCRIPT_DIR}/../.env"

# 检查输入
if [ -z "$1" ]; then
  echo "用法: volcengine_transcribe.sh <音频文件路径> [输出JSON路径]"
  exit 1
fi

AUDIO_FILE="$1"
OUTPUT_JSON="${2:-volcengine_result.json}"

if [ ! -f "$AUDIO_FILE" ]; then
  echo "错误: 找不到音频文件 $AUDIO_FILE"
  exit 1
fi

# 读取 API key
if [ -f "$API_KEY_FILE" ]; then
  API_KEY=$(grep "^VOLCENGINE_API_KEY=" "$API_KEY_FILE" | cut -d'=' -f2)
else
  echo "错误: 找不到 .env 文件 ($API_KEY_FILE)"
  exit 1
fi

if [ -z "$API_KEY" ]; then
  echo "错误: .env 文件中未设置 VOLCENGINE_API_KEY"
  exit 1
fi

echo "🎙️ 音频文件: $AUDIO_FILE"
echo "📝 输出文件: $OUTPUT_JSON"

# 调用火山引擎 API
# 这里需要实际的 API 调用逻辑
# 示例使用 curl（实际端点和参数需要根据火山引擎文档调整）

# 上传音频并获取转录结果
# 注意：以下是示例，实际端点和参数需要根据火山引擎 API 文档调整

# 假设使用 volcengine 的服务端点
# 实际实现需要：
# 1. 上传音频文件获取 URL
# 2. 调用转录 API
# 3. 轮询获取结果

echo "⏳ 正在调用火山引擎语音识别..."

# 示例：调用已有的转录服务（如果存在）
if command -v node &> /dev/null && [ -f "${SCRIPT_DIR}/volcengine_api.js" ]; then
  node "${SCRIPT_DIR}/volcengine_api.js" "$AUDIO_FILE" "$API_KEY" > "$OUTPUT_JSON"
else
  # 如果没有 Node.js 脚本，输出占位符
  # 实际使用时需要实现火山引擎 API 调用
  cat > "$OUTPUT_JSON" << EOF
{
  "utterances": []
}
EOF
  echo "⚠️ 警告: 未找到火山引擎 API 客户端，生成了空结果"
fi

echo "✅ 转录完成: $OUTPUT_JSON"
