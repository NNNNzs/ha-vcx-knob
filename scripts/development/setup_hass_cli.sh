#!/bin/bash

# hass-cli 配置脚本
# 用于在 NAS 本地环境配置 Home Assistant CLI

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=== Home Assistant CLI 配置向导 ===${NC}"
echo ""

# 检测 hass-cli 是否已安装
if ! command -v hass-cli &> /dev/null; then
    echo -e "${RED}✗ hass-cli 未安装${NC}"
    echo "请先安装: pip install homeassistant-cli"
    exit 1
fi

echo -e "${YELLOW}请输入以下信息:${NC}"

# 获取 HA URL
read -p "Home Assistant URL (默认: http://localhost:8123): " HA_URL
HA_URL=${HA_URL:-http://localhost:8123}

# 获取 Token
echo ""
echo -e "${YELLOW}获取长期访问令牌:${NC}"
echo "1. 打开浏览器访问: ${HA_URL}"
echo "2. 点击左下角用户头像 → 滚动到底部 → '创建令牌'"
echo "3. 输入令牌名称 (如: hass-cli-dev)"
echo "4. 复制生成的令牌"
echo ""
read -p "请粘贴令牌: " HA_TOKEN

# 验证令牌
echo ""
echo -e "${YELLOW}验证连接...${NC}"
export HASS_SERVER="${HA_URL}"
export HASS_TOKEN="${HA_TOKEN}"

if hass-cli info &> /dev/null; then
    echo -e "${GREEN}✓ 连接成功！${NC}"

    # 保存配置
    echo ""
    echo -e "${YELLOW}保存配置到 ~/.config/hass-cli/config.json ...${NC}"
    mkdir -p ~/.config/hass-cli
    cat > ~/.config/hass-cli/config.json <<EOF
{
  "server": "${HA_URL}",
  "token": "${HA_TOKEN}"
}
EOF

    echo -e "${GREEN}✓ 配置已保存${NC}"
    echo ""
    echo "测试命令:"
    echo "  hass-cli info              # 查看 HA 信息"
    echo "  hass-cli entity list       # 列出所有实体"
    echo "  hass-cli service call --help  # 查看服务调用帮助"
else
    echo -e "${RED}✗ 连接失败，请检查 URL 和令牌是否正确${NC}"
    exit 1
fi
