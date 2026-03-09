# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 **VCX-Knob 智能马桶的 Home Assistant 自定义集成**，通过蓝牙低功耗 (BLE) 直接与设备通信，无需云端或 MQTT。

## 开发设置

### 同步到 Home Assistant

本项目使用远程 Home Assistant 实例进行测试。运行前请先修改同步脚本中的连接信息：

```bash
# 同步代码到 HA（需要 SSH 访问）
./script/development/sync_to_ha.sh

# 调试连接并检查 HA 状态
./script/development/ha_test.sh

# 在 HA 内测试 BLE 扫描
./test_ble_in_ha.sh
```

**重要**：请在这些脚本中更新 `HA_HOST`、`HA_USER` 和 `HA_CONFIG_DIR` 以匹配你的环境。

### 本地 BLE 测试

```bash
# 直接 BLE 扫描测试 (Python)
python3 ble_scan_test.py
```

### 需要重启 HA

同步代码更改后，需重启 Home Assistant：

```bash
ssh root@<HA_HOST> 'docker restart homeassistant'
```

或通过 HA 界面：设置 → 系统 → 重启

## 架构设计

### 核心组件

集成遵循 Home Assistant 的 `custom_component` 模式：

- **`__init__.py`**：入口点 - 创建协调器，注册实体平台
- **`coordinator.py`**：两个关键类：
  - `VCXKnobBLEClient`：使用 bleak 的底层 BLE 连接
  - `VCXKnobCoordinator`：继承 `DataUpdateCoordinator`，每 30 秒轮询状态
- **`protocol.py`**：协议实现 - 构建命令，解析 6 种状态包类型
- **`const.py`**：所有常量，包括 BLE UUID、命令码、实体描述
- **`config_flow.py`**：设备发现和设置的 UI 向导

### 实体平台文件

- `sensors.py` - 13 个传感器实体（信号强度、百分比、时间、距离）
- `switches.py` - 11 个开关实体（开/关控制）
- `buttons.py` - 3 个按钮实体（一次性操作）
- `selects.py` - 7 个选择实体（多选项设置）
- `binary_sensor.py` - 1 个连接状态传感器

### BLE 协议

**命令帧**：`AA 08 02 {cmd} {d1} {d2} {d3} {checksum}`

**状态帧**：`AA 08 88 {type} {data1} {data2} {data3} {checksum}`

共有 6 种状态包类型（01-06），每种包含不同的设备状态数据。协调器在每次轮询期间等待接收全部 6 种类型。

### BLE UUID

- 服务：`0000FFA0-0000-1000-8000-00805F9B34FB`
- 写特征值：`0000FFA1-0000-1000-8000-00805F9B34FB`
- 通知特征值：`0000FFA2-0000-1000-8000-00805F9B34FB`

## 常见任务

### 添加新实体

1. 在 `const.py` 的相应实体描述列表中添加实体描述
2. 在相应的实体文件（`sensors.py`、`switches.py` 等）中创建实体类
3. 添加翻译到 `strings.json` 和 `translations/zh-Hans.json`
4. 实体通过 `__init__.py` 中的 `async_setup_entry` 自动注册

### 添加新命令

1. 在 `const.py` 的 `Command` 枚举中添加命令码
2. 如果命令返回状态数据，在 `protocol.py` 中添加解码函数
3. 创建相应的实体或服务来暴露该命令

### 协议修改

协议逻辑集中在 `protocol.py` 中：

- `build_command()`：构造带校验和的命令帧
- `parse_status_packet()`：验证并提取数据包字段
- `decode_type_XX_packet()`：解码 6 种数据包类型

## 文件位置

- 主集成代码：`/custom_components/vcx_knob/`
- 测试脚本：根目录（`.sh` 和 `.py` 文件）
- 文档：`DESIGN.md`、`REQUIREMENTS.md`、`README.md`

## 依赖项

- `bleak>=0.21.0` - 跨平台 BLE 库
- Home Assistant 2023.11.0+

## 双语支持

本集成支持英语和简体中文。添加新实体或选项时，务必同时添加到 `strings.json` 和 `translations/zh-Hans.json` 的翻译。
