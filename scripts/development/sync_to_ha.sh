#!/bin/bash

# 本地同步脚本到 Home Assistant
# 使用方法:
# 1. 修改 HA_HOST 和 HA_CONFIG_DIR 为你的实际值
# 2. chmod +x sync_to_ha.sh
# 3. ./sync_to_ha.sh

HA_HOST="192.168.1.80"
HA_USER="root"
HA_CONFIG_DIR="/root/docker_v/homeassistant/config"

# 获取项目根目录 (向上两级从 scripts/development 到项目根)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOCAL_DIR="${PROJECT_ROOT}/custom_components/vcx_knob"

echo "正在同步到 Home Assistant..."
echo "本地目录: ${LOCAL_DIR}"
echo "远程目录: ${HA_USER}@${HA_HOST}:${HA_CONFIG_DIR}/custom_components/vcx_knob/"

# 使用 rsync 同步文件
rsync -avz --delete \
    "${LOCAL_DIR}/" \
    ${HA_USER}@${HA_HOST}:${HA_CONFIG_DIR}/custom_components/vcx_knob/

echo "同步完成！"
echo "请在 Home Assistant 中点击: 设置 → 系统 → 右上角菜单 → 重启"
