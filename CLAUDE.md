# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 **VCX-Knob 智能马桶的 Home Assistant 自定义集成**，通过蓝牙低功耗 (BLE) 直接与设备通信，无需云端或 MQTT。

## 开发设置

### 本地开发环境

**项目位置**：`/root/project/ha-vcx-knob`

**Home Assistant 配置目录**：`/vol2/1000/docker_v/homeassistant/config`

**部署方式**：已使用软链接将项目目录链接到 HA 配置目录，代码修改实时生效（需重启 HA）。

### 同步代码到 Home Assistant

**重要**：由于已配置软链接，代码会自动同步，无需手动复制！

```bash
# 软链接已配置：
# /vol2/1000/docker_v/homeassistant/config/custom_components/vcx_knob -> /root/project/ha-vcx-knob/custom_components/vcx_knob
```

如果你需要手动同步（例如软链接失效）：

```bash
# 同步代码到 HA
./scripts/development/sync_to_ha.sh

# 重启 HA
./scripts/development/restart_ha.sh
```

### 配置 hass-cli

hass-cli 是 Home Assistant 的命令行工具，方便调试和控制。

**安装**（如果尚未安装）：
```bash
pip install homeassistant-cli
```

**配置认证**：

1. **获取访问令牌**：
   - 打开浏览器访问 HA：`http://localhost:8123`
   - 点击左下角用户头像 → 滚动到底部 → "创建令牌"
   - 输入令牌名称（如：`hass-cli-dev`）
   - 复制生成的令牌

2. **设置配置文件**（已创建模板）：
   ```bash
   # 编辑配置文件
   nano ~/.config/hass-cli/config.json

   # 替换 YOUR_TOKEN_HERE 为你的令牌
   ```

3. **验证配置**：
   ```bash
   hass-cli info
   hass-cli entity list | grep vcx_knob
   ```

**或使用配置向导**：
```bash
./scripts/development/setup_hass_cli.sh
```

### 重启 Home Assistant

修改代码后需要重启 HA：

```bash
# 使用便捷脚本
./scripts/development/restart_ha.sh

# 或直接使用 docker 命令
docker restart homeassistant

# 查看启动日志
docker logs -f homeassistant
```

### 测试和调试

```bash
# 检查 HA 状态
./scripts/development/ha_test.sh

# 查看 vcx_knob 相关日志
docker logs homeassistant | grep -i vcx_knob

# 实时查看日志
docker logs -f homeassistant | grep -i vcx_knob

# 清除 Python 缓存（如果修改未生效）
docker exec homeassistant find /config/custom_components/vcx_knob -name "*.pyc" -delete
```

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

- `sensor.py` - 13 个传感器实体（信号强度、百分比、时间、距离）
- `switch.py` - 11 个开关实体（开/关控制）
- `button.py` - 3 个按钮实体（一次性操作）
- `select.py` - 7 个选择实体（多选项设置）
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
2. 在相应的实体文件（`sensor.py`、`switch.py` 等）中创建实体类
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
- 开发脚本：`/scripts/development/`
- 文档：`DESIGN.md`、`REQUIREMENTS.md`、`README.md`
## 参考
微信小程序反编译程序地址 /root/project/skj-toilet
nodejs 后端 /root/project/skj-toilet/nodejs-service ，未经测试，可行度不高

## 依赖项

- `bleak>=0.21.0` - 跨平台 BLE 库
- Home Assistant 2023.11.0+

## 双语支持

本集成支持英语和简体中文。添加新实体或选项时，务必同时添加到 `strings.json` 和 `translations/zh-Hans.json` 的翻译。

## hass-cli 常用命令

```bash
# 查看 HA 信息
hass-cli info

# 列出所有实体
hass-cli entity list

# 列出 vcx_knob 相关实体
hass-cli entity list | grep vcx_knob

# 调用服务
hass-cli service call homeassistant.restart {}

# 查看实体状态
hass-cli state get switch.vcx_knob_flush

# 设置实体状态（测试用）
hass-cli state set switch.vcx_knob_flush "on"
```
