"""VCX-Knob 集成的常量定义"""

from dataclasses import dataclass
from enum import StrEnum

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

# ============================================================================
# BLE UUID
# ============================================================================
# VCX-Knob 设备的服务 UUID
BLE_SERVICE_UUID = "0000FFF0-0000-1000-8000-00805F9B34FB"

# 写特征 UUID - 用于发送命令
BLE_WRITE_CHARACTERISTIC_UUID = "0000FFF1-0000-1000-8000-00805F9B34FB"

# 通知特征 UUID - 用于接收状态更新
BLE_NOTIFY_CHARACTERISTIC_UUID = "0000FFF2-0000-1000-8000-00805F9B34FB"

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
    """VCX-Knob 设备的命令码"""

    # 查询命令
    ZHUANGTAI = "00"  # 查询状态

    # 冲水命令
    DACHONG = "07"  # 大冲水
    XIAOCHONG = "17"  # 小冲水

    # 座圈命令
    ZUOWEN = "30"  # 座温
    ZUOYI = "31"  # 座椅位置

    # 水温命令
    SHUIWEN = "10"  # 水温
    SHUILIANG = "11"  # 水量

    # 热风命令
    QIANGWEN = "20"  # 热风温度
    QIANGDANG = "21"  # 热风档位

    # 灯光命令
    GUANGDENG = "50"  # 夜灯
    GUANGDANG = "51"  # 灯光亮度

    # 自动命令
    ZIDONG = "60"  # 自动模式

    # 气泡命令
    PAOMO = "70"  # 气泡模式

    # 语音命令
    YUYIN = "80"  # 语音控制

    # 传感器命令
    CHUANGAN = "90"  # 传感器设置

    # 系统命令
    FUYUAN = "A0"  # 恢复出厂设置


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
    entity_category: str | None = None
    translation_key: str | None = None


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


@dataclass(frozen=True)
class ButtonEntityDescription(EntityDescription):
    """按钮实体的描述"""

    command: str
    data_byte: str = "00"


@dataclass(frozen=True)
class SelectEntityDescription(EntityDescription):
    """选择实体的描述"""

    command: str
    options: list[str]
    options_map: dict[str, int]  # 选项值到数据字节的映射


# ============================================================================
# 开关定义
# ============================================================================

SWITCHES = [
    SwitchEntityDescription(
        key="flush",
        name="冲水",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="seat",
        name="座圈",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="bubble",
        name="气泡",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="air",
        name="热风",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="radar",
        name="雷达",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="voice",
        name="语音控制",
        entity_category="config",
        command=Command.YUYIN,
    ),
    SwitchEntityDescription(
        key="sensor",
        name="传感器",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="auto_mode",
        name="自动模式",
        entity_category="config",
        command=Command.ZIDONG,
    ),
    SwitchEntityDescription(
        key="night_light",
        name="夜灯",
        entity_category="config",
        command=Command.GUANGDENG,
    ),
    SwitchEntityDescription(
        key="foot_sensor",
        name="脚感应",
        entity_category="config",
    ),
    SwitchEntityDescription(
        key="sterilization",
        name="杀菌",
        entity_category="config",
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
        command=Command.SHUIWEN,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
    ),
    SelectEntityDescription(
        key="seat_temperature",
        name="座温",
        command=Command.ZUOWEN,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
    ),
    SelectEntityDescription(
        key="wind_temperature",
        name="风温",
        command=Command.QIANGWEN,
        options=["off", "40", "45", "50"],
        options_map={"off": 0, "40": 1, "45": 2, "50": 3},
    ),
    SelectEntityDescription(
        key="water_level",
        name="水量",
        command=Command.SHUILIANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
    ),
    SelectEntityDescription(
        key="air_level",
        name="热风档位",
        command=Command.QIANGDANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
    ),
    SelectEntityDescription(
        key="light_brightness",
        name="灯光亮度",
        command=Command.GUANGDANG,
        options=["off", "low", "medium", "high"],
        options_map={"off": 0, "low": 1, "medium": 2, "high": 3},
    ),
    SelectEntityDescription(
        key="radar_sensitivity",
        name="雷达灵敏度",
        command=Command.CHUANGAN,
        options=["low", "medium", "high"],
        options_map={"low": 1, "medium": 2, "high": 3},
    ),
]

# ============================================================================
# 传感器定义
# ============================================================================

SENSORS = [
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
        key="bubble_level",
        name="气泡等级",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="big_flush_timing",
        name="大冲水时间",
        unit="s",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="small_flush_timing",
        name="小冲水时间",
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

# 温度状态键（来自 Type 02 包）
STATE_WATER_TEMP_CODE = "water_temp_code"
STATE_WATER_TEMP_VALUE = "water_temp_value"
STATE_WIND_TEMP_CODE = "wind_temp_code"
STATE_WIND_TEMP_VALUE = "wind_temp_value"
STATE_SEAT_TEMP_CODE = "seat_temp_code"
STATE_SEAT_TEMP_VALUE = "seat_temp_value"
STATE_WATER_LEVEL_CODE = "water_level_code"
STATE_AIR_LEVEL_CODE = "air_level_code"
STATE_LIGHT_BRIGHTNESS_CODE = "light_brightness_code"

# 百分比状态键（来自 Type 03 包）
STATE_AIR_PERCENTAGE = "air_percentage"
STATE_WATER_PERCENTAGE = "water_percentage"
STATE_RADAR_LEVEL = "radar_level"
STATE_COVER_CLOSE_TIME = "cover_close_time"

# 强度状态键（来自 Type 04 包）
STATE_COVER_FLIP_INTENSITY = "cover_flip_intensity"
STATE_RING_FLIP_INTENSITY = "ring_flip_intensity"
STATE_COVER_CLOSE_INTENSITY = "cover_close_intensity"

# 冲水参数状态键（来自 Type 05 包）
STATE_BUBBLE_LEVEL = "bubble_level"
STATE_BIG_FLUSH_TIMING = "big_flush_timing"
STATE_SMALL_FLUSH_TIMING = "small_flush_timing"

# 传感器状态键（来自 Type 06 包）
STATE_FOOT_SENSOR_ENABLED = "foot_sensor_enabled"
STATE_FOOT_SENSOR_DISTANCE = "foot_sensor_distance"
STATE_STERILIZATION_ENABLED = "sterilization_enabled"
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
