"""VCX-Knob 集成的按钮实体

此模块提供用于触发 VCX-Knob 智能马桶设备一次性操作的按钮实体，
如冲水和恢复出厂设置
"""

import logging
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
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
    entity_category: EntityCategory | str | None = None


BUTTON_DESCRIPTIONS: tuple[VCXKnobButtonDescription, ...] = (
    # 冲水按钮
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
    # 清洗按钮
    VCXKnobButtonDescription(
        key="feminine_wash",
        name="妇洗",
        icon="mdi:human-female",
        command=Command.FUXI,
    ),
    VCXKnobButtonDescription(
        key="rear_wash",
        name="臀洗",
        icon="mdi:human-male",
        command=Command.TUNXI,
    ),
    VCXKnobButtonDescription(
        key="massage",
        name="按摩",
        icon="mdi:vibrate",
        command=Command.ANMO,
    ),
    # 功能按钮
    VCXKnobButtonDescription(
        key="bubble",
        name="气泡",
        icon="mdi:buffer",
        command=Command.PAOMO,
    ),
    # 控制按钮
    VCXKnobButtonDescription(
        key="stop",
        name="停止",
        icon="mdi:stop",
        command=Command.STOP,
    ),
    VCXKnobButtonDescription(
        key="dry",
        name="烘干",
        icon="mdi:tumble-dryer",
        command=Command.HONGGAN,
    ),
    # 机械控制按钮
    VCXKnobButtonDescription(
        key="open_lid",
        name="翻盖",
        icon="mdi:arrow-up-bold-box",
        command=Command.FANGAI,
    ),
    VCXKnobButtonDescription(
        key="open_seat",
        name="翻圈",
        icon="mdi:chair-rolling",
        command=Command.FANQUAN,
    ),
    VCXKnobButtonDescription(
        key="close",
        name="关闭",
        icon="mdi:arrow-down-bold-box",
        command=Command.JIENENG,
    ),
    # 其他功能按钮
    VCXKnobButtonDescription(
        key="runbi",
        name="润壁",
        icon="mdi:water-pump",
        command=Command.RUNBI,
    ),
    VCXKnobButtonDescription(
        key="self_clean",
        name="自洁",
        icon="mdi:sparkles",
        command=Command.ZIJIE,
    ),
    # 系统按钮
    VCXKnobButtonDescription(
        key="factory_reset",
        name="恢复出厂设置",
        icon="mdi:restore",
        command=Command.HUIFUCHUCHANG,
        entity_category=EntityCategory.CONFIG,
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
        self._attr_entity_description = description  # 设置 entity_description 属性

        self._attr_has_entity_name = False
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
        # 按钮始终可用，即使设备未连接
        # 这样用户可以尝试点击按钮，如果设备离线，会在点击时显示错误
        # 这比始终显示灰色按钮提供更好的用户体验
        return True

    @property
    def name(self) -> str:
        """返回实体名称"""
        return self._description.name

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
