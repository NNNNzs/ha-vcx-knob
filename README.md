# VCX-Knob 智能马桶 Home Assistant 集成

[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HA 版本](https://img.shields.io/badge/HA-2024.1%2B-blue.svg)](https://www.home-assistant.io)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)

通过蓝牙低功耗 (BLE) 直接控制 VCX-Knob 智能马桶设备的 Home Assistant 自定义集成。

> **当前状态**：开发中 🚧
>
> 目前集成已完成基础功能开发，正在进行最后的调试和优化工作。主要功能包括 BLE 连接、状态读取、设备控制等，已支持传感器、开关、按钮、选择等多种实体类型。

## 功能特点

- **本地控制**：直接 BLE 通信，无需云端或 MQTT
- **丰富的实体支持**：
  - 13 个传感器用于监控（信号强度、百分比、时间）
  - 11 个开关用于开/关控制（冲水、座圈、气泡、热风、雷达等）
  - 7 个选择用于多选项设置（温度、档位、亮度）
  - 14 个按钮用于一次性操作（大冲水、小冲水、妇洗、臀洗等）
  - 1 个连接状态二进制传感器
- **自动发现**：通过 HA UI 扫描并配对设备
- **自动重连**：设备断开后自动重新连接
- **双语支持**：英语和简体中文

## ⚠️ Docker 部署重要说明

如果您使用 Docker 部署 Home Assistant，需要正确配置蓝牙支持。以下是常见问题和解决方案：

### 1. 蓝牙设备权限问题

**问题**：集成报错 `DBus service not found` 或蓝牙功能无法正常工作。

**原因**：Docker 容器需要访问主机的 DBus 系统来与蓝牙适配器通信。

**解决方案**：在 `docker-compose.yml` 中添加 DBus 卷挂载：

```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: homeassistant/home-assistant:stable
    volumes:
      - /path/to/config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro  # ⚠️ 必须添加此行
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    privileged: true
    network_mode: host  # 推荐使用 host 网络模式
```

**验证方法**：
```bash
# 进入容器检查
docker exec -it homeassistant ls -la /run/dbus/

# 应该看到 system_bus_socket 文件
```

### 2. 蓝牙适配器未映射

**问题**：容器内无法检测到蓝牙适配器。

**原因**：即使使用了 `privileged: true` 和 `network_mode: host`，某些系统仍需要显式映射蓝牙 USB 设备。

**解决方案**（可选，如果上述方法无效）：

```yaml
services:
  homeassistant:
    volumes:
      # ... 其他卷 ...
      - /dev/bus/usb:/dev/bus/usb  # 添加 USB 设备映射
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # 如果使用串口蓝牙适配器
```

**验证方法**：
```bash
# 检查容器内的蓝牙适配器
docker exec homeassistant hciconfig -a

# 应该看到类似输出：
# hci0:   Type: Primary  Bus: USB
#         UP RUNNING
#         BD Address: XX:XX:XX:XX:XX:XX
```

### 3. 蓝牙设备配对问题

**问题**：集成显示 `Write not permitted`、按钮显示为灰色，或连接后无法控制设备。

**重要说明**：蓝牙**配对**和**连接**是两个不同的操作：
- **连接**：只是建立通信连接，可以读取设备状态
- **配对**：建立信任关系，**允许写入控制命令**（这是必需的！）

如果你的按钮显示为灰色，说明设备已连接但未配对。

#### 配对方法

本集成提供多种配对方法，请根据您的环境选择：

##### 方法 1：通过 VCX-Knob 集成向导配对（推荐，适用于所有用户）

1. **添加集成时自动配对**：
   - 前往 **设置 → 设备与服务**
   - 点击 **添加集成** → 搜索 **VCX-Knob**
   - 集成会在配置流程中自动检测配对状态
   - 如果未配对，会显示详细的配对说明
   - 点击 **提交** 按钮尝试自动配对
   - 如果自动配对失败，按照屏幕上的说明手动配对

2. **使用 HA 服务配对**：
   - 前往 **开发者工具 → 服务**
   - 选择服务：`vcx_knob.pair_bluetooth_device`
   - 输入设备 MAC 地址
   - 点击 **调用服务**

3. **扫描设备**：
   - 使用服务：`vcx_knob.scan_bluetooth_device`
   - 可配置扫描超时时间（默认 10 秒）
   - 返回发现的 VCX-Knob 设备列表

4. **检查配对状态**：
   - 使用服务：`vcx_knob.get_bluetooth_device_info`
   - 输入设备 MAC 地址
   - 返回配对、信任、连接状态

##### 方法 2：使用 Home Assistant 蓝牙集成

1. **添加蓝牙集成**：
   - 前往 **设置 → 设备与服务**
   - 点击 **添加集成**
   - 搜索并添加 **Bluetooth** 集成

2. **配对设备**：
   - 在蓝牙集成中点击 **配置**
   - 点击 **扫描设备**
   - 找到 **VCX-Knob** 设备
   - 点击 **配对**
   - 输入 PIN 码（如果需要，常见为 `0000`、`1234`）

3. **验证配对**：
   - 设备应显示为 "已配对" 状态
   - 添加 VCX-Knob 集成
   - 检查按钮是否可以点击

##### 方法 3：使用命令行配对（高级用户）

在 Home Assistant **宿主机**上执行（Docker 容器外）：

```bash
# 1. 启动 bluetoothctl 交互模式
bluetoothctl

# 2. 开启扫描
scan on

# 3. 等待发现 VCX-Knob 设备（记录 MAC 地址，格式：XX:XX:XX:XX:XX:XX）

# 4. 配对设备（将 MAC 地址替换为你的设备地址）
pair XX:XX:XX:XX:XX:XX

# 5. 当提示时，在 VCX-Knob 设备上确认配对（通常需要按下按钮）

# 6. 配对成功后，信任设备
trust XX:XX:XX:XX:XX:XX

# 7. 验证配对状态
info XX:XX:XX:XX:XX:XX

# 应该显示：
# Paired: yes  ← 必须是 yes
# Trusted: yes
# Connected: yes

# 8. 退出
exit
```

**配对失败的常见原因**：
- 设备距离太远（请将设备靠近 Home Assistant 服务器到 1 米内）
- 设备未在配对模式（有些设备需要长按按钮进入配对模式）
- 需要输入 PIN 码（常见 PIN：0000、1234、8888）
- 设备之前与其他设备配对过，需要先删除旧配对

**验证配对是否成功**：
```bash
# 在宿主机上检查
echo 'info <设备MAC地址>' | bluetoothctl

# 或在 HA 中测试按钮
# 按钮不再是灰色 = 配对成功
```

### 4. Home Assistant 版本兼容性

**问题**：集成加载失败或出现 API 错误。

**原因**：本集成需要 Home Assistant 2024.1 或更高版本。

**解决方案**：
- 升级 Home Assistant 到最新版本
- 确保 Python 版本为 3.11 或更高（HA 2024.1+ 要求）

**版本兼容性矩阵**：

| HA 版本 | 支持状态 | 说明 |
|---------|---------|------|
| 2024.1+ | ✅ 完全支持 | 推荐版本 |
| 2023.11 - 2023.12 | ⚠️ 可能兼容 | 需要测试 |
| 2023.10 及以下 | ❌ 不支持 | API 不兼容 |

### 5. 网络模式问题

**问题**：蓝牙扫描功能正常，但无法连接设备。

**原因**：使用 `bridge` 或 `nat` 网络模式可能导致蓝牙连接问题。

**解决方案**：在 `docker-compose.yml` 中使用 `network_mode: host`

```yaml
services:
  homeassistant:
    network_mode: host  # 推荐用于蓝牙集成
```

**注意事项**：
- `host` 网络模式会移除网络隔离，容器与宿主机共享网络栈
- 如果需要使用反向代理，请直接使用宿主机 IP 而非容器 IP
- 如果必须使用 `bridge` 模式，需要额外配置端口映射和蓝牙权限

## 安装

### 通过 HACS（推荐）

1. 在 Home Assistant 中打开 HACS
2. 点击 "Integrations"（集成）
3. 点击三个点菜单 → "Custom repositories"（自定义仓库）
4. 添加此仓库 URL: `https://github.com/NNNNzs/ha-vcx-knob`
5. 搜索 "VCX-Knob" 并点击 "Download"（下载）

### 手动安装

1. 将 `custom_components/vcx_knob` 目录复制到 Home Assistant 的 `custom_components` 目录
2. 重启 Home Assistant
3. 通过 设置 → 设备与服务 → 添加集成 来添加集成

**复制目录结构**：
```
/homeassistant/
└── custom_components/
    └── vcx_knob/
        ├── __init__.py
        ├── manifest.json
        ├── config_flow.py
        ├── ...（其他文件）
```

## 配置

### 前置要求

在添加集成之前，请确保：

1. ✅ **蓝牙适配器工作正常**
   - 在宿主机上运行 `hciconfig` 确认蓝牙适配器已启用
   - 在容器内运行 `docker exec homeassistant hciconfig` 确认容器可以访问蓝牙

2. ✅ **蓝牙集成已添加**（推荐）
   - 在 HA 中添加官方 Bluetooth 集成
   - 用于设备发现和配对

3. ✅ **VCX-Knob 设备已开机**
   - 设备电源已打开
   - 设备在蓝牙范围内（通常 < 10 米）

### 添加集成步骤

1. 前往 **设置 → 设备与服务**
2. 点击 **添加集成** ➔
3. 搜索 **VCX-Knob** 或 **Smart Toilet**
4. 点击进入配置流程：
   - 集成将自动扫描附近的 VCX-Knob 设备（约 10 秒）
   - 从列表中选择您的设备
   - 可选：自定义设备名称
   - 选择是否自动连接（推荐启用）
   - 点击 **提交**

### 首次配对

首次使用时，设备需要与系统配对：

1. 如果设备未配对，集成会提示配对失败
2. 按照上述 "蓝牙设备配对问题" 中的步骤进行配对
3. 配对成功后，重新添加集成即可

## 服务

本集成提供以下服务，可通过 **开发者工具 → 服务** 或自动化调用：

### vcx_knob.pair_bluetooth_device

配对 VCX-Knob 蓝牙设备。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| device_address | string | 是 | - | 设备 MAC 地址（例如：88:36:A2:D8:80:AC） |
| timeout | int | 否 | 15 | 配对超时时间（秒） |

**使用示例**（通过自动化）：
```yaml
automation:
  - alias: "自动配对新发现的 VCX-Knob 设备"
    trigger:
      - platform: event
        event_type: bluetooth_device_found
        event_data:
          name: "VCX-Knob"
    action:
      - service: vcx_knob.pair_bluetooth_device
        data:
          device_address: "{{ trigger.event.address }}"
          timeout: 20
```

### vcx_knob.scan_bluetooth_device

扫描附近的 VCX-Knob 设备。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| timeout | int | 否 | 10 | 扫描超时时间（秒） |
| device_filter | string | 否 | VCX | 设备名称过滤器 |

**返回结果**：
```json
{
  "success": true,
  "devices": [
    {"address": "88:36:A2:D8:80:AC", "name": "VCX-Knob"}
  ],
  "count": 1
}
```

### vcx_knob.get_bluetooth_device_info

获取蓝牙设备的配对和连接状态。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| device_address | string | 是 | - | 设备 MAC 地址 |

**返回结果**：
```json
{
  "success": true,
  "device_address": "88:36:A2:D8:80:AC",
  "device_name": "VCX-Knob",
  "paired": true,
  "trusted": true,
  "connected": false,
  "ready_to_use": true
}
```

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
| 妇洗 | 触发妇洗功能 |
| 臀洗 | 触发臀洗功能 |
| 按摩 | 触发按摩功能 |
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
| 已连接 | BLE 连接状态 |

## 故障排除

### Docker 部署相关问题

#### 问题：集成显示 "scan_failed"

**可能原因**：
1. DBus 未正确挂载
2. 蓝牙适配器权限不足
3. 容器内蓝牙服务未启动

**解决步骤**：
```bash
# 1. 验证 DBus 挂载
docker exec homeassistant ls -la /run/dbus/

# 2. 验证蓝牙适配器
docker exec homeassistant hciconfig -a

# 3. 查看蓝牙日志
docker logs homeassistant | grep -i bluetooth

# 4. 重启容器
docker restart homeassistant
```

#### 问题：设备扫描成功但连接失败

**可能原因**：
1. 设备未与系统配对
2. 使用了错误的网络模式
3. 蓝牙适配器被其他应用占用

**解决步骤**：
```bash
# 1. 检查配对状态
bluetoothctl devices Paired

# 2. 手动配对设备
bluetoothctl
pair <设备MAC>
trust <设备MAC>
connect <设备MAC>
exit

# 3. 检查网络模式
docker inspect homeassistant | grep NetworkMode
# 应该显示 "host"
```

#### 问题：频繁断开连接

**可能原因**：
1. 信号强度不足
2. 蓝牙适配器不兼容
3. 其他设备干扰

**解决步骤**：
1. 查看信号强度传感器（应 > -70 dBm）
2. 尝试使用外置 USB 蓝牙适配器
3. 将 HA 服务器移近设备

### 常见问题

#### 找不到设备

1. 确保 VCX-Knob 设备已开机
2. 确保设备在蓝牙范围内（通常 < 10 米）
3. 检查 Home Assistant 日志中的蓝牙错误
4. 尝试重启 Home Assistant

#### 实体显示不可用

1. 检查 "已连接" 二进制传感器
2. 确认设备已配对
3. 查看 Home Assistant 日志中的错误消息
4. 为 `custom_components.vcx_knob` 启用调试日志：

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.vcx_knob: debug
```

#### Python 缓存问题

**问题**：修改代码后 HA 仍加载旧版本

**解决方案**：
```bash
# 清除 Python 缓存
docker exec homeassistant find /config/custom_components/vcx_knob -name "*.pyc" -delete
docker exec homeassistant find /config/custom_components/vcx_knob -name "__pycache__" -type d -exec rm -rf {} +
docker restart homeassistant
```

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
      - service: button.press
        target:
          entity_id: button.vcx_knob_close
```

## 开发

### 项目结构

```
custom_components/vcx_knob/
├── __init__.py           # 集成入口点
├── manifest.json         # 集成元数据
├── config_flow.py        # 配置流程向导
├── const.py              # 常量和实体描述
├── coordinator.py        # BLE 客户端和数据协调器
├── protocol.py           # BLE 协议实现
├── sensor.py             # 传感器实体（⚠️ 注意单数命名）
├── switch.py             # 开关实体
├── button.py             # 按钮实体
├── select.py             # 选择实体
├── binary_sensor.py      # 二进制传感器实体
├── services.yaml         # 服务定义
├── strings.json          # 英文翻译
└── translations/         # 语言文件目录
    ├── en.json
    └── zh-Hans.json
```

### 平台文件命名规范

⚠️ **重要**：Home Assistant 的平台文件必须使用单数形式：
- ✅ `sensor.py`（正确）
- ❌ `sensors.py`（错误）

这是 HA 自动加载平台的要求，使用复数命名会导致 `ModuleNotFoundError`。

## 部署检查清单

在部署前，请确认以下项目：

### 宿主机检查

- [ ] 蓝牙适配器已安装并启用
- [ ] 运行 `hciconfig -a` 确认蓝牙状态为 UP RUNNING
- [ ] 运行 `lsusb | grep -i bluetooth` 确认蓝牙硬件被识别

### Docker 配置检查

- [ ] `docker-compose.yml` 包含 `- /run/dbus:/run/dbus:ro` 卷挂载
- [ ] 使用 `network_mode: host`
- [ ] 包含 `privileged: true`（或等效的蓝牙设备权限）

### Home Assistant 检查

- [ ] HA 版本 ≥ 2024.1
- [ ] 已添加 Bluetooth 集成
- [ ] 蓝牙集成可以扫描到设备
- [ ] 已配对 VCX-Knob 设备（使用 bluetoothctl 或 HA UI）

### 集成文件检查

- [ ] 所有文件已复制到 `custom_components/vcx_knob/`
- [ ] 文件命名使用单数形式（sensor.py 而非 sensors.py）
- [ ] 重启 HA 后没有 Python 导入错误

## 调试工具

项目提供了一系列脚本来简化开发和调试工作：

### 脚本工具

```bash
# 同步代码到 Home Assistant（开发机器上运行）
./scripts/development/sync_to_ha.sh

# 检查 HA 状态（开发机器上运行）
./scripts/development/ha_test.sh

# 在 HA 宿主机上配对蓝牙设备
./scripts/ha-host/pair_device.sh
```

详见 [脚本工具文档](scripts/README.md)。

### 蓝牙调试

```bash
# 在宿主机上
bluetoothctl
# 进入交互模式
scan on
# 查看设备
menu gatt
# 连接到设备
connect XX:XX:XX:XX:XX:XX
# 列出服务
list-attributes
```

### 日志调试

```bash
# 查看 HA 日志
docker logs -f homeassistant

# 只看 vcx_knob 相关
docker logs homeassistant | grep vcx_knob

# 实时查看
docker logs -f homeassistant | grep vcx_knob
```

### 容器内调试

```bash
# 进入容器
docker exec -it homeassistant /bin/bash

# 测试蓝牙
hciconfig -a
python3 -c "from homeassistant.components import bluetooth; print('OK')"
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

## 开发日志

### 当前开发进度 (2026-03)

#### ✅ 已完成
- BLE 连接和断开管理
- 设备状态轮询（6种状态包解析）
- 13个传感器实体（信号强度、百分比、时间等）
- 11个开关实体（冲水、座圈、气泡、热风等）
- 14个按钮实体（大冲水、小冲水、妇洗、臀洗等）
- 7个选择实体（水温、座温、风温、水量等）
- 1个连接状态二进制传感器
- 配置流程向导（设备扫描、配对、设置）
- 双语支持（英语/简体中文）
- Docker 部署支持

#### 🚧 进行中
- 蓝牙配对服务调试（通过 UI 进行设备配对）
- 服务调用优化
- 错误处理和日志完善
- 连接稳定性改进

#### 📋 待完成
- 完整的用户文档
- 自动化示例完善
- 性能优化
- HACS 发布准备

### 技术栈
- Python 3.13
- Home Assistant 2024.1+
- bleak (BLE 库)
- voluptuous (数据验证)

### 开发环境
- 本地开发：macOS + Python 3.13
- 测试环境：Docker 部署的 Home Assistant
- 蓝牙设备：VCX-Knob 智能马桶

### 相关文档
- 博客：[记一次Home Assistant自定义集成开发踩坑](https://nnnnzs.cn/2026/03/07/记一次Home-Assistant自定义集成开发踩坑/)
- 项目文档：详见 `docs/` 目录
