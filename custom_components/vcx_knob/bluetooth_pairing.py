"""
VCX-Knob 蓝牙配对服务

此服务提供通过 Home Assistant UI 执行蓝牙配对的功能。
用户可以通过 "开发者工具 → 动作" 来扫描、配对和验证 VCX-Knob 设备。
"""

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_PAIR_BLUETOOTH_DEVICE = "pair_bluetooth_device"
SERVICE_SCAN_BLUETOOTH = "scan_bluetooth_device"
SERVICE_GET_DEVICE_INFO = "get_bluetooth_device_info"

SERVICE_SCHEMA_PAIR = vol.Schema({
    vol.Required("device_address"): str,
    vol.Optional("timeout", default=15): int,
})

SERVICE_SCHEMA_SCAN = vol.Schema({
    vol.Optional("timeout", default=10): int,
    vol.Optional("device_filter", default="VCX"): str,
})

SERVICE_SCHEMA_INFO = vol.Schema({
    vol.Required("device_address"): str,
})


# ============================================================================
# 服务处理函数（模块级别，避免垃圾回收问题）
# ============================================================================

async def _pair_service_handler(hass: HomeAssistant, call: ServiceCall) -> None:
    """配对服务处理程序"""
    try:
        device_address = call.data.get("device_address")
        if not device_address:
            _LOGGER.error("配对服务缺少 device_address 参数")
            return

        timeout = call.data.get("timeout", 15)

        _LOGGER.info("开始配对蓝牙设备: %s", device_address)

        # 执行配对
        process = await asyncio.create_subprocess_exec(
            "bluetoothctl",
            "pair",
            device_address,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            result = stdout.decode() + stderr.decode()

            if "Pairing successful" in result:
                _LOGGER.info("蓝牙配对成功: %s", device_address)

                # 配对成功后，信任设备
                trust_process = await asyncio.create_subprocess_exec(
                    "bluetoothctl",
                    "trust",
                    device_address,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await trust_process.communicate()

            elif "Already paired" in result:
                _LOGGER.info("设备已配对: %s", device_address)
            elif "Failed to pair" in result or "AuthenticationCanceled" in result:
                _LOGGER.warning("蓝牙配对失败: %s", device_address)
            else:
                _LOGGER.warning("未知配对结果: %s", result)

        except asyncio.TimeoutError:
            process.kill()
            _LOGGER.error("蓝牙配对超时: %s", device_address)

    except Exception as err:
        _LOGGER.exception("配对服务出错: %s", err)


async def _scan_service_handler(hass: HomeAssistant, call: ServiceCall) -> None:
    """扫描服务处理程序"""
    try:
        timeout = call.data.get("timeout", 10)
        device_filter = call.data.get("device_filter", "VCX")

        _LOGGER.info("开始扫描蓝牙设备（过滤器: %s，超时: %s秒）...", device_filter, timeout)

        try:
            from homeassistant.components.bluetooth import (
                BluetoothCallbackMatcher,
                BluetoothScanningMode,
                async_get_scanner,
                async_register_callback,
                BluetoothServiceInfo,
            )

            discovered_devices = {}

            def service_info_callback(
                service_info: BluetoothServiceInfo,
                _change: Any,
            ) -> None:
                """扫描回调"""
                if service_info.name and device_filter.upper() in service_info.name.upper():
                    discovered_devices[service_info.address] = service_info.name
                    _LOGGER.debug("发现设备: %s (%s)", service_info.name, service_info.address)

            scanner = async_get_scanner(hass)
            remove_callback = async_register_callback(
                hass,
                service_info_callback,
                BluetoothCallbackMatcher(connectable=True),
                BluetoothScanningMode.ACTIVE,
            )

            try:
                await asyncio.sleep(timeout)
            finally:
                remove_callback()

            _LOGGER.info("扫描完成，发现 %d 个设备: %s", len(discovered_devices), discovered_devices)

        except ImportError as err:
            _LOGGER.error("无法导入蓝牙模块: %s", err)
        except Exception as err:
            _LOGGER.error("扫描过程出错: %s", err)

    except Exception as err:
        _LOGGER.exception("扫描服务出错: %s", err)


async def _info_service_handler(hass: HomeAssistant, call: ServiceCall) -> None:
    """设备信息服务处理程序"""
    try:
        device_address = call.data.get("device_address")
        if not device_address:
            _LOGGER.error("设备信息服务缺少 device_address 参数")
            return

        _LOGGER.info("获取设备信息: %s", device_address)

        try:
            process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "info",
                device_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            result = stdout.decode() + stderr.decode()

            # 解析配对状态
            paired = "Paired: yes" in result
            trusted = "Trusted: yes" in result
            connected = "Connected: yes" in result

            _LOGGER.info("设备 %s - 配对: %s, 信任: %s, 连接: %s",
                         device_address, paired, trusted, connected)

        except Exception as err:
            _LOGGER.error("获取设备信息过程出错: %s", err)

    except Exception as err:
        _LOGGER.exception("设备信息服务出错: %s", err)


# ============================================================================
# 服务设置/卸载函数
# ============================================================================

async def async_setup_services(hass: HomeAssistant) -> None:
    """设置 VCX-Knob 服务

    Args:
        hass: Home Assistant 实例
    """
    print("DEBUG: async_setup_services called")
    _LOGGER.info("开始注册蓝牙配对服务...")

    # 注册配对服务
    print(f"DEBUG: Registering {SERVICE_PAIR_BLUETOOTH_DEVICE}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_PAIR_BLUETOOTH_DEVICE,
        lambda call: _pair_service_handler(hass, call),
        SERVICE_SCHEMA_PAIR,
    )
    print(f"DEBUG: {SERVICE_PAIR_BLUETOOTH_DEVICE} registered")

    # 注册扫描服务
    print(f"DEBUG: Registering {SERVICE_SCAN_BLUETOOTH}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_BLUETOOTH,
        lambda call: _scan_service_handler(hass, call),
        SERVICE_SCHEMA_SCAN,
    )
    print(f"DEBUG: {SERVICE_SCAN_BLUETOOTH} registered")

    # 注册设备信息服务
    print(f"DEBUG: Registering {SERVICE_GET_DEVICE_INFO}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DEVICE_INFO,
        lambda call: _info_service_handler(hass, call),
        SERVICE_SCHEMA_INFO,
    )
    print(f"DEBUG: {SERVICE_GET_DEVICE_INFO} registered")

    print(f"DEBUG: All services registered successfully")
    _LOGGER.info("蓝牙配对服务已注册: %s, %s, %s",
                 SERVICE_PAIR_BLUETOOTH_DEVICE, SERVICE_SCAN_BLUETOOTH, SERVICE_GET_DEVICE_INFO)


async def async_unload_services(hass: HomeAssistant) -> None:
    """卸载蓝牙配对服务

    Args:
        hass: Home Assistant 实例
    """
    hass.services.async_remove(DOMAIN, SERVICE_PAIR_BLUETOOTH_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_SCAN_BLUETOOTH)
    hass.services.async_remove(DOMAIN, SERVICE_GET_DEVICE_INFO)
    _LOGGER.info("蓝牙配对服务已注销")
