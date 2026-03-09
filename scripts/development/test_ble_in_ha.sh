#!/bin/bash

# 在 Home Assistant 容器内测试蓝牙扫描

echo "========================================"
echo "蓝牙扫描测试"
echo "========================================"
echo ""

ssh root@192.168.1.80 << 'EOF'
# 检查蓝牙适配器状态
echo "1. 检查蓝牙适配器:"
docker exec homeassistant hciconfig -a | head -5

# 检查最近的蓝牙日志
echo ""
echo "2. 最近的蓝牙相关日志:"
docker logs homeassistant --tail 200 2>&1 | grep -i "bluetooth\|ble" | tail -10

# 检查是否有蓝牙设备被发现
echo ""
echo "3. 检查 Home Assistant 内部蓝牙状态:"
docker exec homeassistant python3 -c "
import sys
import logging
logging.basicConfig(level=logging.INFO)

try:
    from homeassistant.components import bluetooth
    from homeassistant.components.bluetooth import (
        async_get_scanner,
        BluetoothScanningMode,
    )
    print('✓ 蓝牙模块导入成功')
    print(f'  BluetoothScanningMode.ACTIVE = {BluetoothScanningMode.ACTIVE}')
    print(f'  BluetoothScanningMode.PASSIVE = {BluetoothScanningMode.PASSIVE}')
except Exception as e:
    print(f'✗ 蓝牙模块导入失败: {e}')
" 2>&1

EOF

echo ""
echo "========================================"
echo "测试完成"
echo "========================================"
echo ""
echo "下一步："
echo "1. 确保 VCX-Knob 设备已开机并在范围内"
echo "2. 在 HA 中添加集成：设置 → 设备与服务 → 添加集成 → VCX-Knob"
echo "3. 如果扫描失败，检查设置 → 系统 → 日志中的详细错误"
