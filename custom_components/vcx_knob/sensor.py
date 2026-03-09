"""VCX-Knob 集成的传感器实体

此模块提供报告 VCX-Knob 智能马桶设备各种测量值的传感器实体
"""

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTime,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 传感器实体描述
# ============================================================================

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="device_address",
        name="蓝牙地址",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:bluetooth",
    ),
    SensorEntityDescription(
        key="rssi",
        name="信号强度",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class="signal_strength",
        state_class="measurement",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="air_percentage",
        name="热风百分比",
        native_unit_of_measurement=PERCENTAGE,
        state_class="measurement",
        icon="mdi:air-filter",
    ),
    SensorEntityDescription(
        key="water_percentage",
        name="水量百分比",
        native_unit_of_measurement=PERCENTAGE,
        state_class="measurement",
        icon="mdi:water-percent",
    ),
    SensorEntityDescription(
        key="radar_level",
        name="雷达等级",
        state_class="measurement",
        icon="mdi:radar",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="cover_close_time",
        name="盖板关闭时间",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class="measurement",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="cover_flip_intensity",
        name="盖板翻转强度",
        state_class="measurement",
        icon="mdi:arrow-up-down",
    ),
    SensorEntityDescription(
        key="ring_flip_intensity",
        name="座圈翻转强度",
        state_class="measurement",
        icon="mdi:arrow-up-down",
    ),
    SensorEntityDescription(
        key="cover_close_intensity",
        name="盖板关闭强度",
        state_class="measurement",
        icon="mdi:arrow-collapse",
    ),
    SensorEntityDescription(
        key="bubble_level",
        name="气泡等级",
        state_class="measurement",
        icon="mdi:buffer",
    ),
    SensorEntityDescription(
        key="big_flush_timing",
        name="大冲水时间",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class="measurement",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="small_flush_timing",
        name="小冲水时间",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class="measurement",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="foot_sensor_distance",
        name="脚感应距离",
        native_unit_of_measurement="cm",
        state_class="measurement",
        icon="mdi:ruler",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="sterilization_time",
        name="杀菌时间",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class="measurement",
        icon="mdi:clock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


# ============================================================================
# 传感器实体
# ============================================================================

class VCXKnobSensor(SensorEntity):
    """VCX-Knob 传感器实体的表示"""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """初始化传感器

        Args:
            coordinator: 数据协调器
            description: 传感器描述
        """
        super().__init__()

        self._coordinator = coordinator
        self.entity_description = description
        self._attr_has_entity_name = False
        self._attr_unique_id = f"{coordinator.device_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "Knob 智能马桶",
        }
        self._attr_should_poll = False  # 使用协调器
        self.entity_description = description

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
        # 蓝牙地址传感器始终可用，其他传感器需要连接
        if self.entity_description.key == "device_address":
            return True
        data = self._coordinator.data
        if data is None:
            return False
        return self._coordinator.last_update_success and data.get("connected", False)

    @property
    def native_value(self) -> int | None:
        """返回传感器的状态"""
        data = self._coordinator.data
        if data is None:
            return None
        return data.get(self.entity_description.key)


# ============================================================================
# 设置函数
# ============================================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置 VCX-Knob 传感器实体

    Args:
        hass: Home Assistant 实例
        entry: 配置条目
        async_add_entities: 添加实体的回调
    """
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VCXKnobSensor(coordinator, description)
        for description in SENSORS
    ]

    async_add_entities(entities)
