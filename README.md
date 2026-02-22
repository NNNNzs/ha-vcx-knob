# VCX-Knob 智能马桶 Home Assistant 集成

[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HA 版本](https://img.shields.io/badge/HA-2023.11%2B-blue.svg)](https://www.home-assistant.io)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)

通过蓝牙低功耗 (BLE) 直接控制 VCX-Knob 智能马桶设备的 Home Assistant 自定义集成。

## 功能特点

- **本地控制**：直接 BLE 通信，无需云端或 MQTT
- **丰富的实体支持**：
  - 13 个传感器用于监控（信号强度、百分比、时间）
  - 11 个开关用于开/关控制（冲水、座圈、气泡、热风、雷达等）
  - 7 个选择用于多选项设置（温度、档位、亮度）
  - 3 个按钮用于一次性操作（大冲水、小冲水、恢复出厂设置）
  - 1 个连接状态二进制传感器
- **自动发现**：通过 HA UI 扫描并配对设备
- **自动重连**：设备断开后自动重新连接
- **双语支持**：英语和简体中文

## 安装

### 通过 HACS（推荐）

1. 在 Home Assistant 中打开 HACS
2. 点击 "Integrations"（集成）
3. 点击三个点菜单 → "Custom repositories"（自定义仓库）
4. 添加此仓库 URL
5. 搜索 "VCX-Knob" 并点击 "Download"（下载）

### 手动安装

1. 将 `custom_components/vcx_knob` 目录复制到 Home Assistant 的 `custom_components` 目录
2. 重启 Home Assistant
3. 通过 设置 → 设备与服务 → 添加集成 来添加集成

## 配置

1. 前往 **设置** → **设备与服务**
2. 点击 **添加集成**
3. 搜索 **VCX-Knob**
4. 按照设置向导操作：
   - 集成将扫描附近的 VCX-Knob 设备
   - 从列表中选择您的设备
   - 可选：自定义设备名称
   - 等待连接测试完成

### 系统要求

- Home Assistant 2023.11 或更高版本
- Home Assistant 支持的蓝牙适配器
- VCX-Knob 智能马桶设备已开机且在范围内

## 实体

### 传感器

| 实体 | 描述 | 单位 |
|------|------|------|
| 信号强度 | BLE 信号强度 | dBm |
| 热风百分比 | 当前热风输出百分比 | % |
| 水量百分比 | 当前水量百分比 | % |
| 雷达等级 | 雷达感应等级 | - |
| 盖板关闭时间 | 自动关闭时间 | 秒 |
| 盖板翻转强度 | 盖板翻转电机强度 | - |
| 座圈翻转强度 | 座圈翻转电机强度 | - |
| 盖板关闭强度 | 盖板关闭电机强度 | - |
| 气泡等级 | 气泡功能等级 | - |
| 大冲水时间 | 大冲水持续时间 | 秒 |
| 小冲水时间 | 小冲水持续时间 | 秒 |
| 脚感应距离 | 脚感应器检测距离 | 厘米 |
| 杀菌时间 | 杀菌功能持续时间 | 分钟 |

### 开关

| 实体 | 描述 |
|------|------|
| 冲水 | 启用/禁用冲水功能 |
| 座圈 | 启用/禁用座圈功能 |
| 气泡 | 启用/禁用气泡功能 |
| 热风 | 启用/禁用热风烘干 |
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
| 已连接 | BLE 连接状态 |

## 自动化示例

### 当浴室变暗时打开夜灯

```yaml
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
```

### 使用 10 分钟后自动关闭座圈

```yaml
automation:
  - alias: "使用后自动关闭马桶座圈"
    trigger:
      - platform: state
        entity_id: binary_sensor.toilet_seat_occupancy
        to: "off"
        for:
          minutes: 10
    action:
      - service: select.select_option
        target:
          entity_id: select.vcx_knob_seat_position
        data:
          option: "关闭"
```

## 服务

### 发送原始命令

向设备发送自定义命令：

```yaml
service: vcx_knob.send_command
data:
  device_id: "abc123vcxknob"
  command: "07"  # 命令代码
  d1: 0          # 数据字节 1 (0-255)
  d2: 0          # 数据字节 2 (0-255)
  d3: 0          # 数据字节 3 (0-255)
```

## 故障排除

### 找不到设备

1. 确保 VCX-Knob 设备已开机
2. 确保设备在蓝牙范围内（通常 < 10 米）
3. 检查 Home Assistant 是否具有蓝牙权限
4. 尝试重启 Home Assistant

### 连接频繁断开

1. 检查信号强度传感器（应 > -70 dBm 以获得稳定连接）
2. 将 Home Assistant 服务器移近设备
3. 检查其他设备的蓝牙干扰
4. 考虑使用蓝牙扩展加密狗

### 实体显示不可用

1. 检查 "已连接" 二进制传感器
2. 查看 Home Assistant 日志中的错误消息
3. 为 `custom_components.vcx_knob` 启用调试日志

## 开发

此项目包含详细的设计和需求文档：

- [DESIGN.md](DESIGN.md) - 架构和设计决策
- [REQUIREMENTS.md](REQUIREMENTS.md) - 功能需求和规格

### 项目结构

```
custom_components/vcx_knob/
├── __init__.py           # 集成入口点
├── manifest.json         # 集成元数据
├── config_flow.py        # 配置流程向导
├── const.py              # 常量和实体描述
├── coordinator.py        # BLE 客户端和数据协调器
├── protocol.py           # BLE 协议实现
├── sensors.py            # 传感器实体
├── switches.py           # 开关实体
├── buttons.py            # 按钮实体
├── selects.py            # 选择实体
├── binary_sensor.py      # 二进制传感器实体
├── services.yaml         # 服务定义
├── strings.json          # 翻译
└── translations/         # 语言文件
    ├── en.json
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
