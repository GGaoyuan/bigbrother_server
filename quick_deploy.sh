#!/bin/bash
# 快速部署脚本 - 用于测试

set -e

echo "=== Flask应用快速部署测试 ==="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本"
    exit 1
fi

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    yum install -y python3 python3-pip
fi

# 检查Nginx
if ! command -v nginx &> /dev/null; then
    echo "安装Nginx..."
    yum install -y nginx
fi

# 启动Nginx
echo "启动Nginx..."
systemctl start nginx
systemctl enable nginx

# 检查Nginx状态
echo "检查Nginx状态..."
systemctl status nginx --no-pager

echo "基础环境检查完成，现在可以运行Python部署脚本"
echo "运行命令: sudo python3 app_deploy.py" 