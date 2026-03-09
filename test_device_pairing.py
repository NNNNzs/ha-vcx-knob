#!/usr/bin/env python3
"""测试 VCX-Knob 设备配对和连接"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient

DEVICE_ADDRESS = "88:36:A2:D8:80:AC"
SERVICE_UUID = "0000FFA0-0000-1000-8000-00805F9B34FB"
WRITE_CHAR_UUID = "0000FFA1-0000-1000-8000-00805F9B34FB"
NOTIFY_CHAR_UUID = "0000FFA2-0000-1000-8000-00805F9B34FB"


async def test_device():
    """测试设备连接和通信"""

    print("=" * 50)
    print("VCX-Knob 设备测试")
    print("=" * 50)

    # 1. 扫描设备
    print("\n1. 扫描设备...")
    device = await BleakScanner.find_device_by_address(DEVICE_ADDRESS, timeout=10)
    if not device:
        print(f"❌ 未找到设备 {DEVICE_ADDRESS}")
        return

    print(f"✅ 找到设备: {device.name}")
    print(f"   地址: {device.address}")
    print(f"   详情: {device.details}")

    # 2. 连接设备
    print("\n2. 连接设备...")
    try:
        client = BleakClient(device)
        await client.connect()
        print(f"✅ 已连接: {client.is_connected}")

        # 3. 获取服务
        print("\n3. 获取服务...")
        services = client.services
        print(f"   找到 {len(services)} 个服务:")

        target_service_found = False
        for service in services:
            print(f"   - {service.uuid}")
            if str(service.uuid).lower() == SERVICE_UUID.lower():
                target_service_found = True
                print(f"     ✅ 找到目标服务!")
                for char in service.characteristics:
                    print(f"       特征: {char.uuid}")
                    print(f"         属性: {char.properties}")

        if not target_service_found:
            print(f"   ⚠️  未找到目标服务 {SERVICE_UUID}")

        # 4. 测试读取
        print("\n4. 尝试订阅通知...")
        try:
            def notification_handler(sender, data):
                print(f"   📨 收到通知: {data.hex().upper()}")

            await client.start_notify(NOTIFY_CHAR_UUID, notification_handler)
            print(f"   ✅ 已订阅通知")

            # 等待一下看是否有数据
            await asyncio.sleep(2)

            await client.stop_notify(NOTIFY_CHAR_UUID)
            print(f"   ✅ 已取消订阅")

        except Exception as e:
            print(f"   ❌ 通知订阅失败: {e}")

        # 5. 测试写入
        print("\n5. 尝试写入命令...")
        test_command = bytes([0xAA, 0x08, 0x02, 0xFF, 0x00, 0x00, 0x00, 0xB5])
        print(f"   命令: {test_command.hex().upper()}")

        try:
            await client.write_gatt_char(
                WRITE_CHAR_UUID,
                test_command,
                response=True
            )
            print(f"   ✅ 写入成功!")
        except Exception as e:
            print(f"   ❌ 写入失败: {e}")

            # 尝试无响应写入
            try:
                await client.write_gatt_char(
                    WRITE_CHAR_UUID,
                    test_command,
                    response=False
                )
                print(f"   ✅ 无响应写入成功!")
            except Exception as e2:
                print(f"   ❌ 无响应写入也失败: {e2}")

        # 6. 断开连接
        print("\n6. 断开连接...")
        await client.disconnect()
        print(f"✅ 已断开连接")

    except Exception as e:
        print(f"❌ 连接或测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_device())
