"""VCX-Knob 集成的常量定义"""

from dataclasses import dataclass, field
from enum import StrEnum

from homeassistant.helpers.entity import EntityCategory

# ============================================================================
# 域名和配置
# ============================================================================
DOMAIN = "vcx_knob"
MANUFACTURER = "VCX"
MODEL = "Knob Smart Toilet"

# 默认配置值
DEFAULT_SCAN_TIMEOUT = 10  # 秒
DEFAULT_CONNECTION_TIMEOUT = 30  # 秒
DEFAULT_STATUS_POLL_INTERVAL = 30  # 秒
DEFAULT_AUTO_CONNECT = True  # 默认自动连接

# ============================================================================
# BLE UUID
# ============================================================================
# VCX-Knob 设备的服务 UUID
BLE_SERVICE_UUID = "0000FFA0-0000-1000-8000-00805F9B34FB"

# 写特征 UUID - 用于发送命令
BLE_WRITE_CHARACTERISTIC_UUID = "0000FFA1-0000-1000-8000-00805F9B34FB"

# 通知特征 UUID - 用于接收状态更新
BLE_NOTIFY_CHARACTERISTIC_UUID = "0000FFA2-0000-1000-8000-00805F9B34FB"

# 设备名称过滤器
BLE_DEVICE_NAME_FILTER = "VCX-Knob"

# ============================================================================
# 协议常量
# ============================================================================

# 协议帧结构
PROTOCOL_HEADER = 0xAA
PROTOCOL_LENGTH = 0x08
PROTOCOL_CMD_TYPE = 0x02  # 命令类型
PROTOCOL_STATUS_TYPE = 0x88  # 状态类型


class Command(StrEnum):
    """VCX-Knob 设备的命令码

    命令格式参考微信小程序和 Node.js 服务的实现
    """

    # ========================================================================
    # 核心命令（P0 - 必须实现）
    # ========================================================================

    # 查询命令
    ZHUANGTAI = "FF"  # 查询状态

    # 清洗命令（核心功能）
    FUXI = "01"  # 妇洗
    TUNXI = "02"  # 臀洗
    HONGGAN = "04"  # 烘干/停止
    STOP = "09"  # 停止
    FANGAI = "05"  # 翻盖
    FANQUAN = "06"  # 翻圈
    SHUIYA = "0A"  # 水压调节
    PENGAN = "0C"  # 喷杆调节
    ANMO = "14"  # 按摩

    # 冲水命令
    DACHONG = "07"  # 大冲水
    XIAOCHONG = "17"  # 小冲水

    # 气泡命令
    PAOMO = "12"  # 气泡
    KONGQI = "19"  # 空气

    # ========================================================================
    # 温度和档位命令（P0 - 必须实现）
    # ========================================================================

    ZUOWEN = "30"  # 座温
    SHUIWEN = "10"  # 水温
    FENGWEN = "20"  # 风温

    # 保留别名以兼容现有代码
    QIANGWEN = "20"  # 风温（别名）
    SHUILIANG = "06"  # 水量（使用翻圈命令值）

    # 档位命令
    QIANGDANG = "21"  # 热风档位（需要确认实际命令码）

    # ========================================================================
    # 机械控制命令（P1 - 重要）
    # ========================================================================

    JIENENG = "13"  # 节能/关闭

    # 翻盖翻圈子命令
    FENWEIDENG = "1A"  # 氛围灯
    ZIJIE = "11"  # 自洁
    PENTOU = "1B"  # 喷头

    # 润壁命令
    RUNBI = "E3"  # 润壁

    # ========================================================================
    # 其他控制命令
    # ========================================================================

    ZIDONG = "08"  # 自动模式
    SHUIMIAN = "18"  # 水面

    # 灯光命令
    GUANGDENG = "50"  # 夜灯（需要确认实际命令码）
    GUANGDANG = "51"  # 灯光亮度（需要确认实际命令码）

    # 语音命令
    YUYIN = "80"  # 语音控制（需要确认实际命令码）

    # ========================================================================
    # 工程模式命令（P2 - 可选）
    # ========================================================================

    # 传感器命令
    CHUANGAN = "90"  # 传感器设置

    # 系统命令
    HUIFUCHUCHANG = "26"  # 恢复出厂设置
    FUYUAN = "26"  # 恢复出厂设置（别名）

    # 脚感应
    JIAOGAN = "A4"  # 脚感应

    # 杀菌时间
    SHAJUN = "F1"  # 杀菌时间


# ============================================================================
# 状态包类型
# ============================================================================

class StatusPacketType(StrEnum):
    """从设备接收的状态包类型"""

    TYPE_01 = "01"  # 基础状态（冲水、座圈、气泡、热风、雷达、语音、传感器、灯光）
    TYPE_02 = "02"  # 温度（水/风/座档位和温度、灯光亮度）
    TYPE_03 = "03"  # 百分比（风%、水%、雷达等级、盖板关闭时间）
    TYPE_04 = "04"  # 强度（盖板/座圈翻转和关闭强度）
    TYPE_05 = "05"  # 冲水参数（气泡等级、大/小冲水时间）
    TYPE_06 = "06"  # 传感器（脚感应启用/距离、杀菌时间）


# ============================================================================
# 温度映射
# ============================================================================

# 水温和座温：0=关闭，1=34°C，2=37°C，3=40°C
WATER_SEAT_TEMPERATURE_MAP = {
    0: "off",
    1: 34,
    2: 37,
    3: 40,
}

# 命令的反向映射
TEMP_TO_CODE_MAP = {
    "off": 0,
    34: 1,
    37: 2,
    40: 3,
}

# 风温：0=关闭，1=40°C，2=45°C，3=50°C
WIND_TEMPERATURE_MAP = {
    0: "off",
    1: 40,
    2: 45,
    3: 50,
}

# ============================================================================
# 实体类型和描述
# ============================================================================


@dataclass(frozen=True)
class EntityDescription:
    """实体描述的基类"""

    key: str
    name: str
    entity_category: EntityCategory | str | None = None
    translation_key: str | None = None
    device_class: str | None = None
    unit: str | None = None
    state_class: str | None = None

    def __post_init__(self):
        # 确保必填字段不为空
        if not self.key:
            raise ValueError("key 不能为空")
        if not self.name:
            raise ValueError("name 不能为空")


@dataclass(frozen=True)
class SwitchEntityDescription(EntityDescription):
    """开关实体的描述"""

    command: str | None = None  # 切换时发送的命令
    data_byte: str = "00"  # 命令的 d1 值


@dataclass(frozen=True)
class SensorEntityDescription(EntityDescription):
    """传感器实体的描述"""

    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    icon: str | None = None


@dataclass(frozen=True)
class ButtonEntityDescription(EntityDescription):
    """按钮实体的描述"""

    command: str = field(default="")
    data_byte: str = "00"


@dataclass(frozen=True)
class SelectEntityDescription(EntityDescription):
    """选择实体的描述"""

    command: str = field(default="")
    options: list[str] = field(default_factory=list)
    options_map: dict[str, int] = field(default_factory=dict)
    state_key: str | None = None
    icon: str | None = None


# ============================================================================
# 开关定义
# ============================================================================

SWITCHES = [
    SwitchEntityDescription(
        key="radar",
        name="雷达",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="voice",
        name="语音控制",
        entity_category=EntityCategory.CONFIG,
        command=Command.YUYIN,
    ),
    SwitchEntityDescription(
        key="sensor",
        name="传感器",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="auto_mode",
        name="自动模式",
        entity_category=EntityCategory.CONFIG,
        command=Command.ZIDONG,
    ),
    SwitchEntityDescription(
        key="night_light",
        name="夜灯",
        entity_category=EntityCategory.CONFIG,
        command=Command.GUANGDENG,
    ),
    SwitchEntityDescription(
        key="foot_sensor",
        name="脚感应",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="sterilization",
        name="杀菌",
        entity_category=EntityCategory.CONFIG,
    ),
]

# ============================================================================
# 按钮定义
# ============================================================================

BUTTONS = [
    ButtonEntityDescription(
        key="big_flush",
        name="大冲水",
        command=Command.DACHONG,
    ),
    ButtonEntityDescription(
        key="small_flush",
        name="小冲水",
        command=Command.XIAOCHONG,
    ),
    ButtonEntityDescription(
        key="factory_reset",
        name="恢复出厂设置",
        command=Command.FUYUAN,
    ),
]

# ============================================================================
# 选择定义
# ============================================================================

SELECTS = [
    SelectEntityDescription(
        key="water_temperature",
        name="水温",
        icon="mdi:water-thermometer",
        command=Command.SHUIWEN,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
        state_key="water_temp_code",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="seat_temperature",
        name="座温",
        icon="mdi:seat",
        command=Command.ZUOWEN,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
        state_key="seat_temp_code",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="wind_temperature",
        name="风温",
        icon="mdi:air-conditioner",
        command=Command.QIANGWEN,
        options=["off", "40", "45", "50"],
        options_map={"off": 0, "40": 1, "45": 2, "50": 3},
        state_key="wind_temp_code",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="water_level",
        name="水量",
        icon="mdi:water",
        command=Command.SHUILIANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
        state_key="water_level_code",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="air_level",
        name="热风档位",
        icon="mdi:air-filter",
        command=Command.QIANGDANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
        state_key="air_level_code",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="light_brightness",
        name="灯光亮度",
        icon="mdi:brightness-6",
        command=Command.GUANGDANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
        state_key="light_brightness_code",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="radar_sensitivity",
        name="雷达灵敏度",
        icon="mdi:radar",
        command=Command.CHUANGAN,
        options=["low", "medium", "high"],
        options_map={"low": 1, "medium": 2, "high": 3},
        entity_category=EntityCategory.CONFIG,
    ),
]

# ============================================================================
# 传感器定义
# ============================================================================

SENSORS = [
    SensorEntityDescription(
        key="device_address",
        name="设备地址",
    ),
    SensorEntityDescription(
        key="rssi",
        name="信号强度",
        unit="dBm",
        device_class="signal_strength",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="air_percentage",
        name="热风百分比",
        unit="%",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="water_percentage",
        name="水量百分比",
        unit="%",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="radar_level",
        name="雷达等级",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="cover_close_time",
        name="盖板关闭时间",
        unit="s",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="cover_flip_intensity",
        name="盖板翻转强度",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="ring_flip_intensity",
        name="座圈翻转强度",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="cover_close_intensity",
        name="盖板关闭强度",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="ring_close_intensity",
        name="座圈关闭强度",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="bubble_level",
        name="气泡等级",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="big_flush_water",
        name="大冲水量",
        unit="s",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="small_flush_water",
        name="小冲水量",
        unit="s",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="small_flush_up",
        name="小冲上冲时间",
        unit="s",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="foot_sensor_distance",
        name="脚感应距离",
        unit="cm",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="sterilization_time",
        name="杀菌时间",
        unit="min",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="water_pressure",
        name="水压",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="ambient_light_brightness",
        name="氛围灯亮度",
        unit="%",
        state_class="measurement",
    ),
]

# ============================================================================
# 二进制传感器定义
# ============================================================================

BINARY_SENSORS = [
    EntityDescription(
        key="connection",
        name="已连接",
        device_class="connectivity",
    ),
]

# ============================================================================
# 配置键
# ============================================================================

CONF_DEVICE_ADDRESS = "device_address"
CONF_DEVICE_NAME = "device_name"
CONF_AUTO_CONNECT = "auto_connect"  # 是否自动连接

# ============================================================================
# 状态键
# ============================================================================

# 基础状态键（来自 Type 01 包）
STATE_FLUSH_ENABLED = "flush_enabled"
STATE_SEAT_ENABLED = "seat_enabled"
STATE_BUBBLE_ENABLED = "bubble_enabled"
STATE_AIR_ENABLED = "air_enabled"
STATE_RADAR_ENABLED = "radar_enabled"
STATE_VOICE_ENABLED = "voice_enabled"
STATE_SENSORS_ENABLED = "sensors_enabled"
STATE_LIGHTS_ENABLED = "lights_enabled"

# 新增状态键（来自 Type 01 包扩展字段）
STATE_WATER_SURFACE_ENABLED = "water_surface_enabled"
STATE_AUTO_AMBIENT_LIGHT_ENABLED = "auto_ambient_light_enabled"
STATE_AMBIENT_LIGHT_ENABLED = "ambient_light_enabled"
STATE_BREATHING_LIGHT_ENABLED = "breathing_light_enabled"
STATE_RUNBI_ENABLED = "runbi_enabled"
STATE_AUTO_FLUSH_ENABLED = "auto_flush_enabled"
STATE_VIRTUAL_SEAT_ENABLED = "virtual_seat_enabled"
STATE_BIG_FLUSH_MODE = "big_flush_mode"

# 温度状态键（来自 Type 02 包）- 根据参考实现更新
STATE_WATER_LEVEL = "water_level"
STATE_WATER_TEMP_VALUE = "water_temp_value"
STATE_WIND_LEVEL = "wind_level"
STATE_WIND_TEMP_VALUE = "wind_temp_value"
STATE_SEAT_LEVEL = "seat_level"
STATE_SEAT_TEMP_VALUE = "seat_temp_value"
STATE_WATER_PRESSURE = "water_pressure"
STATE_AMBIENT_LIGHT_BRIGHTNESS = "ambient_light_brightness"

# 百分比状态键（来自 Type 03 包）
STATE_AIR_PERCENTAGE = "air_percentage"
STATE_WATER_PERCENTAGE = "water_percentage"
STATE_RADAR_LEVEL = "radar_level"
STATE_COVER_CLOSE_TIME = "cover_close_time"

# 强度状态键（来自 Type 04 包）- 根据参考实现更新
STATE_COVER_FLIP_INTENSITY = "cover_flip_intensity"
STATE_RING_FLIP_INTENSITY = "ring_flip_intensity"
STATE_COVER_CLOSE_INTENSITY = "cover_close_intensity"
STATE_RING_CLOSE_INTENSITY = "ring_close_intensity"  # 新增

# 冲水参数状态键（来自 Type 05 包）- 根据参考实现更新
STATE_BUBBLE_LEVEL = "bubble_level"
STATE_BIG_FLUSH_DOWN = "big_flush_down"
STATE_BIG_FLUSH_WATER = "big_flush_water"
STATE_SMALL_FLUSH_UP = "small_flush_up"
STATE_SMALL_FLUSH_WATER = "small_flush_water"
STATE_SMALL_FLUSH_DOWN = "small_flush_down"

# 传感器状态键（来自 Type 06 包）- 根据参考实现更新
STATE_FOOT_SENSOR_ENABLED = "foot_sensor_enabled"  # 改为 int (0-15) 而非 bool
STATE_FOOT_SENSOR_DISTANCE = "foot_sensor_distance"
STATE_STERILIZATION_TIME = "sterilization_time"

# 连接状态
STATE_RSSI = "rssi"
STATE_CONNECTED = "connected"

# ============================================================================
# 服务
# ============================================================================

SERVICE_SEND_COMMAND = "send_command"

# ============================================================================
# 属性
# ============================================================================

ATTR_LAST_UPDATE = "last_update"
ATTR_COMMAND_SENT = "command_sent"
ATTR_PACKET_RECEIVED = "packet_received"
