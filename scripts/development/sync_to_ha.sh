#!/bin/bash

# 本地同步脚本到 Home Assistant
# 适用于 NAS 本地 Docker 部署场景

set -e

HA_CONFIG_DIR="/vol2/1000/docker_v/homeassistant/config"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SOURCE_DIR="${PROJECT_ROOT}/custom_components/vcx_knob"
TARGET_DIR="${HA_CONFIG_DIR}/custom_components/vcx_knob"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}正在同步 VCX-Knob 集成到 Home Assistant...${NC}"
echo "源目录: ${SOURCE_DIR}"
echo "目标目录: ${TARGET_DIR}"
echo ""

# 确保目标目录存在
mkdir -p "${TARGET_DIR}"

# 同步文件
cp -rf "${SOURCE_DIR}/"* "${TARGET_DIR}/"

echo -e "${GREEN}✓ 同步完成！${NC}"
echo ""
echo "接下来："
echo "  1. 清除 Python 缓存:"
echo "     docker exec homeassistant find /config/custom_components/vcx_knob -name '*.pyc' -delete"
echo ""
echo "  2. 重启 Home Assistant:"
echo "     docker restart homeassistant"
echo ""
echo "  或使用便捷命令:"
echo "     ./scripts/development/restart_ha.sh"
