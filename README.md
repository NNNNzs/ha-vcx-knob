# VCX-Knob 智能马桶 Home Assistant 集成

[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HA 版本](https://img.shields.io/badge/HA-2024.1%2B-blue.svg)](https://www.home-assistant.io)
[![Open your Home Assistant instance and show the VCX-Knob integration.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=NNNNzs&repository=ha-vcx-knob&category=integration)
[![Add Integration](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vcx_knob)

通过蓝牙低功耗 (BLE) 直接控制 VCX-Knob 智能马桶设备的 Home Assistant 自定义集成。

## 功能特点

- **本地控制**：直接 BLE 通信，无需云端或 MQTT
- **丰富的实体支持**：
  - 18 个传感器（信号强度、百分比、时间、距离等）
  - 7 个开关（雷达、语音、传感器、自动模式、夜灯、脚感应、杀菌）
  - 15 个按钮（冲水、清洗、烘干、翻盖/圈、润壁、自洁等）
  - 7 个选择（水温、座温、风温、水量、灯光亮度、雷达灵敏度等）
  - 2 个二进制传感器（BLE 连接状态、配对状态）
- **自动发现**：通过 HA UI 扫描并配对设备
- **自动重连**：设备断开后自动重新连接
- **双语支持**：英语和简体中文

## 安装

### 通过 HACS（推荐）

1. 在 Home Assistant 中打开 HACS
2. 点击 "Integrations"（集成）
3. 点击三个点菜单 → "Custom repositories"（自定义仓库）
4. 添加此仓库 URL: `https://github.com/NNNNzs/ha-vcx-knob`
5. 搜索 "VCX-Knob" 并点击 "Download"（下载）

或点击上方 HACS 徽章直接跳转。

### 手动安装

1. 下载最新 [Release](https://github.com/NNNNzs/ha-vcx-knob/releases) 的 zip 文件
2. 解压到 Home Assistant 的 `custom_components/` 目录
3. 重启 Home Assistant

```
/homeassistant/config/
└── custom_components/
    └── vcx_knob/
        ├── __init__.py
        ├── manifest.json
        └── ...
```

## Docker 部署

如果使用 Docker 部署 Home Assistant，需要正确配置蓝牙支持（DBus 挂载、网络模式等）。

详见 **[Docker 蓝牙部署指南](docs/DOCKER_SETUP.md)**。

## 配置

### 前置要求

1. 蓝牙适配器工作正常
2. 蓝牙集成已添加（推荐）
3. VCX-Knob 设备已开机且在蓝牙范围内（< 10 米）
4. 设备已与系统配对（详见 [配对指南](docs/DOCKER_SETUP.md#3-蓝牙设备配对问题)）

### 添加集成

1. 前往 **设置 → 设备与服务 → 添加集成**
2. 搜索 **VCX-Knob** 或点击上方 "Add Integration" 徽章
3. 从扫描结果中选择您的设备
4. 可选：自定义设备名称，选择是否自动连接
5. 点击 **提交**

## 服务

通过 **开发者工具 → 服务** 或自动化调用：

| 服务 | 参数 | 说明 |
|------|------|------|
| `vcx_knob.pair_bluetooth_device` | `device_address` (必填), `timeout` (可选) | 配对蓝牙设备 |
| `vcx_knob.scan_bluetooth_device` | `timeout` (可选), `device_filter` (可选) | 扫描附近设备 |
| `vcx_knob.get_bluetooth_device_info` | `device_address` (必填) | 获取配对和连接状态 |

## 实体

### 传感器

| 实体 | 描述 | 单位 |
|------|------|------|
| 蓝牙地址 | 设备 BLE 地址 | - |
| 信号强度 | BLE 信号强度 | dBm |
| 热风百分比 | 当前热风输出百分比 | % |
| 水量百分比 | 当前水量百分比 | % |
| 雷达等级 | 雷达感应等级 | - |
| 盖板关闭时间 | 自动关闭时间 | 秒 |
| 盖板翻转强度 | 盖板翻转电机强度 | - |
| 座圈翻转强度 | 座圈翻转电机强度 | - |
| 盖板关闭强度 | 盖板关闭电机强度 | - |
| 座圈关闭强度 | 座圈关闭电机强度 | - |
| 气泡等级 | 气泡功能等级 | - |
| 大冲水量 | 大冲水持续时间 | 秒 |
| 小冲水量 | 小冲水持续时间 | 秒 |
| 小冲上冲时间 | 小冲上冲持续时间 | 秒 |
| 脚感应距离 | 脚感应器检测距离 | 厘米 |
| 杀菌时间 | 杀菌功能持续时间 | 分钟 |
| 水压 | 当前水压值 | - |
| 氛围灯亮度 | 氛围灯当前亮度 | % |

### 开关

| 实体 | 描述 |
|------|------|
| 雷达 | 启用/禁用雷达感应 |
| 语音控制 | 启用/禁用语音控制 |
| 传感器 | 启用/禁用传感器 |
| 自动模式 | 启用/禁用自动模式 |
| 夜灯 | 启用/禁用夜灯 |
| 脚感应 | 启用/禁用脚感应 |
| 杀菌 | 启用/禁用杀菌功能 |

### 按钮

| 实体 | 描述 |
|------|------|
| 大冲水 | 触发大冲水 |
| 小冲水 | 触发小冲水 |
| 妇洗 | 触发妇洗功能 |
| 臀洗 | 触发臀洗功能 |
| 按摩 | 触发按摩功能 |
| 气泡 | 触发气泡功能 |
| 停止 | 停止所有清洗功能 |
| 烘干 | 触发热风烘干 |
| 翻盖 | 打开盖板 |
| 翻圈 | 打开座圈 |
| 关闭 | 关闭盖板和座圈 |
| 润壁 | 触发润壁功能 |
| 自洁 | 触发自洁功能 |
| 恢复出厂设置 | 恢复出厂设置 |

### 选择

| 实体 | 选项 |
|------|------|
| 水温 | 关闭, 34°C, 37°C, 40°C |
| 座温 | 关闭, 34°C, 37°C, 40°C |
| 风温 | 关闭, 40°C, 45°C, 50°C |
| 水量 | 关闭, 低, 中, 高 |
| 热风档位 | 关闭, 低, 中, 高 |
| 灯光亮度 | 关闭, 低, 中, 高 |
| 雷达灵敏度 | 低, 中, 高 |

### 二进制传感器

| 实体 | 描述 |
|------|------|
| 蓝牙连接 | BLE 连接状态 |
| 配对状态 | 蓝牙配对状态 |

## 自动化示例

```yaml
# 当浴室变暗时打开夜灯
automation:
  - alias: "浴室变暗时打开马桶夜灯"
    trigger:
      - platform: state
        entity_id: sensor.bathroom_illuminance
        below: 10
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.vcx_knob_night_light

# 使用后自动关闭
automation:
  - alias: "使用后自动关闭马桶"
    trigger:
      - platform: state
        entity_id: binary_sensor.toilet_seat_occupancy
        to: "off"
        for:
          minutes: 10
    action:
      - service: button.press
        target:
          entity_id: button.vcx_knob_close
```

## 故障排除

详见 **[故障排除指南](docs/TROUBLESHOOTING.md)**。

## 项目结构

```
custom_components/vcx_knob/
├── __init__.py              # 集成入口点
├── manifest.json            # 集成元数据
├── config_flow.py           # 配置流程向导
├── const.py                 # 常量和实体描述
├── coordinator.py           # BLE 客户端和数据协调器
├── protocol.py              # BLE 协议实现
├── bluetooth_pairing.py     # 蓝牙配对模块
├── sensor.py                # 传感器实体（18个）
├── switch.py                # 开关实体（7个）
├── button.py                # 按钮实体（15个）
├── select.py                # 选择实体（7个）
├── binary_sensor.py         # 二进制传感器实体（2个）
├── services.yaml            # 服务定义
├── strings.json             # 英文翻译
└── translations/
    └── zh-Hans.json
```

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 支持

- **问题**: [GitHub Issues](https://github.com/NNNNzs/ha-vcx-knob/issues)
- **讨论**: [GitHub Discussions](https://github.com/NNNNzs/ha-vcx-knob/discussions)

## 致谢

- 此集成使用 [bleak](https://github.com/hbldh/bleak) 库进行 BLE 通信
- 协议文档基于 VCX-Knob 智能马桶设备的分析
