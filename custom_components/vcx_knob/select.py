"""VCX-Knob 集成的选择实体

此模块提供用于在 VCX-Knob 智能马桶设备的多个选项之间进行选择的选择实体，
如温度级别
"""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    SELECTS,
    DOMAIN,
)
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 选择实体
# ============================================================================

class VCXKnobSelect(SelectEntity):
    """VCX-Knob 选择实体的表示"""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description,
    ) -> None:
        """初始化选择

        Args:
            coordinator: 数据协调器
            description: 选择描述
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
        data = self._coordinator.data
        if data is None:
            self.async_write_ha_state()
            return

        state_key = self._description.state_key
        if state_key:
            state_code = data.get(state_key)
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
        # 选择在客户端存在就可用
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
        for description in SELECTS
    ]

    async_add_entities(entities)
