# 故障排除

## Docker 部署相关问题

### 问题：集成显示 "scan_failed"

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

详见 [Docker 蓝牙部署指南](DOCKER_SETUP.md)。

### 问题：设备扫描成功但连接失败

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

详见 [蓝牙设备配对](DOCKER_SETUP.md#3-蓝牙设备配对问题)。

### 问题：频繁断开连接

**可能原因**：
1. 信号强度不足
2. 蓝牙适配器不兼容
3. 其他设备干扰

**解决步骤**：
1. 查看信号强度传感器（应 > -70 dBm）
2. 尝试使用外置 USB 蓝牙适配器
3. 将 HA 服务器移近设备

## 常见问题

### 找不到设备

1. 确保 VCX-Knob 设备已开机
2. 确保设备在蓝牙范围内（通常 < 10 米）
3. 检查 Home Assistant 日志中的蓝牙错误
4. 尝试重启 Home Assistant

### 实体显示不可用

1. 检查 "蓝牙连接" 二进制传感器
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

### Python 缓存问题

**问题**：修改代码后 HA 仍加载旧版本

**解决方案**：
```bash
# 清除 Python 缓存
docker exec homeassistant find /config/custom_components/vcx_knob -name "*.pyc" -delete
docker exec homeassistant find /config/custom_components/vcx_knob -name "__pycache__" -type d -exec rm -rf {} +
docker restart homeassistant
```
