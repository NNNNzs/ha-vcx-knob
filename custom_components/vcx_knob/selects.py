"""VCX-Knob 集成的选择实体

此模块提供用于在 VCX-Knob 智能马桶设备的多个选项之间进行选择的选择实体，
如温度级别
"""

import logging
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    SELECTS,
    Command,
    DOMAIN,
)
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 选择实体描述
# ============================================================================

@dataclass(frozen=True)
class VCXKnobSelectDescription:
    """VCX-Knob 选择的描述"""

    key: str
    name: str
    icon: str
    command: str
    options: list[str]
    options_map: dict[str, int]  # 选项值到数据字节的映射
    state_key: str | None = None
    entity_category: str | None = None
    unit: str | None = None


SELECT_DESCRIPTIONS: tuple[VCXKnobSelectDescription, ...] = (
    VCXKnobSelectDescription(
        key="water_temperature",
        name="水温",
        icon="mdi:water-thermometer",
        command=Command.SHUIWEN,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
        state_key="water_temp_code",
        entity_category="config",
    ),
    VCXKnobSelectDescription(
        key="seat_temperature",
        name="座温",
        icon="mdi:seat",
        command=Command.ZUOWEN,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
        state_key="seat_temp_code",
        entity_category="config",
    ),
    VCXKnobSelectDescription(
        key="wind_temperature",
        name="风温",
        icon="mdi:air-conditioner",
        command=Command.QIANGWEN,
        options=["off", "40", "45", "50"],
        options_map={"off": 0, "40": 1, "45": 2, "50": 3},
        state_key="wind_temp_code",
        entity_category="config",
    ),
    VCXKnobSelectDescription(
        key="water_level",
        name="水量",
        icon="mdi:water",
        command=Command.SHUILIANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
        state_key="water_level_code",
        entity_category="config",
    ),
    VCXKnobSelectDescription(
        key="air_level",
        name="热风档位",
        icon="mdi:air-filter",
        command=Command.QIANGDANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
        state_key="air_level_code",
        entity_category="config",
    ),
    VCXKnobSelectDescription(
        key="light_brightness",
        name="灯光亮度",
        icon="mdi:brightness-6",
        command=Command.GUANGDANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
        state_key="light_brightness_code",
        entity_category="config",
    ),
    VCXKnobSelectDescription(
        key="radar_sensitivity",
        name="雷达灵敏度",
        icon="mdi:radar",
        command=Command.CHUANGAN,
        options=["low", "medium", "high"],
        options_map={"low": 1, "medium": 2, "high": 3},
        entity_category="config",
    ),
)


# ============================================================================
# 选择实体
# ============================================================================

class VCXKnobSelect(SelectEntity):
    """VCX-Knob 选择实体的表示"""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: VCXKnobSelectDescription,
    ) -> None:
        """初始化选择

        Args:
            coordinator: 数据协调器
            description: 选择描述
        """
        super().__init__()

        self._coordinator = coordinator
        self._description = description

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.device_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "Knob 智能马桶",
        }
        self._attr_should_poll = False  # 使用协调器
        self._attr_options = description.options
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """当实体添加到 hass 时"""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )
        # 初始化状态
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """处理来自协调器的更新数据"""
        state_key = self._description.state_key
        if state_key:
            state_code = self._coordinator.data.get(state_key)
            if state_code is not None:
                # 将代码映射到选项值
                self._attr_current_option = self._code_to_option(state_code)
        self.async_write_ha_state()

    def _code_to_option(self, code: int) -> str | None:
        """将代码转换为选项值

        Args:
            code: 来自设备的状态代码

        Returns:
            选项值，如果未找到则返回 None
        """
        # 特殊处理温度值
        if self._description.key in ("water_temperature", "seat_temperature"):
            temp_map = {0: "off", 1: "34", 2: "37", 3: "40"}
            return temp_map.get(code)
        elif self._description.key == "wind_temperature":
            temp_map = {0: "off", 1: "40", 2: "45", 3: "50"}
            return temp_map.get(code)
        else:
            # 对于基于档位的选择
            level_map = {0: "off", 1: "low", 2: "medium", 3: "high"}
            if self._description.key == "radar_sensitivity":
                level_map = {1: "low", 2: "medium", 3: "high"}
            return level_map.get(code)

    @property
    def available(self) -> bool:
        """返回实体是否可用"""
        return self._coordinator.last_update_success and self._coordinator.data.get("connected", False)

    @property
    def icon(self) -> str | None:
        """返回图标"""
        return self._description.icon

    async def async_select_option(self, option: str) -> None:
        """更改选定的选项

        Args:
            option: 要选择的选项
        """
        data_byte = self._description.options_map.get(option)
        if data_byte is None:
            _LOGGER.error("无效的选项: %s", option)
            return

        await self._coordinator.async_send_command(
            self._description.command,
            data_byte,
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
    """设置 VCX-Knob 选择实体

    Args:
        hass: Home Assistant 实例
        entry: 配置条目
        async_add_entities: 添加实体的回调
    """
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VCXKnobSelect(coordinator, description)
        for description in SELECT_DESCRIPTIONS
    ]

    async_add_entities(entities)
