# Docker 蓝牙部署指南

如果您使用 Docker 部署 Home Assistant，需要正确配置蓝牙支持。

## 1. 蓝牙设备权限问题

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
      - /run/dbus:/run/dbus:ro  # 必须添加此行
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    privileged: true
    network_mode: host  # 推荐使用 host 网络模式
```

**验证方法**：
```bash
docker exec -it homeassistant ls -la /run/dbus/
# 应该看到 system_bus_socket 文件
```

## 2. 蓝牙适配器未映射

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
docker exec homeassistant hciconfig -a
# 应该看到类似输出：
# hci0:   Type: Primary  Bus: USB
#         UP RUNNING
#         BD Address: XX:XX:XX:XX:XX:XX
```

## 3. 蓝牙设备配对问题

**问题**：集成显示 `Write not permitted`、按钮显示为灰色，或连接后无法控制设备。

**重要说明**：蓝牙**配对**和**连接**是两个不同的操作：
- **连接**：只是建立通信连接，可以读取设备状态
- **配对**：建立信任关系，**允许写入控制命令**（这是必需的！）

如果你的按钮显示为灰色，说明设备已连接但未配对。

### 方法 1：通过 VCX-Knob 集成向导配对（推荐）

1. 前往 **设置 → 设备与服务** → **添加集成** → 搜索 **VCX-Knob**
2. 集成会在配置流程中自动检测配对状态
3. 如果未配对，按照屏幕上的说明操作

也可以使用 HA 服务：
- `vcx_knob.pair_bluetooth_device` — 配对设备
- `vcx_knob.scan_bluetooth_device` — 扫描设备
- `vcx_knob.get_bluetooth_device_info` — 查看配对状态

### 方法 2：使用 Home Assistant 蓝牙集成

1. **设置 → 设备与服务 → 添加集成** → 搜索并添加 **Bluetooth** 集成
2. 在蓝牙集成中点击 **配置** → **扫描设备** → 找到 **VCX-Knob** → **配对**
3. 输入 PIN 码（如果需要，常见为 `0000`、`1234`）

### 方法 3：使用命令行配对（高级用户）

在 Home Assistant **宿主机**上执行（Docker 容器外）：

```bash
# 1. 启动 bluetoothctl 交互模式
bluetoothctl

# 2. 开启扫描
scan on

# 3. 等待发现 VCX-Knob 设备（记录 MAC 地址）

# 4. 配对设备
pair XX:XX:XX:XX:XX:XX

# 5. 当提示时，在设备上确认配对（通常需要按下按钮）

# 6. 配对成功后，信任设备
trust XX:XX:XX:XX:XX:XX

# 7. 验证配对状态
info XX:XX:XX:XX:XX:XX
# 应该显示：Paired: yes  Trusted: yes  Connected: yes

# 8. 退出
exit
```

**配对失败的常见原因**：
- 设备距离太远（请将设备靠近 Home Assistant 服务器到 1 米内）
- 设备未在配对模式（有些设备需要长按按钮进入配对模式）
- 需要输入 PIN 码（常见 PIN：0000、1234、8888）
- 设备之前与其他设备配对过，需要先删除旧配对

## 4. Home Assistant 版本兼容性

本集成需要 Home Assistant **2024.1** 或更高版本。

| HA 版本 | 支持状态 | 说明 |
|---------|---------|------|
| 2024.1+ | 完全支持 | 推荐版本 |
| 2023.11 - 2023.12 | 不支持 | API 不兼容 |
| 2023.10 及以下 | 不支持 | API 不兼容 |

## 5. 网络模式问题

**问题**：蓝牙扫描功能正常，但无法连接设备。

**原因**：使用 `bridge` 或 `nat` 网络模式可能导致蓝牙连接问题。

**解决方案**：使用 `network_mode: host`

```yaml
services:
  homeassistant:
    network_mode: host  # 推荐用于蓝牙集成
```

**注意事项**：
- `host` 网络模式会移除网络隔离，容器与宿主机共享网络栈
- 如果需要使用反向代理，请直接使用宿主机 IP 而非容器 IP

## 部署检查清单

### 宿主机

- [ ] 蓝牙适配器已安装并启用
- [ ] 运行 `hciconfig -a` 确认蓝牙状态为 UP RUNNING
- [ ] 运行 `lsusb | grep -i bluetooth` 确认蓝牙硬件被识别

### Docker 配置

- [ ] `docker-compose.yml` 包含 `- /run/dbus:/run/dbus:ro` 卷挂载
- [ ] 使用 `network_mode: host`
- [ ] 包含 `privileged: true`（或等效的蓝牙设备权限）

### Home Assistant

- [ ] HA 版本 >= 2024.1
- [ ] 已添加 Bluetooth 集成
- [ ] 蓝牙集成可以扫描到设备
- [ ] 已配对 VCX-Knob 设备（使用 bluetoothctl 或 HA UI）

### 集成文件

- [ ] 所有文件已复制到 `custom_components/vcx_knob/`
- [ ] 重启 HA 后没有 Python 导入错误
