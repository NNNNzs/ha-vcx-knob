# VCX-Knob 配对指南 - NAS + Docker 环境

## 你的环境
- Home Assistant 运行在 Docker 中（NAS：linke-me-mini）
- 蓝牙适配器：Intel AX201 (D4:AB:61:BB:DE:A5)
- VCX-Knob 设备 MAC：88:36:A2:D8:80:AC

## 快速配对步骤

### 步骤 1：SSH 到你的 NAS

```bash
ssh root@192.168.1.80
```

### 步骤 2：启动 bluetoothctl

```bash
bluetoothctl
```

你会看到提示符变为：`[bluetooth]#`

### 步骤 3：扫描设备

```
[bluetooth]# scan on
```

等待几秒，你应该会看到：
```
Device 88:36:A2:D8:80:AC VCX-Knob
```

### 步骤 4：配对设备

```
[bluetooth]# pair 88:36:A2:D8:80:AC
```

**重要**：
- 此时如果设备上有配对按钮，**请按下按钮**
- 或者查看设备指示灯是否有闪烁
- 等待配对完成（可能需要 5-10 秒）

### 步骤 5：验证配对

```
[bluetooth]# info 88:36:A2:D8:80:AC
```

应该显示：
```
Paired: yes      ← 必须是 yes
Trusted: yes     ← 必须是 yes
Connected: yes
```

如果显示 `Paired: no`，请：
1. 将设备靠近 NAS（1 米以内）
2. 在设备上进入配对模式（查看说明书）
3. 重新执行 `pair` 命令

### 步骤 6：信任设备

```
[bluetooth]# trust 88:36:A2:D8:80:AC
```

### 步骤 7：退出

```
[bluetooth]# quit
```

## 配对成功后

1. 在 Home Assistant 中**删除现有的 VCX-Knob 集成**
2. **重新添加** VCX-Knob 集成
3. 按钮应该不再是灰色
4. 可以正常控制设备了

## 常见问题

### Q: 配对时显示 "Host key verification failed"

A: 这表示设备需要你**在设备上确认配对**：
1. 查看设备是否有配对按钮
2. 按下配对按钮
3. 或者在设备菜单中进入配对模式
4. 重新执行 `pair` 命令

### Q: 配对后仍然显示 `Paired: no`

A: 可能原因：
1. 设备距离太远 - 移近到 1 米以内
2. 设备未在配对模式 - 查看设备说明书
3. 设备已与其他设备配对 - 先取消原配对

### Q: 我没有设备物理按钮怎么办？

A: 尝试以下方法：
1. **使用手机蓝牙配对**（最简单）
   - 打开手机蓝牙
   - 找到 VCX-Knob 设备
   - 点击配对
   - 配对成功后，NAS 系统会自动信任该设备

2. **尝试不同的配对流程**
   ```
   bluetoothctl
   agent KeyboardDisplayOnly
   pair 88:36:A2:D8:80:AC
   ```

3. **取消原配对后重试**
   ```
   bluetoothctl
   remove 88:36:A2:D8:80:AC
   pair 88:36:A2:D8:80:AC
   ```

## 自动配对脚本

你也可以使用提供的自动配对脚本：

```bash
# 在 NAS 上执行
chmod +x pair_device.sh
./pair_device.sh
```

脚本会自动：
1. 扫描设备
2. 配对设备
3. 信任设备
4. 验证配对状态

## 验证配对成功的最简单方法

在 Home Assistant 中：
1. 添加 VCX-Knob 集成
2. 检查**按钮**实体
3. 如果按钮**可以点击**（不是灰色）= 配对成功 ✅
4. 如果按钮**仍然是灰色**= 配对失败 ❌

## 配对只需要一次

配对信息会永久保存在 NAS 的蓝牙系统中：
- 重启 Home Assistant 不会影响
- 重启 NAS 不会影响
- 只需要配对一次

## 需要帮助？

如果上述方法都无法配对成功：
1. 查看设备说明书关于蓝牙配对的章节
2. 尝试联系设备厂商
3. 在 GitHub 上提交 Issue：https://github.com/NNNNzs/ha-vcx-knob/issues
