#!/usr/bin/env python3
"""蓝牙扫描测试工具 - 在 Home Assistant 容器内运行"""

import asyncio
import sys
from bleak import BleakScanner
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    BluetoothChange,
    async_get_scanner,
    async_register_callback,
    BluetoothCallbackMatcher,
    BluetoothScanningMode,
)

DEVICE_NAME_FILTER = "VCX-Knob"

async def test_bluetooth_scan():
    """测试蓝牙扫描功能"""
    print("=" * 50)
    print("蓝牙扫描测试")
    print("=" * 50)

    # 1. 测试 bleak 扫描
    print("\n[1] 使用 bleak 直接扫描...")
    try:
        devices = await BleakScanner.discover(timeout=10)
        print(f"发现 {len(devices)} 个蓝牙设备:")

        vcx_devices = []
        for device in devices:
            if device.name and DEVICE_NAME_FILTER in device.name:
                vcx_devices.append(device)
                print(f"  ✓ 找到目标设备: {device.name} ({device.address}) RSSI: {device.rssi}")

        if not vcx_devices:
            print(f"  ✗ 未找到 {DEVICE_NAME_FILTER} 设备")
            print("\n所有发现的设备:")
            for device in devices[:10]:  # 只显示前10个
                name = device.name or "未知"
                print(f"    - {name} ({device.address})")
        else:
            print(f"\n总共找到 {len(vcx_devices)} 个 {DEVICE_NAME_FILTER} 设备")

    except Exception as e:
        print(f"✗ bleak 扫描失败: {e}")

    # 2. 测试 Home Assistant 蓝牙 API
    print("\n[2] 使用 Home Assistant 蓝牙 API...")
    print("此测试需要在 Home Assistant 环境中运行")

    return vcx_devices if 'vcx_devices' in locals() else []

if __name__ == "__main__":
    try:
        asyncio.run(test_bluetooth_scan())
    except KeyboardInterrupt:
        print("\n\n扫描已中断")
        sys.exit(0)
