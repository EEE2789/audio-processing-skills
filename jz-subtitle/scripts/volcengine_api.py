#!/usr/bin/env python3
"""
火山引擎语音识别 + uguu.se 上传

用法: python volcengine_api.py <audio_file>
输出: volcengine_result.json
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"
OUTPUT_JSON = "volcengine_result.json"

def load_api_key():
    """从 .env 文件加载 API Key"""
    if not ENV_FILE.exists():
        # 尝试父目录的 .env
        ENV_FILE_PARENT = SCRIPT_DIR.parent / ".env"
        if ENV_FILE_PARENT.exists():
            with open(ENV_FILE_PARENT) as f:
                for line in f:
                    if line.startswith("VOLCENGINE_API_KEY="):
                        return line.split("=", 1)[1].strip()
        raise RuntimeError(f"❌ 找不到 .env 文件: {ENV_FILE}")

    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("VOLCENGINE_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                if api_key and api_key != "your_api_key_here":
                    return api_key
    raise RuntimeError("❌ 请在 .env 文件中设置正确的 VOLCENGINE_API_KEY")

def upload_to_uguu(audio_file):
    """上传音频文件到 uguu.se"""
    print(f"🎤 音频文件: {audio_file}")
    print("📤 正在上传到 uguu.se...")

    cmd = [
        "curl", "-s", "-F", f"files[]=@{audio_file}",
        "https://uguu.se/upload"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    response = result.stdout

    try:
        data = json.loads(response)
        if data.get("success") and data.get("files"):
            url = data["files"][0]["url"]
            # 移除转义斜杠
            url = url.replace("\\/", "/")
            print(f"✅ 上传成功: {url}")
            return url
        else:
            raise RuntimeError(f"上传失败: {response}")
    except json.JSONDecodeError:
        raise RuntimeError(f"上传响应解析失败: {response}")

def submit_volcengine_task(audio_url, api_key):
    """提交火山引擎转录任务"""
    print("🎙️ 提交火山引擎转录任务...")

    cmd = [
        "curl", "-s", "-L", "-X", "POST",
        "https://openspeech.bytedance.com/api/v1/vc/submit?language=zh-CN&use_itn=True&use_capitalize=True&max_lines=1&words_per_line=15",
        "-H", "Accept: */*",
        "-H", f"x-api-key: {api_key}",
        "-H", "Connection: keep-alive",
        "-H", "content-type: application/json",
        "-d", json.dumps({"url": audio_url})
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    response = result.stdout

    try:
        data = json.loads(response)
        task_id = data.get("id")
        if not task_id:
            raise RuntimeError(f"提交失败: {response}")
        print(f"✅ 任务已提交，ID: {task_id}")
        return task_id
    except json.JSONDecodeError:
        raise RuntimeError(f"提交响应解析失败: {response}")

def poll_volcengine_result(task_id, api_key, max_attempts=120, interval=5):
    """轮询火山引擎转录结果"""
    print("⏳ 等待转录完成...")

    for attempt in range(max_attempts):
        time.sleep(interval)

        cmd = [
            "curl", "-s", "-L", "-X", "GET",
            f"https://openspeech.bytedance.com/api/v1/vc/query?id={task_id}",
            "-H", "Accept: */*",
            "-H", f"x-api-key: {api_key}",
            "-H", "Connection: keep-alive"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        response = result.stdout

        try:
            data = json.loads(response)
            code = data.get("code")

            if code == 0:
                # 成功完成
                with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 转录完成，已保存 {OUTPUT_JSON}")

                # 统计语音段数
                utterances = data.get("result", {}).get("utterances", [])
                print(f"📝 识别到 {len(utterances)} 段语音")
                return True
            elif code == 1000:
                # 处理中
                print(".", end="", flush=True)
            else:
                # 其他错误
                print(f"\n❌ 转录失败，响应: {response}")
                return False
        except json.JSONDecodeError:
            print(f"\n❌ 响应解析失败: {response}")
            return False

    print("\n❌ 超时，任务未完成")
    return False

def main():
    if len(sys.argv) < 2:
        print("❌ 用法: python volcengine_api.py <audio_file>")
        sys.exit(1)

    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"❌ 音频文件不存在: {audio_file}")
        sys.exit(1)

    try:
        # 1. 加载 API Key
        api_key = load_api_key()

        # 2. 上传到 uguu.se
        audio_url = upload_to_uguu(audio_file)

        # 3. 提交火山引擎任务
        task_id = submit_volcengine_task(audio_url, api_key)

        # 4. 轮询结果
        success = poll_volcengine_result(task_id, api_key)

        sys.exit(0 if success else 1)

    except RuntimeError as e:
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
