"""VCX-Knob 集成的配置流程

此模块实现添加 VCX-Knob 智能马桶设备到 Home Assistant 的配置流程。

流程:
1. 用户启动配置流程
2. 通过 BLE 扫描附近的 VCX-Knob 设备
3. 用户从列表中选择设备
4. 可选：自定义设备名称
5. 测试连接
6. 创建配置条目
"""

import asyncio
import logging
from typing import Any

import voluptuous as vol
from bleak import BleakError
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    BluetoothChange,
    BluetoothScanningMode,
    async_get_scanner,
    async_register_callback,
    BluetoothCallbackMatcher,
)
from homeassistant.const import CONF_NAME, CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_AUTO_CONNECT,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    DEFAULT_AUTO_CONNECT,
    DEFAULT_SCAN_TIMEOUT,
    DOMAIN,
    BLE_DEVICE_NAME_FILTER,
)
from .coordinator import VCXKnobBLEClient, VCXKnobConnectionError

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 模式定义
# ============================================================================

STEP_USER_DATA_SCHEMA = vol.Schema({})


# ============================================================================
# 发现数据
# ============================================================================

class DiscoveredDevice:
    """表示发现的 BLE 设备"""

    def __init__(
        self,
        name: str,
        address: str,
        rssi: int,
    ) -> None:
        """初始化发现的设备

        Args:
            name: 设备名称
            address: 设备地址（MAC 或 UUID）
            rssi: 信号强度
        """
        self.name = name
        self.address = address
        self.rssi = rssi

    @property
    def title(self) -> str:
        """获取显示标题"""
        return f"{self.name} ({self.address})"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "address": self.address,
            "rssi": self.rssi,
        }


# ============================================================================
# 配置流程
# ============================================================================

class VCXKnobConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理 VCX-Knob 的配置流程"""

    VERSION = 1

    def __init__(self) -> None:
        """初始化配置流程"""
        self._discovered_devices: dict[str, DiscoveredDevice] = {}
        self._selected_device: DiscoveredDevice | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """处理初始步骤

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        if user_input is not None:
            # 直接执行扫描
            return await self._async_scan_and_proceed()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={
                "device_name": BLE_DEVICE_NAME_FILTER,
            },
        )

    async def _async_scan_and_proceed(self) -> FlowResult:
        """执行扫描并跳转到相应步骤

        Returns:
            流程结果
        """
        # 清空之前发现的设备
        self._discovered_devices.clear()

        # 开始扫描
        _LOGGER.info("正在扫描附近的 %s 设备...", BLE_DEVICE_NAME_FILTER)

        try:
            await self._async_scan_for_devices()
        except Exception as err:
            _LOGGER.error("扫描失败: %s", err)
            return self.async_abort(reason="scan_failed")

        # 检查是否发现任何设备
        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        # 如果只发现一个设备，自动选择它，然后进入配对步骤
        if len(self._discovered_devices) == 1:
            self._selected_device = next(iter(self._discovered_devices.values()))
            return await self.async_step_pair()

        # 显示设备选择
        return await self.async_step_select_device()

    async def async_step_scan(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """处理扫描步骤

        此步骤通过蓝牙扫描附近的 VCX-Knob 设备

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        # 清空之前发现的设备
        self._discovered_devices.clear()

        # 开始扫描
        _LOGGER.info("正在扫描附近的 %s 设备...", BLE_DEVICE_NAME_FILTER)

        try:
            await self._async_scan_for_devices()

        except Exception as err:
            _LOGGER.error("扫描失败: %s", err)
            return self.async_abort(reason="scan_failed")

        # 检查是否发现任何设备
        if not self._discovered_devices:
            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema({}),
                errors={"base": "no_devices_found"},
                description_placeholders={
                    "device_name": BLE_DEVICE_NAME_FILTER,
                },
            )

        # 如果只发现一个设备，自动选择它，然后进入配对步骤
        if len(self._discovered_devices) == 1:
            self._selected_device = next(iter(self._discovered_devices.values()))
            return await self.async_step_pair()

        # 显示设备选择
        return await self.async_step_select_device()

    async def _async_scan_for_devices(
        self,
        timeout: int = DEFAULT_SCAN_TIMEOUT,
    ) -> None:
        """扫描 VCX-Knob 设备

        Args:
            timeout: 扫描超时（秒）
        """
        scanner = async_get_scanner(self.hass)

        discovered_addresses: set[str] = set()
        discovered_names: dict[str, str] = {}
        discovered_rssi: dict[str, int] = {}

        def _service_info_callback(
            service_info: BluetoothServiceInfo,
            _change: BluetoothChange,
        ) -> None:
            """BLE 扫描器回调"""
            if service_info.name and BLE_DEVICE_NAME_FILTER in service_info.name:
                address = service_info.address
                discovered_addresses.add(address)
                discovered_names[address] = service_info.name
                discovered_rssi[address] = service_info.rssi

                _LOGGER.debug(
                    "发现设备: %s (%s), RSSI: %d",
                    service_info.name,
                    address,
                    service_info.rssi,
                )

        # 注册回调
        remove_callback = async_register_callback(
            self.hass,
            _service_info_callback,
            BluetoothCallbackMatcher(connectable=True),
            BluetoothScanningMode.ACTIVE,
        )

        try:
            # 等待发现
            await asyncio.sleep(timeout)

            # 转换为 DiscoveredDevice 对象
            for address in discovered_addresses:
                device = DiscoveredDevice(
                    name=discovered_names[address],
                    address=address,
                    rssi=discovered_rssi.get(address, 0),
                )

                # 检查是否已配置
                await self.async_set_unique_id(device.address)
                self._abort_if_unique_id_configured()

                self._discovered_devices[address] = device

        finally:
            remove_callback()

    async def async_step_select_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """处理设备选择步骤

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        errors = {}

        if user_input is not None:
            device_address = user_input[CONF_DEVICE_ADDRESS]
            self._selected_device = self._discovered_devices[device_address]

            # 设置唯一 ID
            await self.async_set_unique_id(self._selected_device.address)
            self._abort_if_unique_id_configured()

            return await self.async_step_pair()

        # 构建选择模式
        devices_dict = {
            addr: device.title
            for addr, device in self._discovered_devices.items()
        }

        data_schema = vol.Schema({
            vol.Required(CONF_DEVICE_ADDRESS): vol.In(devices_dict),
        })

        return self.async_show_form(
            step_id="select_device",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_pair(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """处理配对步骤

        此步骤引导用户配对 VCX-Knob 设备。
        配对于控制设备是必需的，否则按钮将显示为灰色。

        注意：某些 BLE 设备可能不支持标准蓝牙配对，
        这种情况下可以跳过配对直接使用。

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        device_address = self._selected_device.address

        # 检查是否已配对
        is_paired = await self._check_device_paired(device_address)

        if is_paired:
            _LOGGER.info("设备 %s 已配对，跳过配对步骤", device_address)
            return await self.async_step_confirm()

        # 如果用户确认，尝试配对
        if user_input is not None:
            try:
                await self._async_pair_device(device_address)
                # 配对成功，继续到确认步骤
                return await self.async_step_confirm()
            except Exception as err:
                _LOGGER.warning("配对失败: %s，但继续设置流程", err)
                # 即使配对失败也继续，因为某些设备可能不需要配对
                return await self.async_step_confirm()

        # 显示配对说明和确认按钮
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({}),
            description_placeholders={
                "device_name": self._selected_device.name,
                "device_address": device_address,
                "rssi": self._selected_device.rssi,
            },
        )

    async def _check_device_paired(self, device_address: str) -> bool:
        """检查设备是否已配对

        Args:
            device_address: 设备 MAC 地址

        Returns:
            如果已配对返回 True
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "info",
                device_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await process.communicate()
            result = stdout.decode()

            # 检查是否已配对
            is_paired = "Paired: yes" in result

            _LOGGER.debug("设备 %s 配对状态: %s", device_address, is_paired)
            return is_paired

        except Exception as err:
            _LOGGER.error("检查配对状态失败: %s", err)
            return False

    async def _async_pair_device(self, device_address: str) -> None:
        """执行蓝牙配对

        Args:
            device_address: 设备 MAC 地址

        Raises:
            VCXKnobConnectionError: 如果配对失败
        """
        _LOGGER.info("正在配对设备: %s", device_address)

        # 配对
        pair_process = await asyncio.create_subprocess_exec(
            "bluetoothctl",
            "pair",
            device_address,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await pair_process.communicate()
        result = stdout.decode() + stderr.decode()

        if "Pairing successful" in result or "Already paired" in result:
            _LOGGER.info("蓝牙配对成功: %s", device_address)

            # 信任设备
            trust_process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "trust",
                device_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await trust_process.communicate()

        else:
            raise Exception(f"配对失败: {result}")

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """处理确认步骤

        此步骤显示选定的设备并允许在连接前自定义

        用户可以选择：
        - 自定义设备名称
        - 是否立即连接设备（扫描+连接模式）
        - 是否测试连接

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        errors = {}

        if user_input is not None:
            auto_connect = user_input.get(CONF_AUTO_CONNECT, DEFAULT_AUTO_CONNECT)

            # 如果用户选择自动连接，先测试连接
            if auto_connect:
                try:
                    await self._async_test_connection()
                except Exception as err:
                    _LOGGER.error("连接测试失败: %s", err)
                    errors["base"] = "cannot_connect"
                    # 显示错误，但仍然允许继续

            # 创建配置条目（无论连接测试是否成功）
            return self._async_create_entry(user_input)

        # 如果尚未设置唯一 ID
        if self._selected_device:
            await self.async_set_unique_id(self._selected_device.address)
            self._abort_if_unique_id_configured()

        data_schema = vol.Schema({
            vol.Optional(
                CONF_DEVICE_NAME,
                default=self._selected_device.name if self._selected_device else BLE_DEVICE_NAME_FILTER,
            ): str,
            vol.Optional(
                CONF_AUTO_CONNECT,
                default=DEFAULT_AUTO_CONNECT,
            ): bool,
        })

        return self.async_show_form(
            step_id="confirm",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "device_name": self._selected_device.name if self._selected_device else BLE_DEVICE_NAME_FILTER,
                "device_address": self._selected_device.address if self._selected_device else "未知",
                "rssi": str(self._selected_device.rssi) if self._selected_device else "0",
            },
        )

    async def _async_test_connection(self) -> None:
        """测试与选定设备的连接

        Raises:
            VCXKnobConnectionError: 如果连接失败
        """
        if not self._selected_device:
            raise VCXKnobConnectionError("未选择设备")

        client = VCXKnobBLEClient(
            address=self._selected_device.address,
            name=self._selected_device.name,
            notification_callback=lambda data: None,
        )

        try:
            async with asyncio.timeout(30):
                await client.connect()

                # 保持连接片刻以验证稳定性
                await asyncio.sleep(2)

                await client.disconnect()

        except asyncio.TimeoutError as err:
            raise VCXKnobConnectionError("连接超时") from err
        except BleakError as err:
            raise VCXKnobConnectionError(f"BLE 错误: {err}") from err
        except Exception as err:
            raise VCXKnobConnectionError(f"连接失败: {err}") from err

    def _async_create_entry(self, user_input: dict[str, Any]) -> FlowResult:
        """创建配置条目

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        device_name = user_input.get(
            CONF_DEVICE_NAME,
            self._selected_device.name if self._selected_device else BLE_DEVICE_NAME_FILTER,
        )
        auto_connect = user_input.get(CONF_AUTO_CONNECT, DEFAULT_AUTO_CONNECT)

        return self.async_create_entry(
            title=device_name,
            data={
                CONF_DEVICE_ADDRESS: self._selected_device.address,
                CONF_DEVICE_NAME: device_name,
                CONF_AUTO_CONNECT: auto_connect,
            },
        )

    async def async_step_bluetooth(
        self,
        discovery_info: BluetoothServiceInfo,
    ) -> FlowResult:
        """处理自动蓝牙发现

        当 VCX-Knob 设备被 Home Assistant 的蓝牙集成自动发现时触发

        Args:
            discovery_info: 蓝牙服务信息

        Returns:
            流程结果
        """
        _LOGGER.info(
            "发现 %s 设备: %s (%s)",
            BLE_DEVICE_NAME_FILTER,
            discovery_info.name,
            discovery_info.address,
        )

        # 设置唯一 ID
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # 存储发现的设备
        self._selected_device = DiscoveredDevice(
            name=discovery_info.name or BLE_DEVICE_NAME_FILTER,
            address=discovery_info.address,
            rssi=discovery_info.rssi,
        )

        # 进入配对步骤
        return await self.async_step_pair()


# ============================================================================
# 选项流程
# ============================================================================

class VCXKnobOptionsFlow(config_entries.OptionsFlow):
    """处理 VCX-Knob 的选项流程"""

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
    ) -> None:
        """初始化选项流程

        Args:
            config_entry: 要修改的配置条目
        """
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """管理选项

        Args:
            user_input: 用户输入

        Returns:
            流程结果
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # 目前没有选项，但这是未来选项（如轮询间隔、重连设置）的占位符

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
