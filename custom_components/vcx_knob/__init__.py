"""VCX-Knob 智能马桶 Home Assistant 集成

此集成通过蓝牙低功耗 (BLE) 提供对 VCX-Knob 智能马桶设备的本地控制。

该集成使用 bleak 库进行 BLE 通信，并实现了自定义协议与设备通信。

配置:
    此集成使用配置流程进行设置。通过 Home Assistant UI 添加：
    设置 → 设备与服务 → 添加集成 → 搜索 "VCX-Knob"

功能:
    - 开关实体，用于开/关控制（冲水、座圈、气泡、热风、雷达等）
    - 选择实体，用于多选项设置（温度、档位等）
    - 按钮实体，用于一次性操作（大冲水、小冲水、恢复出厂设置）
    - 传感器实体，用于监控（信号强度、百分比、时间）
    - 连接状态的二进制传感器
    - 蓝牙配对服务（通过开发者工具调用）

设备支持:
    - VCX-Knob 智能马桶
"""

import logging
from typing import Final

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    DOMAIN,
)
from .coordinator import VCXKnobCoordinator, VCXKnobBLEClient

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 平台
# ============================================================================

PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
]

# 用于跟踪配置条目数量，管理服务生命周期
_DATA_ENTRY_COUNT = "entry_count"


# ============================================================================
# 设置函数
# ============================================================================

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """设置 VCX-Knob 集成

    Args:
        hass: Home Assistant 实例
        config: 配置字典

    Returns:
        如果设置成功返回 True
    """
    print(f"DEBUG: async_setup called for {DOMAIN}")
    _LOGGER.info("VCX-Knob async_setup called")
    # 初始化 entry 计数器
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][_DATA_ENTRY_COUNT] = 0
    print(f"DEBUG: entry_count initialized to 0")
    _LOGGER.info("entry_count initialized to 0")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """从配置条目设置 VCX-Knob

    当设置或更新配置条目时调用此函数。
    它创建 BLE 客户端和协调器，并设置所有平台。

    Args:
        hass: Home Assistant 实例
        entry: 配置条目

    Returns:
        如果设置成功返回 True，否则返回 False
    """
    print(f"DEBUG: VCX-Knob async_setup_entry called for {entry.title}")
    _LOGGER.info("正在设置 VCX-Knob 集成: %s", entry.title)

    # 从配置条目获取设备信息
    device_address = entry.data.get(CONF_DEVICE_ADDRESS) or entry.data.get(CONF_ADDRESS)
    device_name = entry.data.get(CONF_DEVICE_NAME) or entry.data.get(CONF_NAME, "VCX-Knob")

    print(f"DEBUG: device_address={device_address}, device_name={device_name}")
    _LOGGER.info("设备地址: %s, 设备名称: %s", device_address, device_name)

    if not device_address:
        _LOGGER.error("配置条目中没有设备地址")
        return False

    # 增加条目计数
    hass.data[DOMAIN][_DATA_ENTRY_COUNT] = hass.data[DOMAIN].get(_DATA_ENTRY_COUNT, 0) + 1
    entry_count = hass.data[DOMAIN][_DATA_ENTRY_COUNT]
    print(f"DEBUG: entry_count={entry_count}")
    _LOGGER.info("配置条目计数: %d (设备: %s)", entry_count, device_name)

    # 如果这是第一个条目，注册服务
    if entry_count == 1:
        print(f"DEBUG: Calling _async_setup_bluetooth_services")
        _LOGGER.info("这是第一个配置条目，正在注册蓝牙配对服务...")
        await _async_setup_bluetooth_services(hass)
        print(f"DEBUG: Finished _async_setup_bluetooth_services")
    else:
        print(f"DEBUG: Skipping service registration (entry_count={entry_count})")
        _LOGGER.info("跳过服务注册（已有 %d 个条目）", entry_count)

    if not device_address:
        _LOGGER.error("配置条目中没有设备地址")
        return False

    # 创建 BLE 客户端和通知回调
    coordinator_instance = None

    def _notification_callback(data: bytes) -> None:
        """处理 BLE 通知"""
        # 协调器将在轮询期间处理通知
        pass

    client = VCXKnobBLEClient(
        address=device_address,
        name=device_name,
        notification_callback=_notification_callback,
    )

    # 创建协调器
    coordinator = VCXKnobCoordinator(
        hass=hass,
        config_entry=entry,
        client=client,
        poll_interval=30,  # 默认 30 秒
    )

    # 在 hass 数据中存储协调器
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # 设置平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 在更新时重新加载条目
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("VCX-Knob 集成设置完成: %s", device_name)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目

    Args:
        hass: Home Assistant 实例
        entry: 要卸载的配置条目

    Returns:
        如果卸载成功返回 True，否则返回 False
    """
    _LOGGER.info("正在卸载 VCX-Knob 集成: %s", entry.title)

    # 卸载平台
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # 断开 BLE 客户端连接
        coordinator: VCXKnobCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()

        # 减少条目计数
        hass.data[DOMAIN][_DATA_ENTRY_COUNT] = hass.data[DOMAIN].get(_DATA_ENTRY_COUNT, 1) - 1

        # 如果这是最后一个条目，注销服务
        if hass.data[DOMAIN][_DATA_ENTRY_COUNT] == 0:
            await _async_unload_bluetooth_services(hass)

        _LOGGER.info("VCX-Knob 集成已卸载: %s", entry.title)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """更新选项

    Args:
        hass: Home Assistant 实例
        entry: 已更新的配置条目
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """迁移旧条目数据

    Args:
        hass: Home Assistant 实例
        entry: 要迁移的配置条目

    Returns:
        如果迁移成功返回 True
    """
    _LOGGER.debug("正在从版本 %s.%s 迁移配置条目", entry.version, entry.minor_version)

    if entry.version == 1:
        # 目前不需要迁移
        pass

    return True


# ============================================================================
# 蓝牙服务管理
# ============================================================================

async def _async_setup_bluetooth_services(hass: HomeAssistant) -> None:
    """设置蓝牙配对相关服务

    Args:
        hass: Home Assistant 实例
    """
    print("DEBUG: _async_setup_bluetooth_services called")
    _LOGGER.info("正在调用 _async_setup_bluetooth_services...")
    try:
        from .bluetooth_pairing import async_setup_services
        print("DEBUG: async_setup_services imported")
        _LOGGER.info("已导入 async_setup_services，正在调用...")
        await async_setup_services(hass)
        print("DEBUG: async_setup_services completed")
        _LOGGER.info("蓝牙配对服务已启用")
    except ImportError as err:
        print(f"DEBUG: ImportError: {err}")
        _LOGGER.error("无法导入 async_setup_services: %s", err)
        raise
    except Exception as err:
        print(f"DEBUG: Exception: {err}")
        _LOGGER.error("启用蓝牙配对服务时出错: %s", err, exc_info=True)
        raise


async def _async_unload_bluetooth_services(hass: HomeAssistant) -> None:
    """卸载蓝牙配对相关服务

    Args:
        hass: Home Assistant 实例
    """
    try:
        from .bluetooth_pairing import async_unload_services
        await async_unload_services(hass)
        _LOGGER.info("蓝牙配对服务已禁用")
    except ImportError:
        pass
    except Exception as err:
        _LOGGER.error("禁用蓝牙配对服务时出错: %s", err)
