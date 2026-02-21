"""VCX-Knob 集成的按钮实体

此模块提供用于触发 VCX-Knob 智能马桶设备一次性操作的按钮实体，
如冲水和恢复出厂设置
"""

import logging
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BUTTONS,
    Command,
    DOMAIN,
)
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 按钮实体描述
# ============================================================================

@dataclass(frozen=True)
class VCXKnobButtonDescription:
    """VCX-Knob 按钮的描述"""

    key: str
    name: str
    icon: str
    command: str
    data_byte: int = 0
    entity_category: str | None = None


BUTTON_DESCRIPTIONS: tuple[VCXKnobButtonDescription, ...] = (
    VCXKnobButtonDescription(
        key="big_flush",
        name="大冲水",
        icon="mdi:toilet",
        command=Command.DACHONG,
    ),
    VCXKnobButtonDescription(
        key="small_flush",
        name="小冲水",
        icon="mdi:toilet",
        command=Command.XIAOCHONG,
    ),
    VCXKnobButtonDescription(
        key="factory_reset",
        name="恢复出厂设置",
        icon="mdi:restore",
        command=Command.FUYUAN,
        entity_category="config",
    ),
)


# ============================================================================
# 按钮实体
# ============================================================================

class VCXKnobButton(ButtonEntity):
    """VCX-Knob 按钮实体的表示"""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: VCXKnobButtonDescription,
    ) -> None:
        """初始化按钮

        Args:
            coordinator: 数据协调器
            description: 按钮描述
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
        self._attr_should_poll = False  # 按钮不轮询

    @property
    def available(self) -> bool:
        """返回实体是否可用"""
        return self._coordinator.data.get("connected", False)

    @property
    def icon(self) -> str | None:
        """返回图标"""
        return self._description.icon

    async def async_press(self, **kwargs) -> None:
        """按下按钮

        Args:
            **kwargs: 额外关键字参数
        """
        await self._coordinator.async_send_command(
            self._description.command,
            self._description.data_byte,
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
    """设置 VCX-Knob 按钮实体

    Args:
        hass: Home Assistant 实例
        entry: 配置条目
        async_add_entities: 添加实体的回调
    """
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VCXKnobButton(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    ]

    async_add_entities(entities)
