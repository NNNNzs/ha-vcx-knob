"""VCX-Knob 设备的 BLE 协调器

此模块提供协调器，用于管理通过蓝牙低功耗与 VCX-Knob 智能马桶设备的通信。

协调器扩展了 DataUpdateCoordinator 以提供自动状态轮询和
Home Assistant 实体的状态管理。

该协调器的数据包含来自所有状态包的合并状态:
{
    "connected": bool,
    "paired": bool,
    "rssi": int | None,
    "device_address": str,
    # Type 01: 基础状态
    "flush_enabled": bool,
    "seat_enabled": bool,
    "bubble_enabled": bool,
    "air_enabled": bool,
    "radar_enabled": bool,
    "voice_enabled": bool,
    "sensors_enabled": bool,
    "lights_enabled": bool,
    # Type 02: 温度（根据参考实现更新）
    "water_level": int,
    "water_temp_value": int,
    "wind_level": int,
    "wind_temp_value": int,
    "seat_level": int,
    "seat_temp_value": int,
    "water_pressure": int,
    "ambient_light_brightness": int,
    # Type 03: 百分比
    "air_percentage": int,
    "water_percentage": int,
    "radar_level": int,
    "cover_close_time": int,
    # Type 04: 强度（根据参考实现更新）
    "cover_flip_intensity": int,
    "ring_flip_intensity": int,
    "cover_close_intensity": int,
    "ring_close_intensity": int,
    # Type 05: 冲水参数（根据参考实现更新）
    "bubble_level": int,
    "big_flush_down": int,
    "big_flush_water": int,
    "small_flush_up": int,
    "small_flush_water": int,
    "small_flush_down": int,
    # Type 06: 传感器（根据参考实现更新）
    "foot_sensor_enabled": int,
    "foot_sensor_distance": int,
    "sterilization_time": int,
}
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Final

import voluptuous as vol
from bleak import BleakClient, BleakError
from bleak.exc import BleakDBusError
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_get_scanner,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BLE_NOTIFY_CHARACTERISTIC_UUID,
    BLE_SERVICE_UUID,
    BLE_WRITE_CHARACTERISTIC_UUID,
    BLE_DEVICE_NAME_FILTER,
    CONF_AUTO_CONNECT,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    DEFAULT_AUTO_CONNECT,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_SCAN_TIMEOUT,
    DEFAULT_STATUS_POLL_INTERVAL,
    DOMAIN,
)
from .protocol import build_command, decode_status_packet, parse_status_packet

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 常量
# ============================================================================

# 重试配置
CONNECT_RETRY_COUNT: Final = 3
CONNECT_RETRY_DELAY: Final = 5  # 秒
DISCONNECT_COOLDOWN: Final = 10  # 秒

# 状态轮询
MIN_POLL_INTERVAL: Final = 10  # 秒
MAX_POLL_INTERVAL: Final = 300  # 秒

# 连接超时
CONNECTION_TIMEOUT: Final = DEFAULT_CONNECTION_TIMEOUT


# ============================================================================
# 异常
# ============================================================================

class VCXKnobConnectionError(Exception):
    """当设备连接失败时抛出"""

    def __init__(self, message: str, retryable: bool = True) -> None:
        """初始化异常

        Args:
            message: 错误消息
            retryable: 错误是否可重试
        """
        super().__init__(message)
        self.retryable = retryable


class VCXKnobNotFoundError(VCXKnobConnectionError):
    """扫描期间找不到设备时抛出"""

    def __init__(self, address: str) -> None:
        """初始化异常

        Args:
            address: 未找到的设备地址
        """
        super().__init__(f"设备 {address} 未找到", retryable=True)


# ============================================================================
# BLE 客户端管理器
# ============================================================================

class VCXKnobBLEClient:
    """管理 VCX-Knob 设备的 BLE 连接和通信

    此类处理:
    - 使用 bleak 进行低级 BLE 连接
    - 命令传输
    - 状态包接收和缓冲
    - 连接状态管理
    """

    def __init__(
        self,
        address: str,
        name: str,
        notification_callback: Callable[[bytes], None],
    ) -> None:
        """初始化 BLE 客户端

        Args:
            address: BLE 设备地址（Linux 上为 MAC，macOS 上为 UUID）
            name: 设备名称（用于日志记录）
            notification_callback: 接收通知的回调
        """
        self._address = address
        self._name = name

        def _disconnected_callback(client: BleakClient) -> None:
            _LOGGER.warning("设备 %s 已断开连接", address)
            self._is_connected = False

        self._client = BleakClient(
            address,
            disconnected_callback=_disconnected_callback,
        )
        self._notification_callback = notification_callback
        self._status_buffer: list[str] = []
        self._is_connected = False
        self._disconnect_time: float | None = None
        self._lock = asyncio.Lock()

    @property
    def address(self) -> str:
        """获取设备地址"""
        return self._address

    @property
    def name(self) -> str:
        """获取设备名称"""
        return self._name

    @property
    def is_connected(self) -> bool:
        """检查设备是否已连接"""
        return self._is_connected and self._client.is_connected

    @property
    def rssi(self) -> int | None:
        """获取当前 RSSI 值"""
        if not self.is_connected:
            return None

        # 尝试从蓝牙适配器获取 RSSI
        try:
            service_info = bluetooth.async_get_service_info_from_name(
                self._address, self._name
            )
            if service_info:
                return service_info.rssi
        except Exception:
            pass

        return None

    async def connect(self) -> None:
        """连接到 BLE 设备

        Raises:
            VCXKnobConnectionError: 如果连接失败
        """
        async with self._lock:
            if self.is_connected:
                _LOGGER.debug("已连接到 %s", self._address)
                return

            # 检查冷却时间
            if self._disconnect_time:
                cooldown_remaining = DISCONNECT_COOLDOWN - (
                    asyncio.get_event_loop().time() - self._disconnect_time
                )
                if cooldown_remaining > 0:
                    _LOGGER.debug(
                        "在断开冷却期内，等待 %.1f 秒",
                        cooldown_remaining,
                    )
                    await asyncio.sleep(cooldown_remaining)

            _LOGGER.info("正在连接到 %s (%s)", self._name, self._address)

            try:
                async with asyncio.timeout(CONNECTION_TIMEOUT):
                    await self._client.connect()

                # 验证服务 UUID 存在
                services = self._client.services
                if BLE_SERVICE_UUID not in str(services):
                    _LOGGER.warning(
                        "在设备服务中未找到服务 UUID %s: %s",
                        BLE_SERVICE_UUID,
                        services,
                    )

                # 订阅通知
                await self._client.start_notify(
                    BLE_NOTIFY_CHARACTERISTIC_UUID,
                    self._notification_handler,
                )

                self._is_connected = True
                self._disconnect_time = None
                self._status_buffer.clear()

                _LOGGER.info("已连接到 %s (%s)", self._name, self._address)

            except asyncio.TimeoutError as err:
                raise VCXKnobConnectionError(
                    f"连接到 {self._address} 超时",
                    retryable=True,
                ) from err
            except BleakDBusError as err:
                raise VCXKnobConnectionError(
                    f"连接到 {self._address} 时发生 DBus 错误: {err}",
                    retryable=True,
                ) from err
            except BleakError as err:
                raise VCXKnobConnectionError(
                    f"无法连接到 {self._address}: {err}",
                    retryable=False,
                ) from err

    async def disconnect(self) -> None:
        """从 BLE 设备断开连接"""
        async with self._lock:
            if not self.is_connected:
                return

            _LOGGER.info("正在从 %s (%s) 断开连接", self._name, self._address)

            try:
                # 取消订阅通知
                try:
                    await self._client.stop_notify(BLE_NOTIFY_CHARACTERISTIC_UUID)
                except Exception:
                    pass

                await self._client.disconnect()
            except Exception as err:
                _LOGGER.warning("断开连接期间出错: %s", err)
            finally:
                self._is_connected = False
                self._disconnect_time = asyncio.get_event_loop().time()

                _LOGGER.info("已从 %s 断开连接", self._address)

    async def send_command(
        self,
        cmd: str,
        d1: int = 0,
        d2: int = 0,
        d3: int = 0,
    ) -> None:
        """向设备发送命令

        Args:
            cmd: 命令码（例如 "07" 表示大冲水）
            d1: 第一个数据字节
            d2: 第二个数据字节
            d3: 第三个数据字节

        Raises:
            VCXKnobConnectionError: 如果未连接或发送失败
        """
        if not self.is_connected:
            raise VCXKnobConnectionError(
                "未连接到设备",
                retryable=True,
            )

        command = build_command(cmd, d1, d2, d3)

        _LOGGER.debug(
            "发送命令: %s",
            command.hex().upper(),
        )

        try:
            async with asyncio.timeout(10):
                # VCX-Knob 设备使用 write-without-response
                # 参考 Node.js 实现，特征值属性为 'write-without-response'
                await self._client.write_gatt_char(
                    BLE_WRITE_CHARACTERISTIC_UUID,
                    command,
                    response=False,
                )
        except asyncio.TimeoutError as err:
            raise VCXKnobConnectionError(
                "命令发送超时",
                retryable=True,
            ) from err
        except BleakError as err:
            raise VCXKnobConnectionError(
                f"发送命令失败: {err}",
                retryable=False,
            ) from err

    def _notification_handler(self, sender: int, data: bytearray) -> None:
        """处理来自设备的通知

        BLE 通知可能包含多个连续的 8 字节状态包，需要按 PACKET_TOTAL_SIZE 切分。

        Args:
            sender: 发送通知的特征句柄
            data: 接收的数据字节
        """
        hex_str = data.hex().upper()
        _LOGGER.debug("收到通知(%d字节): %s", len(data), hex_str)

        # 按 8 字节切分，逐个加入缓冲区
        PACKET_SIZE = 8
        for i in range(0, len(data), PACKET_SIZE):
            chunk = data[i:i + PACKET_SIZE]
            if len(chunk) == PACKET_SIZE:
                self._status_buffer.append(chunk.hex().upper())
            else:
                _LOGGER.debug(
                    "忽略不完整的尾部数据(%d字节): %s",
                    len(chunk),
                    chunk.hex().upper(),
                )

        # 防止缓冲区增长过大
        if len(self._status_buffer) > 100:
            self._status_buffer = self._status_buffer[-100:]

        # 通知回调（保留原始数据兼容性）
        self._notification_callback(data)

    def get_status_buffer(self) -> list[str]:
        """获取当前状态缓冲区

        Returns:
            表示接收到的数据包的十六进制字符串列表
        """
        return self._status_buffer.copy()

    def clear_status_buffer(self) -> None:
        """清空状态缓冲区"""
        self._status_buffer.clear()


# ============================================================================
# 数据更新协调器
# ============================================================================

class VCXKnobCoordinator(DataUpdateCoordinator[dict]):
    """用于管理 VCX-Knob 设备状态和更新的协调器

    此协调器:
    - 管理 BLE 连接
    - 定期轮询状态更新
    - 向实体提供当前状态
    - 处理断开后的重连
    - 执行来自实体的命令
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: VCXKnobBLEClient,
        poll_interval: int = DEFAULT_STATUS_POLL_INTERVAL,
    ) -> None:
        """初始化协调器

        Args:
            hass: Home Assistant 实例
            config_entry: 此集成的配置条目
            client: BLE 客户端实例
            poll_interval: 状态轮询间隔（秒）
        """
        self._config_entry = config_entry
        self._client = client
        self._poll_interval = max(MIN_POLL_INTERVAL, min(MAX_POLL_INTERVAL, poll_interval))

        self._device_state: dict[str, bool | int | str | None] = {
            "connected": False,
            "paired": False,
            "rssi": None,
            "device_address": self.device_address,  # 添加设备地址到状态
        }

        # 监听 Home Assistant 关闭事件
        config_entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._async_shutdown)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._poll_interval),
        )

        # 开始连接
        hass.async_create_task(self._async_initial_connect())

        # 检查配对状态
        hass.async_create_task(self._async_check_paired_status())

    @property
    def client(self) -> VCXKnobBLEClient:
        """获取 BLE 客户端"""
        return self._client

    @property
    def device_address(self) -> str:
        """获取设备地址"""
        return self._config_entry.data[CONF_DEVICE_ADDRESS]

    @property
    def device_name(self) -> str:
        """获取设备名称"""
        return self._config_entry.data.get(CONF_DEVICE_NAME, "VCX-Knob")

    @property
    def auto_connect(self) -> bool:
        """获取是否自动连接配置"""
        return self._config_entry.data.get(CONF_AUTO_CONNECT, DEFAULT_AUTO_CONNECT)

    async def _async_check_paired_status(self) -> None:
        """检查蓝牙设备配对状态"""
        try:
            process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "info",
                self.device_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            result = stdout.decode() + stderr.decode()

            # 解析配对状态
            paired = "Paired: yes" in result
            self._device_state["paired"] = paired
            _LOGGER.debug("设备 %s 配对状态: %s", self.device_address, paired)

        except asyncio.TimeoutError:
            _LOGGER.warning("检查配对状态超时: %s", self.device_address)
            self._device_state["paired"] = False
        except FileNotFoundError:
            # 蓝牙命令不可用（可能不在 Linux 上）
            _LOGGER.debug("bluetoothctl 不可用，无法检查配对状态")
            self._device_state["paired"] = True  # 假设已配对
        except Exception as err:
            _LOGGER.warning("检查配对状态时出错: %s", err)
            self._device_state["paired"] = False

    async def _async_initial_connect(self) -> None:
        """执行与设备的初始连接

        根据 auto_connect 配置决定是否立即连接：
        - True: 自动连接设备（默认）
        - False: 仅扫描模式，不自动连接
        """
        if not self.auto_connect:
            _LOGGER.info(
                "自动连接已禁用，设备将保持扫描模式。"
                "请使用服务或手动触发连接。"
            )
            self._device_state["connected"] = False
            return

        try:
            await self._client.connect()
            self._device_state["connected"] = True
            self._device_state["rssi"] = self._client.rssi
            _LOGGER.info("初始连接成功")
        except VCXKnobConnectionError as err:
            _LOGGER.error("初始连接失败: %s", err)
            self._device_state["connected"] = False

    async def _async_update_data(self) -> dict:
        """通过查询状态更新设备状态

        此方法:
        1. 检查 auto_connect 配置
        2. 如果启用自动连接，确保已连接并查询状态
        3. 如果禁用自动连接，仅返回当前状态（扫描模式）

        Returns:
            当前设备状态字典

        Raises:
            UpdateFailed: 如果更新失败
        """
        # 如果禁用自动连接，处于扫描模式，不进行状态查询
        if not self.auto_connect:
            # 扫描模式下，仅更新连接状态为 False
            self._device_state["connected"] = False
            return self._device_state.copy()

        try:
            # 确保我们已连接
            if not self._client.is_connected:
                _LOGGER.info("设备已断开，尝试重新连接...")
                await self._client.connect()

            # 更新 RSSI
            self._device_state["rssi"] = self._client.rssi

            # 清空缓冲区以接收新状态
            self._client.clear_status_buffer()

            # 发送状态查询命令 (ZHUANGTAI = "FF")
            await self._client.send_command("FF", 0, 0, 0)

            # 等待状态包（所有 6 种类型）
            await self._async_wait_for_status_packets()

            # 更新连接状态
            self._device_state["connected"] = True

            return self._device_state.copy()

        except VCXKnobConnectionError as err:
            self._device_state["connected"] = False
            if err.retryable:
                _LOGGER.warning("连接错误（将重试）: %s", err)
                # 返回带有 connected=False 的当前状态
                return self._device_state.copy()
            else:
                raise UpdateFailed(f"不可重试的连接错误: {err}") from err

        except Exception as err:
            self._device_state["connected"] = False
            raise UpdateFailed(f"更新失败: {err}") from err

    async def _async_wait_for_status_packets(
        self,
        timeout: float = 10.0,
    ) -> None:
        """等待所有状态包被接收

        Args:
            timeout: 最大等待时间（秒）
        """
        received_types = set()
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            buffer = self._client.get_status_buffer()

            for hex_str in buffer:
                try:
                    data = bytes.fromhex(hex_str)
                    packet = parse_status_packet(data)

                    if packet:
                        packet_type = packet["type"]
                        if packet_type not in received_types:
                            received_types.add(packet_type)

                            # 解码并合并状态
                            decoded = decode_status_packet(packet)
                            if decoded:
                                self._device_state.update(decoded)

                except Exception as err:
                    _LOGGER.debug("解析状态数据包时出错: %s", err)

            # 检查是否接收到所有 6 种数据包类型
            if len(received_types) >= 6:
                _LOGGER.debug("接收到全部 6 种状态数据包类型")
                break

            await asyncio.sleep(0.2)

        if len(received_types) < 6:
            _LOGGER.debug(
                "仅接收到 %d / 6 种状态数据包类型",
                len(received_types),
            )

    async def async_send_command(
        self,
        cmd: str,
        d1: int = 0,
        d2: int = 0,
        d3: int = 0,
    ) -> None:
        """向设备发送命令

        这是实体发送命令的便捷方法

        Args:
            cmd: 命令码
            d1: 第一个数据字节
            d2: 第二个数据字节
            d3: 第三个数据字节

        Raises:
            VCXKnobConnectionError: 如果命令发送失败
        """
        await self._client.send_command(cmd, d1, d2, d3)

    async def async_disconnect(self) -> None:
        """从设备断开连接"""
        await self._client.disconnect()
        self._device_state["connected"] = False

    @callback
    def _async_shutdown(self, event: Event) -> None:
        """处理 Home Assistant 关闭

        Args:
            event: 关闭事件
        """
        _LOGGER.info("正在关闭 %s 的协调器", self.device_address)
        self.hass.async_create_task(self.async_disconnect())


# ============================================================================
# 工具函数
# ============================================================================

async def async_get_ble_device(
    hass: HomeAssistant,
    address: str,
) -> BluetoothServiceInfo | None:
    """通过地址获取 BLE 设备

    Args:
        hass: Home Assistant 实例
        address: BLE 设备地址

    Returns:
        如果找到返回 BluetoothServiceInfo，否则返回 None
    """
    return bluetooth.async_get_service_info_from_name(hass, address)


async def async_scan_for_device(
    hass: HomeAssistant,
    name_filter: str = BLE_DEVICE_NAME_FILTER,
    timeout: int = DEFAULT_SCAN_TIMEOUT,
) -> BluetoothServiceInfo | None:
    """扫描 VCX-Knob 设备

    Args:
        hass: Home Assistant 实例
        name_filter: 设备名称过滤器
        timeout: 扫描超时（秒）

    Returns:
        如果找到返回 BluetoothServiceInfo，否则返回 None
    """
    _LOGGER.info("正在扫描 BLE 设备 '%s'（超时: %d秒）", name_filter, timeout)

    current_address = set()

    def _service_info_callback(
        service_info: BluetoothServiceInfo,
        _change: bluetooth.Change,
    ) -> None:
        """BLE 扫描器回调"""
        if service_info.name and name_filter in service_info.name:
            _LOGGER.debug(
                "发现设备: %s (%s)",
                service_info.name,
                service_info.address,
            )
            current_address.add(service_info.address)

    # 注册回调
    remove_callback = bluetooth.async_register_callback(
        hass,
        _service_info_callback,
        bluetooth.BluetoothCallbackMatcher(connectable=True),
    )

    try:
        # 确保扫描器正在运行
        scanner = async_get_scanner(hass)

        # 等待设备发现
        await asyncio.sleep(timeout)

        # 获取第一个找到的设备信息
        for address in current_address:
            device_info = await async_get_ble_device(hass, address)
            if device_info:
                return device_info

        return None

    finally:
        remove_callback()
