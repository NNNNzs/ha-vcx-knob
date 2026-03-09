# VCX-Knob 脚本工具集

本目录包含用于开发和部署的各类脚本工具。

## 目录结构

```
scripts/
├── ha-host/              # Home Assistant 宿主机运行脚本
│   └── pair_device.sh    # 蓝牙配对工具
│
└── development/          # 开发调试脚本
    ├── sync_to_ha.sh     # 同步代码到 HA
    ├── ha_test.sh        # HA 状态调试
    ├── test_ble_in_ha.sh # BLE 功能测试
    └── ble_scan_test.py  # 本地 BLE 扫描测试
```

## HA 宿主机脚本 (ha-host/)

这些脚本需要在 **Home Assistant 的宿主机**上运行，用于设备配对等操作。

### pair_device.sh - 蓝牙配对工具

用于在宿主机上配对 VCX-Knob 蓝牙设备。

**使用方法：**

```bash
# 方法 1: 自动扫描发现（推荐）
cd scripts/ha-host
./pair_device.sh

# 方法 2: 手动指定 MAC 地址
# 编辑脚本中的 DEVICE_MAC 变量
./pair_device.sh
```

**功能：**
- 自动扫描发现 VCX-Knob 设备
- 执行蓝牙配对
- 设置设备信任
- 验证配对状态
- 提供详细的错误诊断

**注意事项：**
- 必须在 HA 宿主机上运行（不是容器内）
- 需要安装 `bluez` 包：`apt-get install bluez`
- 设备距离应 < 1 米
- 部分设备需要在配对时按下物理按钮

## 开发调试脚本 (development/)

这些脚本在**开发机器**上运行，用于代码同步和调试。

### sync_to_ha.sh - 同步代码到 HA

将本地修改的代码同步到远程 Home Assistant 服务器。

**使用方法：**

```bash
# 1. 修改脚本中的连接信息
# HA_HOST="192.168.1.80"       # HA 服务器地址
# HA_USER="root"                # SSH 用户名
# HA_CONFIG_DIR="/path/to/config"  # HA 配置目录

# 2. 运行同步
cd scripts/development
./sync_to_ha.sh
```

**说明：**
- 使用 rsync 增量同步
- 自动删除远程多余文件
- 同步后需要重启 HA

### ha_test.sh - HA 状态调试

检查 Home Assistant 和蓝牙适配器的运行状态。

**使用方法：**

```bash
cd scripts/development
./ha_test.sh
```

**检查项目：**
- 服务器连接状态
- HA 容器运行状态
- 蓝牙适配器状态
- 集成文件完整性
- Python 模块导入
- 最新日志输出

### test_ble_in_ha.sh - BLE 功能测试

在 HA 容器内测试蓝牙扫描功能。

**使用方法：**

```bash
cd scripts/development
./test_ble_in_ha.sh
```

**测试内容：**
- 蓝牙适配器配置
- 蓝牙相关日志
- HA 蓝牙模块状态

### ble_scan_test.py - 本地 BLE 扫描

在开发机器上直接测试蓝牙扫描（不需要 HA）。

**使用方法：**

```bash
cd scripts/development
python3 ble_scan_test.py
```

**依赖：**
```bash
pip install bleak
```

## 快速开始

### 首次部署

```bash
# 1. 同步代码到 HA
./scripts/development/sync_to_ha.sh

# 2. 在 HA 宿主机上配对设备
ssh root@your-ha-host
./scripts/ha-host/pair_device.sh

# 3. 重启 HA
ssh root@your-ha-host 'docker restart homeassistant'
```

### 开发调试循环

```bash
# 1. 修改代码
# 2. 同步到 HA
./scripts/development/sync_to_ha.sh

# 3. 检查状态
./scripts/development/ha_test.sh

# 4. 查看日志
ssh root@your-ha-host 'docker logs -f homeassistant | grep vcx_knob'
```

## 故障排除

### 脚本无法执行

```bash
# 添加执行权限
chmod +x scripts/ha-host/*.sh
chmod +x scripts/development/*.sh
```

### SSH 连接失败

- 检查 `HA_HOST` 和 `HA_USER` 配置
- 确保开发机器可以 SSH 到 HA 宿主机
- 检查防火墙设置

### 蓝牙配对失败

- 确保在**宿主机**上运行（不是容器内）
- 检查蓝牙适配器状态：`hciconfig -a`
- 设备距离应 < 1 米
- 部分设备需要进入配对模式

## 相关文档

- [配对指南](../docs/PAIRING_NAS.md)
- [主 README](../README.md)
- [开发状态](../STATUS.md)
