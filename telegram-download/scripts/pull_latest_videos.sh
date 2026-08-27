#!/bin/bash
set -euo pipefail

SERVER_IP="${TG_VIDEO_SERVER_IP:-43.167.173.8}"
SERVER_USER="${TG_VIDEO_SERVER_USER:-root}"
REMOTE_DIR="${TG_VIDEO_REMOTE_DIR:-/root/videos}"
LOCAL_DIR="${1:-${TG_VIDEO_LOCAL_DIR:-/Users/ai/Documents/video_downloads}}"
PASSWORD="${TG_VIDEO_SERVER_PASSWORD:-}"

if ! command -v expect >/dev/null 2>&1; then
  echo "expect is required but not installed."
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but not installed."
  exit 1
fi

mkdir -p "$LOCAL_DIR"

if [[ -z "$PASSWORD" ]]; then
  read -r -s -p "Server password: " PASSWORD
  echo
fi

export TG_VIDEO_SERVER_PASSWORD="$PASSWORD"
export TG_VIDEO_SERVER_IP="$SERVER_IP"
export TG_VIDEO_SERVER_USER="$SERVER_USER"
export TG_VIDEO_REMOTE_DIR="$REMOTE_DIR"
export TG_VIDEO_LOCAL_DIR="$LOCAL_DIR"

echo "Starting manual video sync..."
echo "Remote: ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/"
echo "Local:  ${LOCAL_DIR}/"

expect <<'EOF'
set timeout -1
set password $env(TG_VIDEO_SERVER_PASSWORD)
set server_ip $env(TG_VIDEO_SERVER_IP)
set server_user $env(TG_VIDEO_SERVER_USER)
set remote_dir $env(TG_VIDEO_REMOTE_DIR)
set local_dir $env(TG_VIDEO_LOCAL_DIR)

spawn rsync -av --ignore-existing --partial --info=progress2 --include=*/ --include=*.mp4 --exclude=* -e {ssh -o StrictHostKeyChecking=no} ${server_user}@${server_ip}:${remote_dir}/ ${local_dir}/

expect {
  -re "Are you sure you want to continue connecting \\(yes/no(/\\[fingerprint\\])?\\)\\?" {
    send "yes\r"
    exp_continue
  }
  -re ".*password:.*" {
    send "$password\r"
    exp_continue
  }
  eof
}
EOF

echo "Manual video sync finished."
