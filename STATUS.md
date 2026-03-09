# VCX-Knob Home Assistant 集成开发状态

> **最后更新**: 2026-03-08

## 项目概述

这是一个用于 VCX-Knob 智能马桶的 Home Assistant 自定义集成，通过蓝牙低功耗 (BLE) 直接与设备通信。

## ✅ 已完成功能

### 核心功能
- ✅ BLE 连接和自动重连
- ✅ 设备扫描和发现
- ✅ 蓝牙配对服务（通过 HA UI 或服务调用）
- ✅ 设备状态轮询（6种状态包解析）
- ✅ 双语支持（英语/简体中文）

### 实体支持
- ✅ **13个传感器**：信号强度、百分比、时间、距离等
- ✅ **11个开关**：冲水、座圈、气泡、热风、雷达等
- ✅ **14个按钮**：大冲水、小冲水、妇洗、臀洗、烘干等
- ✅ **7个选择**：水温、座温、风温、水量、热风档位、灯光亮度、雷达灵敏度
- ✅ **1个二进制传感器**：BLE 连接状态

### 服务
- ✅ `vcx_knob.pair_bluetooth_device` - 蓝牙配对服务
- ✅ `vcx_knob.scan_bluetooth_device` - 扫描设备服务
- ✅ `vcx_knob.get_bluetooth_device_info` - 获取设备信息服务

### 部署支持
- ✅ Docker 部署支持（DBus 挂载配置）
- ✅ Python 3.13 兼容性
- ✅ Home Assistant 2024.1+ 支持

## 🚧 当前工作

### 正在优化
- 错误处理和日志完善
- 连接稳定性改进
- 服务调用优化

## 📋 待完成

### 文档
- [ ] 完善自动化示例
- [ ] 添加更多故障排除指南
- [ ] 准备 HACS 发布说明

### 测试
- [ ] 完整的端到端测试
- [ ] 多设备场景测试
- [ ] 长时间运行稳定性测试

## 📁 项目结构

```
ha-vcx-knob/
├── custom_components/vcx_knob/
│   ├── __init__.py              # 集成入口
│   ├── manifest.json            # 集成清单
│   ├── config_flow.py           # 配置流程
│   ├── const.py                 # 常量定义
│   ├── coordinator.py           # BLE 客户端和协调器
│   ├── protocol.py              # BLE 协议实现
│   ├── sensor.py                # 传感器实体
│   ├── switch.py                # 开关实体
│   ├── button.py                # 按钮实体
│   ├── select.py                # 选择实体
│   ├── binary_sensor.py         # 二进制传感器
│   ├── bluetooth_pairing.py     # 蓝牙配对模块
│   ├── services.yaml            # 服务定义
│   ├── strings.json             # 英文翻译
│   └── translations/
│       ├── en.json
│       └── zh-Hans.json
├── docs/                        # 配对指南文档
│   ├── PAIRING_NAS.md
│   ├── QUICK_START_PAIRING.md
│   └── PAIRING_GUI.md
├── scripts/                     # 脚本工具集
│   ├── README.md                # 脚本使用说明
│   ├── ha-host/                 # HA 宿主机脚本
│   │   └── pair_device.sh       # 蓝牙配对工具
│   └── development/             # 开发调试脚本
│       ├── sync_to_ha.sh        # 同步代码到 HA
│       ├── ha_test.sh           # HA 状态调试
│       ├── test_ble_in_ha.sh    # BLE 功能测试
│       └── ble_scan_test.py     # 本地 BLE 扫描测试
├── CLAUDE.md                    # Claude Code 指导
├── STATUS.md                    # 本文档
├── DESIGN.md                    # 设计文档
├── REQUIREMENTS.md              # 需求文档
└── README.md                    # 项目说明
```

## 🔧 开发环境

- **本地开发**: macOS + Python 3.13
- **测试环境**: Docker 部署的 Home Assistant
- **蓝牙设备**: VCX-Knob 智能马桶
- **蓝牙适配器**: Intel AX201

## 🐛 已知问题

### BLE 配对
- 部分设备需要在配对时按下物理按钮
- 配对后需要重启集成才能生效

### 连接稳定性
- 信号弱时可能频繁断开重连
- 建议保持设备在 5 米范围内

## 📝 开发日志

### 2026-03-08
- 清理项目结构，删除重复文档
- 合并配对脚本为单一工具
- 更新开发状态文档

### 2026-03-07
- 添加蓝牙配对服务
- 完善配置流程 UI
- 添加配对文档

### 2026-03-06
- 完成所有实体类型实现
- 修复 Python 3.13 兼容性问题
- 添加 DBus 支持

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/NNNNzs/ha-vcx-knob/issues)
- **博客**: [nnnnzs.cn](https://nnnnzs.cn)
