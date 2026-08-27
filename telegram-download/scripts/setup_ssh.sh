#!/bin/bash
#
# 配置 SSH 自动化 - 设置密钥认证
#
# 用法:
#   ./setup_ssh.sh
#

set -e

# ====== 配置 ======
SERVER="root@43.167.173.8"
SSH_KEY_PATH="$HOME/.ssh/id_ed25519"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "SSH 自动化配置"
echo "=========================================="
echo ""

# 1. 检查本地是否有 SSH 密钥
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}本地 SSH 密钥不存在，正在生成...${NC}"
    ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N ""
    echo -e "${GREEN}✅ SSH 密钥已生成${NC}"
else
    echo -e "${GREEN}✅ 本地 SSH 密钥已存在${NC}"
fi

# 2. 显示公钥
echo ""
echo "=========================================="
echo -e "${GREEN}步骤 1: 将以下公钥添加到服务器${NC}"
echo "=========================================="
echo ""
cat "${SSH_KEY_PATH}.pub"
echo ""
echo "=========================================="
echo ""

# 3. 提供命令
echo -e "${YELLOW}请在服务器上执行以下命令：${NC}"
echo ""
echo "  # 方式 1: 使用 echo 命令"
echo "  echo \"$(cat ${SSH_KEY_PATH}.pub)\" >> ~/.ssh/authorized_keys"
echo ""
echo "  # 方式 2: 使用 ssh-copy-id（如果服务器支持）"
echo "  ssh-copy-id -i ${SSH_KEY_PATH}.pub ${SERVER}"
echo ""
echo "=========================================="
echo ""

# 4. 等待用户确认
echo -e "${YELLOW}完成上述操作后，按回车键继续...${NC}"
read -r

# 5. 测试连接
echo ""
echo "=========================================="
echo -e "${GREEN}步骤 2: 测试 SSH 连接${NC}"
echo "=========================================="
echo ""

if ssh -o BatchMode=yes -o ConnectTimeout=10 "$SERVER" "echo '连接成功！'"; then
    echo ""
    echo -e "${GREEN}✅ SSH 自动化配置成功！${NC}"
    echo ""
    echo "现在可以使用 sync_videos.sh 脚本自动同步视频了。"
else
    echo ""
    echo -e "${RED}❌ SSH 连接失败${NC}"
    echo ""
    echo "可能的原因："
    echo "  1. 公钥未正确添加到服务器"
    echo "  2. ~/.ssh/authorized_keys 文件权限不正确（应该是 600）"
    echo "  3. SSH 服务器配置不允许密钥认证"
    echo ""
    echo "请检查以上问题后重试。"
    exit 1
fi
