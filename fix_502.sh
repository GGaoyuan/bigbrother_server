#!/bin/bash
# 快速修复502 Bad Gateway错误

echo "=== 修复502 Bad Gateway错误 ==="
echo ""

# 1. 重启Flask应用服务
echo "1. 重启Flask应用服务..."
systemctl restart bigbrother_server.service
sleep 3

# 2. 检查服务状态
echo "2. 检查Flask应用服务状态..."
systemctl status bigbrother_server.service --no-pager
echo ""

# 3. 重启Nginx
echo "3. 重启Nginx..."
systemctl restart nginx
sleep 2

# 4. 检查Nginx状态
echo "4. 检查Nginx状态..."
systemctl status nginx --no-pager
echo ""

# 5. 检查端口监听
echo "5. 检查端口监听..."
echo "端口5000 (Gunicorn):"
netstat -tlnp | grep 5000 || echo "端口5000未监听"
echo ""

echo "端口80 (Nginx):"
netstat -tlnp | grep 80 || echo "端口80未监听"
echo ""

# 6. 测试连接
echo "6. 测试连接..."
echo "测试Gunicorn (127.0.0.1:5000):"
curl -I http://127.0.0.1:5000/health 2>/dev/null || echo "Gunicorn连接失败"
echo ""

echo "测试Nginx (127.0.0.1:80):"
curl -I http://127.0.0.1/health 2>/dev/null || echo "Nginx连接失败"
echo ""

# 7. 检查防火墙
echo "7. 配置防火墙..."
firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || echo "防火墙配置失败"
firewall-cmd --reload 2>/dev/null || echo "防火墙重载失败"
echo ""

# 8. 检查SELinux
echo "8. 配置SELinux..."
setsebool -P httpd_can_network_connect 1 2>/dev/null || echo "SELinux配置失败"
echo ""

# 9. 检查日志
echo "9. 检查错误日志..."
echo "Flask应用错误日志 (最近5行):"
if [ -f "/var/log/bigbrother_server/error.log" ]; then
    tail -5 /var/log/bigbrother_server/error.log
else
    echo "应用错误日志文件不存在"
fi
echo ""

echo "Nginx错误日志 (最近5行):"
if [ -f "/var/log/nginx/error.log" ]; then
    tail -5 /var/log/nginx/error.log
else
    echo "Nginx错误日志文件不存在"
fi
echo ""

echo "=== 修复完成 ==="
echo ""
echo "现在请尝试访问: http://49.235.60.18/"
echo "如果仍然有问题，请运行: ./debug.sh" 