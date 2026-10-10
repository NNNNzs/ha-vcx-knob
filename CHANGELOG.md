# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.5] - 2026-10-10

### Fixed
- 修复 HACS Release ZIP 包结构：压缩包根目录直接包含集成文件，避免安装后多嵌套一层

## [1.0.4] - 2026-10-07

### Added
- 新增有人入座二进制传感器（`binary_sensor.you_ren_ru_zuo` / `occupancy`），逆向解析 Type 01 状态帧第 4 字节 Bit 1 判定座圈微动/重力感应
- 补充有人入座传感器中英文翻译与实体描述映射

### Changed
- 完善协议解析，将状态帧中误标为脚感的传感器状态细化为真实入座状态

- 将冲水、座圈、气泡、热风从 switch 实体改为 button 实体，更符合一次性操作的语义
- 将 entity_category 从字符串改为 EntityCategory 枚举，适配新版 HA
- 修复 BLE 写入方式（改为无响应写入），优化实体可用性检测
- 更新 BLE Service UUID 为 `0000FFA0`（修正此前文档中的 `0000FFF0`）
- 扩展传感器实体至 18 个（新增蓝牙地址、座圈关闭强度、小冲上冲时间、水压、氛围灯亮度）
- 新增配对状态二进制传感器（共 2 个二进制传感器）
- 扩展按钮实体至 15 个（新增妇洗、臀洗、按摩、气泡、停止、烘干、翻盖、翻圈、关闭、润壁、自洁）
- 补全所有 button 实体的中英文翻译
- 开发环境从 macOS 迁移至零刻 Mini (Debian 12)

### Fixed
- 修复集成加载失败（软链接不可达、缺少 entity_description 属性等）
- 修复 BLE 写入方式，使用无响应写入提升兼容性

### Removed
- 删除过时的 STATUS.md 文档
- 删除测试脚本 test_device_pairing.py

## [1.0.0] - 2026-XX-XX

### Added
- Initial release
- Full BLE protocol implementation for VCX-Knob devices
- Config flow with device scanning and pairing
- 18 sensor entities for monitoring device state
- 7 switch entities for on/off control
- 15 button entities for one-time actions
- 7 select entities for multi-option settings
- 2 binary sensors (BLE connection and pairing status)
- Bilingual support (English and Simplified Chinese)
- Auto-reconnection and auto-connect functionality
- Bluetooth pairing service
- Docker deployment support
