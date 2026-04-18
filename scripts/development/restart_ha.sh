#!/bin/bash

# 重启 Home Assistant 并清理缓存

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[1/3] 清除 Python 缓存...${NC}"
docker exec homeassistant find /config/custom_components/vcx_knob -name "*.pyc" -delete 2>/dev/null || true
docker exec homeassistant find /config/custom_components/vcx_knob -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓ 缓存已清除${NC}"

echo -e "${YELLOW}[2/3] 重启 Home Assistant...${NC}"
docker restart homeassistant
echo -e "${GREEN}✓ 重启命令已发送${NC}"

echo -e "${YELLOW}[3/3] 等待 Home Assistant 启动...${NC}"
echo "（此过程可能需要 1-2 分钟，请稍候...）"
echo ""
echo "启动完成后，可以通过以下方式检查状态："
echo "  - 浏览器访问: http://<NAS_IP>:8123"
echo "  - 查看日志: docker logs -f homeassistant"
echo "  - 运行状态检查: ./scripts/development/ha_test.sh"
