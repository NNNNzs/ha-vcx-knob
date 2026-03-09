#!/bin/bash

# Home Assistant 调试脚本
# 用于测试集成配置和蓝牙连接

HA_HOST="192.168.1.80"
HA_USER="root"
HA_CONFIG_DIR="/root/docker_v/homeassistant/config"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Home Assistant 调试工具"
echo "=========================================="
echo ""

# 1. 检查连接
echo -e "${YELLOW}[1/6] 检查服务器连接...${NC}"
if ssh -o ConnectTimeout=5 ${HA_USER}@${HA_HOST} "echo '连接成功'" 2>&1 | grep -q "连接成功"; then
    echo -e "${GREEN}✓ 服务器连接正常${NC}"
else
    echo -e "${RED}✗ 无法连接到服务器${NC}"
    exit 1
fi

# 2. 检查容器状态
echo -e "${YELLOW}[2/6] 检查 Home Assistant 容器...${NC}"
if ssh ${HA_USER}@${HA_HOST} "docker inspect homeassistant >/dev/null 2>&1 && docker ps | grep -q homeassistant"; then
    echo -e "${GREEN}✓ Home Assistant 容器正在运行${NC}"
else
    echo -e "${RED}✗ Home Assistant 容器未运行${NC}"
    exit 1
fi

# 3. 检查蓝牙设备
echo -e "${YELLOW}[3/6] 检查蓝牙适配器...${NC}"
BLE_INFO=$(ssh ${HA_USER}@${HA_HOST} "docker exec homeassistant hciconfig -a 2>&1" | head -3)
if echo "$BLE_INFO" | grep -q "UP RUNNING"; then
    echo -e "${GREEN}✓ 蓝牙适配器正常运行${NC}"
    echo "$BLE_INFO" | head -2
else
    echo -e "${RED}✗ 蓝牙适配器未运行${NC}"
    echo "$BLE_INFO"
fi

# 4. 检查集成文件
echo -e "${YELLOW}[4/6] 检查 VCX-Knob 集成文件...${NC}"
FILE_COUNT=$(ssh ${HA_USER}@${HA_HOST} "ls -1 ${HA_CONFIG_DIR}/custom_components/vcx_knob/*.py 2>/dev/null | wc -l")
if [ "$FILE_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✓ 集成文件完整 (${FILE_COUNT} 个 Python 文件)${NC}"
else
    echo -e "${RED}✗ 集成文件不完整 (只有 ${FILE_COUNT} 个文件)${NC}"
fi

# 5. 测试模块导入
echo -e "${YELLOW}[5/6] 测试 Python 模块导入...${NC}"
IMPORT_RESULT=$(ssh ${HA_USER}@${HA_HOST} "docker exec homeassistant python -c 'import sys; sys.path.insert(0, \"/config\"); from custom_components.vcx_knob import const, config_flow, coordinator; print(\"OK\")' 2>&1")
if echo "$IMPORT_RESULT" | grep -q "OK"; then
    echo -e "${GREEN}✓ 模块导入成功${NC}"
else
    echo -e "${RED}✗ 模块导入失败${NC}"
    echo "$IMPORT_RESULT" | tail -5
fi

# 6. 查看最新日志
echo -e "${YELLOW}[6/6] 查看 VCX-Knob 相关日志...${NC}"
echo "最近的错误日志:"
ssh ${HA_USER}@${HA_HOST} "docker logs homeassistant --tail 100 2>&1 | grep -i 'vcx_knob\|scan_failed' | tail -5"

echo ""
echo "=========================================="
echo "  调试完成"
echo "=========================================="
echo ""
echo "常用命令:"
echo "  查看实时日志: ssh ${HA_USER}@${HA_HOST} 'docker logs -f homeassistant'"
echo "  重启 HA:      ssh ${HA_USER}@${HA_HOST} 'docker restart homeassistant'"
echo "  进入容器:     ssh ${HA_USER}@${HA_HOST} 'docker exec -it homeassistant /bin/bash'"
echo "  同步文件:     bash /Users/nnnnzs/project/ha-vcx-knob/sync_to_ha.sh"
echo ""
