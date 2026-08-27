#!/bin/bash
#
# 火山引擎语音识别（异步模式）+ uguu.se 上传
#
# 用法: ./volcengine_api.sh <audio_file>
# 输出: volcengine_result.json
#

set -e

AUDIO_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
OUTPUT_JSON="volcengine_result.json"

# 检查输入
if [ -z "$AUDIO_FILE" ]; then
  echo "❌ 用法: $0 <audio_file>"
  exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
  echo "❌ 音频文件不存在: $AUDIO_FILE"
  exit 1
fi

# 读取 API Key
if [ -f "$ENV_FILE" ]; then
  API_KEY=$(grep "^VOLCENGINE_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
else
  echo "❌ 找不到 .env 文件: $ENV_FILE"
  exit 1
fi

if [ -z "$API_KEY" ] || [ "$API_KEY" = "your_api_key_here" ]; then
  echo "❌ 请在 .env 文件中设置正确的 VOLCENGINE_API_KEY"
  exit 1
fi

echo "🎤 音频文件: $AUDIO_FILE"
echo "📤 正在上传到 uguu.se..."

# 上传到 uguu.se
UPLOAD_RESPONSE=$(curl -s -F "files[]=@${AUDIO_FILE}" https://uguu.se/upload)

# 提取 URL（使用 Python 解析 JSON）
AUDIO_URL=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['files'][0]['url'].replace('\\\\/', '/'))" 2>/dev/null)

if [ -z "$AUDIO_URL" ]; then
  echo "❌ 上传失败，响应: $UPLOAD_RESPONSE"
  exit 1
fi

echo "✅ 上传成功: $AUDIO_URL"
echo "🎙️ 提交火山引擎转录任务..."

# 步骤1: 提交任务
SUBMIT_RESPONSE=$(curl -s -L -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?language=zh-CN&use_itn=True&use_capitalize=True&max_lines=1&words_per_line=15" \
  -H "Accept: */*" \
  -H "x-api-key: $API_KEY" \
  -H "Connection: keep-alive" \
  -H "content-type: application/json" \
  -d "{\"url\": \"$AUDIO_URL\"}")

# 提取任务 ID
TASK_ID=$(echo "$SUBMIT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
  echo "❌ 提交失败，响应:"
  echo "$SUBMIT_RESPONSE"
  exit 1
fi

echo "✅ 任务已提交，ID: $TASK_ID"
echo "⏳ 等待转录完成..."

# 步骤2: 轮询结果
MAX_ATTEMPTS=120  # 最多等待 10 分钟（每 5 秒查一次）
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 5
  ATTEMPT=$((ATTEMPT + 1))

  QUERY_RESPONSE=$(curl -s -L -X GET "https://openspeech.bytedance.com/api/v1/vc/query?id=$TASK_ID" \
    -H "Accept: */*" \
    -H "x-api-key: $API_KEY" \
    -H "Connection: keep-alive")

  # 检查状态
  STATUS=$(echo "$QUERY_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | cut -d':' -f2)

  if [ "$STATUS" = "0" ]; then
    # 成功完成
    echo "$QUERY_RESPONSE" > "$OUTPUT_JSON"
    echo "✅ 转录完成，已保存 $OUTPUT_JSON"

    # 显示统计
    UTTERANCES=$(echo "$QUERY_RESPONSE" | grep -o '"text"' | wc -l | tr -d ' ')
    echo "📝 识别到 $UTTERANCES 段语音"
    exit 0
  elif [ "$STATUS" = "1000" ]; then
    # 处理中
    echo -n "."
  else
    # 其他错误
    echo ""
    echo "❌ 转录失败，响应:"
    echo "$QUERY_RESPONSE"
    exit 1
  fi
done

echo ""
echo "❌ 超时，任务未完成"
exit 1
