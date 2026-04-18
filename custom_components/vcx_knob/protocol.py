"""VCX-Knob BLE 协议实现

此模块处理与 VCX-Knob 智能马桶设备通过蓝牙低功耗通信的所有协议相关操作。

协议规范:
    命令帧: AA 08 02 {cmd} {d1} {d2} {d3} {checksum}
    状态帧: AA 08 88 {type} {data1} {data2} {data3} {checksum}

    - AA: 帧头字节 (0xAA)
    - 08: 长度字节 (固定为 0x08)
    - 02: 命令类型（用于发送命令）或 88: 状态类型（用于接收）
    - cmd: 命令码（例如 "07" 表示大冲水）
    - d1, d2, d3: 数据字节（通常 d1 携带主要参数）
    - checksum: 所有字节之和与 0xFF 的与运算结果
"""

import logging
from typing import Final

from .const import (
    PROTOCOL_CMD_TYPE,
    PROTOCOL_HEADER,
    PROTOCOL_LENGTH,
    PROTOCOL_STATUS_TYPE,
    StatusPacketType,
    WATER_SEAT_TEMPERATURE_MAP,
    WIND_TEMPERATURE_MAP,
)

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 协议常量
# ============================================================================

PACKET_HEADER_SIZE: Final = 3  # AA 08 02 或 AA 08 88
PACKET_TOTAL_SIZE: Final = 8   # 一个数据包的总字节数
CHECKSUM_MASK: Final = 0xFF

STATUS_BUFFER_MAX_SIZE: Final = 100  # 防止畸形数据导致内存泄漏


# ============================================================================
# 协议函数
# ============================================================================

def build_command(
    cmd: str,
    d1: int | str = 0,
    d2: int | str = 0,
    d3: int | str = 0,
) -> bytes:
    """构建用于发送给设备的命令帧

    Args:
        cmd: 命令码（2字符十六进制字符串，例如 "07" 表示大冲水）
        d1: 第一个数据字节 (0-255)
        d2: 第二个数据字节 (0-255)
        d3: 第三个数据字节 (0-255)

    Returns:
        完整的命令帧（字节），可通过 BLE 发送

    示例:
        >>> build_command("07", 0, 0, 0)  # 大冲水命令
        b'\\xaa\\x08\\x02\\x07\\x00\\x00\\x00\\xb1'
    """
    # 将参数转换为整数
    d1_int = _to_int(d1)
    d2_int = _to_int(d2)
    d3_int = _to_int(d3)

    # 将命令十六进制字符串转换为整数
    cmd_int = int(cmd, 16)

    # 计算校验和: (AA + 08 + 02 + cmd + d1 + d2 + d3) & 0xFF
    checksum = (
        PROTOCOL_HEADER
        + PROTOCOL_LENGTH
        + PROTOCOL_CMD_TYPE
        + cmd_int
        + d1_int
        + d2_int
        + d3_int
    ) & CHECKSUM_MASK

    # 构建命令帧
    frame = bytes([
        PROTOCOL_HEADER,
        PROTOCOL_LENGTH,
        PROTOCOL_CMD_TYPE,
        cmd_int,
        d1_int,
        d2_int,
        d3_int,
        checksum,
    ])

    _LOGGER.debug(
        "构建命令: %s (命令=%s, d1=%d, d2=%d, d3=%d, 校验和=0x%02X)",
        frame.hex().upper(),
        cmd,
        d1_int,
        d2_int,
        d3_int,
        checksum,
    )

    return frame


def parse_status_packet(data: bytes) -> dict | None:
    """解析从设备接收的状态数据包

    Args:
        data: 从 BLE 通知接收的原始字节

    Returns:
        解析后的状态数据字典，如果数据包无效则返回 None
        结构:
        {
            "type": "01" | "02" | "03" | "04" | "05" | "06",
            "data1": int,
            "data2": int,
            "data3": int,
            "checksum": int,
        }

    示例:
        >>> parse_status_packet(b'\\xaa\\x08\\x88\\x01\\x12\\x34\\x56\\xd3')
        {'type': '01', 'data1': 18, 'data2': 52, 'data3': 86, 'checksum': 211}
    """
    if len(data) != PACKET_TOTAL_SIZE:
        _LOGGER.warning(
            "无效的数据包长度: 预期 %d，实际 %d",
            PACKET_TOTAL_SIZE,
            len(data),
        )
        return None

    # 验证帧头
    if data[0] != PROTOCOL_HEADER:
        _LOGGER.warning("无效的数据包头: 0x%02X", data[0])
        return None

    # 验证长度
    if data[1] != PROTOCOL_LENGTH:
        _LOGGER.warning("无效的数据包长度字节: 0x%02X", data[1])
        return None

    # 验证数据包类型
    if data[2] != PROTOCOL_STATUS_TYPE:
        _LOGGER.warning("无效的数据包类型: 0x%02X (预期 0x88)", data[2])
        return None

    # 提取数据包字段
    packet_type = f"{data[3]:02X}"
    data1 = data[4]
    data2 = data[5]
    data3 = data[6]
    checksum = data[7]

    # 验证校验和
    expected_checksum = (
        PROTOCOL_HEADER
        + PROTOCOL_LENGTH
        + PROTOCOL_STATUS_TYPE
        + data[3]
        + data1
        + data2
        + data3
    ) & CHECKSUM_MASK

    if checksum != expected_checksum:
        _LOGGER.warning(
            "无效的校验和: 预期 0x%02X，实际 0x%02X",
            expected_checksum,
            checksum,
        )
        return None

    parsed = {
        "type": packet_type,
        "data1": data1,
        "data2": data2,
        "data3": data3,
        "checksum": checksum,
    }

    _LOGGER.debug("解析状态数据包: %s", parsed)
    return parsed


def decode_type_01_packet(data1: int, data2: int, data3: int) -> dict:
    """解码 Type 01 数据包: 基础状态

    data1 的位布局 (第4个字节):
    - 第7位: 冲水启用
    - 第6位: 座圈启用
    - 第5位: 气泡启用
    - 第4位: 热风启用
    - 第3位: 雷达启用
    - 第2位: 语音启用
    - 第1位: 传感器启用
    - 第0位: 节能启用

    data2 的位布局 (第5个字节):
    - 第7位: 水面状态
    - 第6位: 自动氛围灯状态
    - 第5位: 氛围灯状态
    - 第4位: 呼吸氛围灯状态
    - 第3-0位: 保留

    data3 的位布局 (第6个字节):
    - 第7位: 润壁状态
    - 第6位: 罐自动冲状态
    - 第5位: 虚拟坐座状态
    - 第4位: 保留
    - 第3-0位: 大冲水模式 (0=不水, 1=下冲, 2=上冲, 3=其他)

    Args:
        data1: 包含启用/禁用标志的第一个数据字节
        data2: 第二个数据字节
        data3: 第三个数据字节

    Returns:
        包含解码状态标志的字典
    """
    # data1 的 8 个位
    chongshui_status = bool(data1 & 0x80)  # 冲水状态
    zhuozuo_status = bool(data1 & 0x40)    # 座座状态
    paopao_status = bool(data1 & 0x20)     # 气泡状态
    kongqi_status = bool(data1 & 0x10)     # 空气状态
    leida_status = bool(data1 & 0x08)      # 雷达状态
    yuyin_status = bool(data1 & 0x04)      # 语音状态
    jiaogan_status = bool(data1 & 0x02)    # 脚感状态
    jieneng_status = bool(data1 & 0x01)    # 节能状态

    # data2 的 8 个位
    shuimian_status = bool(data2 & 0x80)            # 水面状态
    autofenweideng_status = bool(data2 & 0x40)      # 自动氛围灯状态
    fenweideng_status = bool(data2 & 0x20)          # 氛围灯状态
    huxifenweideng_status = bool(data2 & 0x10)      # 呼吸氛围灯状态

    # data3 的位
    runbi_status = bool(data3 & 0x80)               # 润壁状态
    guanautochong_status = bool(data3 & 0x40)       # 罐自动冲状态
    xunizhuozuo_status = bool(data3 & 0x20)         # 虚拟坐座状态
    dachong_mode = data3 & 0x0F                     # 大冲水模式

    return {
        "flush_enabled": chongshui_status,
        "seat_enabled": zhuozuo_status,
        "bubble_enabled": paopao_status,
        "air_enabled": kongqi_status,
        "radar_enabled": leida_status,
        "voice_enabled": yuyin_status,
        "sensors_enabled": jiaogan_status,
        "lights_enabled": jieneng_status,
        # 新增字段
        "water_surface_enabled": shuimian_status,
        "auto_ambient_light_enabled": autofenweideng_status,
        "ambient_light_enabled": fenweideng_status,
        "breathing_light_enabled": huxifenweideng_status,
        "runbi_enabled": runbi_status,
        "auto_flush_enabled": guanautochong_status,
        "virtual_seat_enabled": xunizhuozuo_status,
        "big_flush_mode": dachong_mode,
    }


def decode_type_02_packet(data1: int, data2: int, data3: int) -> dict:
    """解码 Type 02 数据包: 温度设置

    字节布局 (根据参考实现):
    - data1: [000][水量档位(3位)][00][风温档位(3位)]
    - data2: [000][座温档位(3位)][00][水压档位(3位)]
    - data3: [0000][氛围灯亮度(4位)] - 值需要乘以10

    温度码 (通过 levelToTemp 映射):
    - 水/座: 0=关闭, 1=34°C, 2=37°C, 3=40°C
    - 风: 0=关闭, 1=40°C, 2=45°C, 3=50°C

    Args:
        data1: 包含水量档位(高3位)和风温档位(中间3位)的第一个数据字节
        data2: 包含座温档位(高3位)和水压档位(中间3位)的第二个数据字节
        data3: 包含氛围灯亮度(低4位)的第三个数据字节

    Returns:
        包含解码温度设置的字典
    """
    # 从 data1 提取 (参考: parseTemperatureStatus)
    water_level = (data1 >> 5) & 0x07  # 高3位 (bits 5-7)
    wind_level = (data1 >> 2) & 0x07   # 中间3位 (bits 2-4)

    # 从 data2 提取 (参考: parseTemperatureStatus)
    seat_level = (data2 >> 5) & 0x07   # 高3位 (bits 5-7)
    water_pressure = (data2 >> 2) & 0x07  # 中间3位 (bits 2-4)

    # 从 data3 提取 (参考: parseTemperatureStatus)
    ambient_light_brightness = (data3 >> 4) & 0x0F  # 高4位 (bits 4-7), 需要乘以10

    # 根据档位映射到温度值 (参考: levelToTemp)
    water_temp_value = WATER_SEAT_TEMPERATURE_MAP.get(water_level, 0)
    seat_temp_value = WATER_SEAT_TEMPERATURE_MAP.get(seat_level, 0)
    wind_temp_value = WIND_TEMPERATURE_MAP.get(wind_level, 0)

    return {
        "water_level": water_level,
        "water_temp_value": water_temp_value,
        "wind_level": wind_level,
        "wind_temp_value": wind_temp_value,
        "seat_level": seat_level,
        "seat_temp_value": seat_temp_value,
        "water_pressure": water_pressure,
        "ambient_light_brightness": ambient_light_brightness * 10,  # 值需要乘以10
    }


def decode_type_03_packet(data1: int, data2: int, data3: int) -> dict:
    """解码 Type 03 数据包: 百分比值

    字节布局:
    - data1: 热风百分比 (0-100)
    - data2: 水量百分比 (0-100)
    - data3: [雷达等级(4位), 盖板关闭时间(4位)]

    Args:
        data1: 热风百分比值
        data2: 水量百分比值
        data3: 雷达等级和盖板关闭时间（半字节）

    Returns:
        包含解码百分比的字典
    """
    cover_close_time = data3 & 0x0F  # 低 4 位 (参考: byte3Bits.substring(0, 4))
    radar_level = (data3 >> 4) & 0x0F  # 高 4 位 (参考: byte3Bits.substring(4, 8))

    return {
        "air_percentage": data1,
        "water_percentage": data2,
        "radar_level": radar_level,
        "cover_close_time": cover_close_time,
    }


def decode_type_04_packet(data1: int, data2: int, data3: int) -> dict:
    """解码 Type 04 数据包: 强度设置

    字节布局 (根据参考实现):
    - data1: [盖板翻转强度(4位), 座圈翻转强度(4位)]
    - data2: [盖板关闭强度(4位), 座圈关闭强度(4位)]
    - data3: 未使用

    Args:
        data1: 包含盖板翻转强度(高4位)和座圈翻转强度(低4位)的第一个数据字节
        data2: 包含盖板关闭强度(高4位)和座圈关闭强度(低4位)的第二个数据字节
        data3: 未使用的第三个数据字节

    Returns:
        包含解码强度值的字典
    """
    # 参考: parseIntensityStatus
    cover_flip_intensity = (data1 >> 4) & 0x0F  # data1 高4位 (byte1Bits.substring(4, 8))
    ring_flip_intensity = data1 & 0x0F            # data1 低4位 (byte1Bits.substring(0, 4))
    cover_close_intensity = (data2 >> 4) & 0x0F  # data2 高4位 (byte2Bits.substring(4, 8))
    ring_close_intensity = data2 & 0x0F            # data2 低4位 (byte2Bits.substring(0, 4))

    return {
        "cover_flip_intensity": cover_flip_intensity,
        "ring_flip_intensity": ring_flip_intensity,
        "cover_close_intensity": cover_close_intensity,
        "ring_close_intensity": ring_close_intensity,  # 新增字段
    }


def decode_type_05_packet(data1: int, data2: int, data3: int) -> dict:
    """解码 Type 05 数据包: 冲水参数

    字节布局 (根据参考实现):
    - data1: [气泡用量档位(4位), 大冲下冲(4位)]
    - data2: [大冲水量(4位), 小冲上冲(4位)]
    - data3: [小冲水量(4位), 小冲下冲(4位)]

    Args:
        data1: 包含气泡用量档位(高4位)和大冲下冲(低4位)的第一个数据字节
        data2: 包含大冲水量(高4位)和小冲上冲(低4位)的第二个数据字节
        data3: 包含小冲水量(高4位)和小冲下冲(低4位)的第三个数据字节

    Returns:
        包含解码冲水参数的字典
    """
    # 参考: parseFlushStatus
    bubble_level = (data1 >> 4) & 0x0F      # 高4位: 气泡用量档位
    big_flush_down = data1 & 0x0F           # 低4位: 大冲下冲

    big_flush_water = (data2 >> 4) & 0x0F  # 高4位: 大冲水量
    small_flush_up = data2 & 0x0F           # 低4位: 小冲上冲

    small_flush_water = (data3 >> 4) & 0x0F  # 高4位: 小冲水量
    small_flush_down = data3 & 0x0F           # 低4位: 小冲下冲

    return {
        "bubble_level": bubble_level,
        "big_flush_down": big_flush_down,     # 修正: 原来叫 big_flush_timing
        "big_flush_water": big_flush_water,   # 修正: 原来叫 big_flush_no_water
        "small_flush_up": small_flush_up,     # 修正: 原来叫 small_flush_timing
        "small_flush_water": small_flush_water,  # 修正: 原来叫 small_flush_no_water
        "small_flush_down": small_flush_down,
    }


def decode_type_06_packet(data1: int, data2: int, data3: int) -> dict:
    """解码 Type 06 数据包: 传感器设置

    字节布局 (根据参考实现):
    - data1: [脚感启用档位(4位), 脚感距离档位(4位)]
    - data2: 未使用
    - data3: [0000][杀菌时间档位(4位)]

    Args:
        data1: 包含脚感启用档位(高4位)和脚感距离档位(低4位)的第一个数据字节
        data2: 未使用的第二个数据字节
        data3: 包含杀菌时间档位(高4位)的第三个数据字节

    Returns:
        包含解码传感器设置的字典
    """
    # 参考: parseSensorStatus
    foot_sensor_enabled = (data1 >> 4) & 0x0F  # data1 高4位: 脚感启用档位 (0-15)
    foot_sensor_distance = data1 & 0x0F         # data1 低4位: 脚感距离档位 (0-15)
    sterilization_time = (data3 >> 4) & 0x0F   # data3 高4位: 杀菌时间档位

    return {
        "foot_sensor_enabled": foot_sensor_enabled,  # 改为 int (0-15) 而非 bool
        "foot_sensor_distance": foot_sensor_distance,
        "sterilization_time": sterilization_time,
    }


# ============================================================================
# Type 01 解码器映射
# ============================================================================

PACKET_DECODERS = {
    StatusPacketType.TYPE_01: decode_type_01_packet,
    StatusPacketType.TYPE_02: decode_type_02_packet,
    StatusPacketType.TYPE_03: decode_type_03_packet,
    StatusPacketType.TYPE_04: decode_type_04_packet,
    StatusPacketType.TYPE_05: decode_type_05_packet,
    StatusPacketType.TYPE_06: decode_type_06_packet,
}


def decode_status_packet(packet: dict) -> dict | None:
    """将解析后的状态数据包解码为人类可读的值

    Args:
        packet: 从 parse_status_packet() 解析的数据包

    Returns:
        包含解码状态值的字典，如果数据包类型未知则返回 None

    示例:
        >>> packet = {'type': '01', 'data1': 0xFF, 'data2': 0, 'data3': 0, 'checksum': 123}
        >>> decode_status_packet(packet)
        {'flush_enabled': True, 'seat_enabled': True, ...}
    """
    packet_type = packet.get("type")

    if packet_type not in PACKET_DECODERS:
        _LOGGER.warning("未知的数据包类型: %s", packet_type)
        return None

    decoder = PACKET_DECODERS[packet_type]
    decoded = decoder(
        packet["data1"],
        packet["data2"],
        packet["data3"],
    )

    _LOGGER.debug("解码 %s 数据包: %s", packet_type, decoded)
    return decoded


# ============================================================================
# 工具函数
# ============================================================================

def _to_int(value: int | str) -> int:
    """将值转换为整数

    Args:
        value: 要转换的整数或字符串

    Returns:
        整数值

    Raises:
        ValueError: 如果无法将值转换为整数
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"无法将 {type(value)} 转换为 int")


def format_command_log(cmd: str, d1: int, d2: int, d3: int) -> str:
    """格式化命令用于日志记录

    Args:
        cmd: 命令码
        d1: 第一个数据字节
        d2: 第二个数据字节
        d3: 第三个数据字节

    Returns:
        用于日志记录的格式化字符串
    """
    return f"命令={cmd}, d1={d1:02X}, d2={d2:02X}, d3={d3:02X}"
