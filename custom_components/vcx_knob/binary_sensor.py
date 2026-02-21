"""VCX-Knob 集成的二进制传感器实体

此模块提供报告来自 VCX-Knob 智能马桶设备两状态信息的二进制传感器实体
"""

import logging
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 二进制传感器实体描述
# ============================================================================

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="connection",
        name="已连接",
        device_class="connectivity",
        entity_category="diagnostic",
    ),
)


# ============================================================================
# 二进制传感器实体
# ============================================================================

class VCXKnobBinarySensor(BinarySensorEntity):
    """VCX-Knob 二进制传感器实体的表示"""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """初始化二进制传感器

        Args:
            coordinator: 数据协调器
            description: 二进制传感器描述
        """
        super().__init__()

        self._coordinator = coordinator
        self.entity_description = description

        self._attr_has_entity_name = True
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
    def is_on(self) -> bool:
        """如果二进制传感器打开则返回 True"""
        if self.entity_description.key == "connection":
            return self._coordinator.data.get("connected", False)
        return False


# ============================================================================
# 设置函数
# ============================================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置 VCX-Knob 二进制传感器实体

    Args:
        hass: Home Assistant 实例
        entry: 配置条目
        async_add_entities: 添加实体的回调
    """
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VCXKnobBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    ]

    async_add_entities(entities)
