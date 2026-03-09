"""VCX-Knob 集成的开关实体

此模块提供用于控制 VCX-Knob 智能马桶设备各种开/关功能的开关实体
"""

import logging
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    SWITCHES,
    Command,
    DOMAIN,
)
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 开关实体描述
# ============================================================================

@dataclass(frozen=True)
class VCXKnobSwitchDescription:
    """VCX-Knob 开关的描述"""

    key: str
    name: str
    icon: str
    command: str | None = None
    data_byte: int = 0
    state_key: str | None = None
    entity_category: str | None = None


SWITCH_DESCRIPTIONS: tuple[VCXKnobSwitchDescription, ...] = (
    VCXKnobSwitchDescription(
        key="flush",
        name="冲水",
        icon="mdi:toilet",
        state_key="flush_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="seat",
        name="座圈",
        icon="mdi:seat",
        state_key="seat_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="bubble",
        name="气泡",
        icon="mdi:buffer",
        state_key="bubble_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="air",
        name="热风",
        icon="mdi:air-filter",
        state_key="air_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="radar",
        name="雷达",
        icon="mdi:radar",
        state_key="radar_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="voice",
        name="语音控制",
        icon="mdi:microphone",
        command=Command.YUYIN,
        state_key="voice_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="sensor",
        name="传感器",
        icon="mdi:sensor",
        state_key="sensors_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="auto_mode",
        name="自动模式",
        icon="mdi:autorenew",
        command=Command.ZIDONG,
        state_key="auto_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="night_light",
        name="夜灯",
        icon="mdi:lightbulb-night",
        command=Command.GUANGDENG,
        state_key="lights_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="foot_sensor",
        name="脚感应",
        icon="mdi:eye",
        state_key="foot_sensor_enabled",
        entity_category="config",
    ),
    VCXKnobSwitchDescription(
        key="sterilization",
        name="杀菌",
        icon="mdi:spray-bottle",
        state_key="sterilization_enabled",
        entity_category="config",
    ),
)


# ============================================================================
# 开关实体
# ============================================================================

class VCXKnobSwitch(SwitchEntity):
    """VCX-Knob 开关实体的表示"""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: VCXKnobSwitchDescription,
    ) -> None:
        """初始化开关

        Args:
            coordinator: 数据协调器
            description: 开关描述
        """
        super().__init__()

        self._coordinator = coordinator
        self._description = description

        self._attr_has_entity_name = False
        self._attr_unique_id = f"{coordinator.device_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "Knob 智能马桶",
        }
        self._attr_should_poll = False  # 使用协调器

    async def async_added_to_hass(self) -> None:
        """当实体添加到 hass 时"""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """处理来自协调器的更新数据"""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """返回实体是否可用"""
        # 开关在客户端存在就可用
        try:
            client = self._coordinator.client._client
            if client is None:
                return False
            try:
                return client.is_connected
            except Exception:
                # 如果无法检查连接状态，假设可用
                return True
        except Exception:
            return False

    @property
    def name(self) -> str:
        """返回实体名称"""
        return self._description.name

    @property
    def is_on(self) -> bool | None:
        """如果开关打开则返回 True"""
        data = self._coordinator.data
        if data is None:
            return None
        state_key = self._description.state_key
        if state_key:
            return data.get(state_key, False)
        return None

    @property
    def icon(self) -> str | None:
        """返回图标"""
        return self._description.icon

    async def async_turn_on(self, **kwargs) -> None:
        """打开开关

        Args:
            **kwargs: 额外关键字参数
        """
        if self._description.command:
            await self._coordinator.async_send_command(
                self._description.command,
                1,  # d1 = 1 启用
                0,
                0,
            )

    async def async_turn_off(self, **kwargs) -> None:
        """关闭开关

        Args:
            **kwargs: 额外关键字参数
        """
        if self._description.command:
            await self._coordinator.async_send_command(
                self._description.command,
                0,  # d1 = 0 禁用
                0,
                0,
            )


# ============================================================================
# 设置函数
# ============================================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置 VCX-Knob 开关实体

    Args:
        hass: Home Assistant 实例
        entry: 配置条目
        async_add_entities: 添加实体的回调
    """
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VCXKnobSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
    ]

    async_add_entities(entities)
