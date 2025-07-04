#!/bin/bash
# OpenCloudOS Flask应用快速部署脚本

set -e

# 配置变量
APP_NAME="bigbrother_server"
APP_USER="flask"
APP_PORT="5000"
APP_DIR="/opt/$APP_NAME"
VENV_DIR="/home/$APP_USER/venv"

echo "=== OpenCloudOS Flask应用部署脚本 ==="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本"
    exit 1
fi

# 检查系统
echo "检查系统环境..."
if [ ! -f /etc/os-release ]; then
    echo "警告: 无法确定系统类型"
else
    if grep -q "OpenCloudOS" /etc/os-release; then
        echo "检测到OpenCloudOS系统"
    else
        echo "警告: 当前系统可能不是OpenCloudOS"
    fi
fi

# 更新系统包
echo "更新系统包..."
yum update -y

# 安装系统依赖
echo "安装系统依赖..."
yum install -y python3 python3-pip python3-devel gcc gcc-c++ make \
    openssl-devel libffi-devel nginx supervisor curl

# 创建应用用户
echo "创建应用用户..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d /home/$APP_USER $APP_USER
    mkdir -p /home/$APP_USER
    chown $APP_USER:$APP_USER /home/$APP_USER
else
    echo "用户 $APP_USER 已存在"
fi

# 创建Python虚拟环境
echo "创建Python虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
chown -R $APP_USER:$APP_USER $VENV_DIR

# 安装Python依赖
echo "安装Python依赖..."
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r requirements.txt
$VENV_DIR/bin/pip install gunicorn gevent psutil

# 创建应用目录
echo "创建应用目录..."
mkdir -p $APP_DIR
cp -r ./* $APP_DIR/
chown -R $APP_USER:$APP_USER $APP_DIR
chmod +x $APP_DIR/app.py

# 创建Gunicorn配置
echo "创建Gunicorn配置..."
cp gunicorn.conf.py $APP_DIR/
chown $APP_USER:$APP_USER $APP_DIR/gunicorn.conf.py

# 创建日志目录
mkdir -p /var/log/$APP_NAME
chown $APP_USER:$APP_USER /var/log/$APP_NAME

# 创建systemd服务
echo "创建systemd服务..."
cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=$APP_NAME Flask Application
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
systemctl daemon-reload
systemctl enable $APP_NAME.service

# 创建Nginx配置
echo "创建Nginx配置..."
cp nginx.conf /etc/nginx/conf.d/$APP_NAME.conf

# 启动并启用服务
echo "启动服务..."
systemctl start nginx
systemctl enable nginx
systemctl start $APP_NAME.service

# 检查服务状态
echo "检查服务状态..."
sleep 3
systemctl status $APP_NAME.service --no-pager
systemctl status nginx --no-pager

# 测试应用
echo "测试应用..."
sleep 5
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "应用部署成功！"
    echo "访问地址: http://localhost"
    echo "健康检查: http://localhost/health"
else
    echo "应用可能未正常启动，请检查日志"
fi

echo ""
echo "=== 部署完成 ==="
echo "应用名称: $APP_NAME"
echo "应用目录: $APP_DIR"
echo "服务名称: $APP_NAME.service"
echo ""
echo "常用命令:"
echo "  查看服务状态: systemctl status $APP_NAME.service"
echo "  重启服务: systemctl restart $APP_NAME.service"
echo "  查看日志: journalctl -u $APP_NAME.service -f"
echo "  查看nginx状态: systemctl status nginx"
echo "  健康检查: curl http://localhost/health" 