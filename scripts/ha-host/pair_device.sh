#!/bin/bash

# VCX-Knob 蓝牙配对脚本
# 使用方法:
# 1. 修改 DEVICE_MAC 为你的设备 MAC 地址（或留空自动发现）
# 2. chmod +x pair_device.sh
# 3. ./pair_device.sh

DEVICE_MAC=""  # 留空自动发现，或填写你的设备 MAC 地址
SCAN_TIMEOUT=10  # 扫描超时（秒）

echo "=========================================="
echo "  VCX-Knob 蓝牙配对工具"
echo "=========================================="
echo ""

# 检查 bluetoothctl 是否可用
if ! command -v bluetoothctl &> /dev/null; then
    echo "❌ 错误: bluetoothctl 未安装"
    echo "请安装: apt-get install bluez"
    exit 1
fi

# 如果未指定 MAC 地址，自动扫描发现
if [ -z "$DEVICE_MAC" ]; then
    echo "步骤 1/5: 扫描设备..."
    echo "正在扫描附近的 VCX-Knob 设备（${SCAN_TIMEOUT} 秒）..."
    echo ""

    # 启动扫描
    bluetoothctl scan on &
    SCAN_PID=$!

    # 等待扫描完成
    sleep $SCAN_TIMEOUT

    # 停止扫描
    kill $SCAN_PID 2>/dev/null
    bluetoothctl scan off > /dev/null 2>&1

    echo ""
    echo "步骤 2/5: 查找设备..."
    echo ""

    # 查找设备
    FOUND_DEVICE=$(bluetoothctl devices | grep -i "VCX-Knob" | head -1)

    if [ -z "$FOUND_DEVICE" ]; then
        echo "❌ 错误: 未找到 VCX-Knob 设备"
        echo ""
        echo "所有发现的设备:"
        bluetoothctl devices
        exit 1
    fi

    echo "找到设备: $FOUND_DEVICE"
    DEVICE_MAC=$(echo "$FOUND_DEVICE" | awk '{print $2}')
else
    echo "使用预设 MAC 地址: $DEVICE_MAC"
    echo ""
fi

echo "使用 MAC 地址: $DEVICE_MAC"
echo ""

echo "步骤 3/5: 配对设备..."
echo "请在设备上确认配对（如果有配对按钮，请按下）"
echo ""

# 配对设备
PAIR_OUTPUT=$(timeout 20 bluetoothctl pair $DEVICE_MAC 2>&1)
echo "$PAIR_OUTPUT" | grep -v "^$" | grep -v "Agent registered"

# 检查配对是否成功
if echo "$PAIR_OUTPUT" | grep -q "Pairing successful"; then
    echo "✓ 配对成功！"
elif echo "$PAIR_OUTPUT" | grep -q "Already paired"; then
    echo "✓ 设备已配对"
elif echo "$PAIR_OUTPUT" | grep -q "Failed to pair"; then
    echo "❌ 配对失败"
    echo ""
    echo "可能的原因:"
    echo "  1. 设备距离太远（请靠近到 1 米以内）"
    echo "  2. 设备未在配对模式（查看设备说明书）"
    echo "  3. 需要在设备上确认配对"
    echo ""
    echo "建议: 尝试使用手机蓝牙配对（最简单的方法）"
    exit 1
else
    echo "配对状态未知，继续..."
fi
echo ""

echo "步骤 4/5: 信任设备..."

# 信任设备
TRUST_OUTPUT=$(bluetoothctl trust $DEVICE_MAC 2>&1)
if echo "$TRUST_OUTPUT" | grep -q "trust succeeded"; then
    echo "✓ 信任成功"
else
    echo "信任状态未知，继续..."
fi
echo ""

echo "步骤 5/5: 验证配对..."
echo ""

# 查看设备信息
INFO_OUTPUT=$(bluetoothctl info $DEVICE_MAC 2>&1)

# 检查配对状态
if echo "$INFO_OUTPUT" | grep -q "Paired: yes"; then
    PAIRED="✅ 是"
else
    PAIRED="❌ 否"
fi

if echo "$INFO_OUTPUT" | grep -q "Trusted: yes"; then
    TRUSTED="✅ 是"
else
    TRUSTED="❌ 否"
fi

if echo "$INFO_OUTPUT" | grep -q "Connected: yes"; then
    CONNECTED="✅ 是"
else
    CONNECTED="❌ 否"
fi

echo "配对状态: $PAIRED"
echo "信任状态: $TRUSTED"
echo "连接状态: $CONNECTED"
echo ""

if echo "$INFO_OUTPUT" | grep -q "Paired: yes"; then
    echo "=========================================="
    echo "  ✓ 配对成功！"
    echo "=========================================="
    echo ""
    echo "现在你可以在 Home Assistant 中:"
    echo "1. 删除现有的 VCX-Knob 集成（如果有）"
    echo "2. 重新添加 VCX-Knob 集成"
    echo "3. 按钮应该可以正常工作了"
else
    echo "=========================================="
    echo "  ✗ 配对失败"
    echo "=========================================="
    echo ""
    echo "尝试以下方法:"
    echo ""
    echo "方法 1: 使用手机配对（最简单）"
    echo "  1. 打开手机蓝牙"
    echo "  2. 找到 VCX-Knob 设备"
    echo "  3. 点击配对"
    echo "  4. 完成！"
    echo ""
    echo "方法 2: 手动配对"
    echo "  bluetoothctl"
    echo "  pair $DEVICE_MAC"
    echo "  # 在设备上确认配对"
    echo "  trust $DEVICE_MAC"
    echo "  info $DEVICE_MAC"
    echo "  quit"
fi
