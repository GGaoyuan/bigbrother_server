#!/bin/bash
# 调试脚本 - 排查502 Bad Gateway错误

echo "=== 502错误调试脚本 ==="
echo "服务器IP: http://49.235.60.18/"
echo ""

# 1. 检查服务状态
echo "1. 检查服务状态..."
echo "--- Flask应用服务 ---"
systemctl status bigbrother_server.service --no-pager
echo ""

echo "--- Nginx服务 ---"
systemctl status nginx --no-pager
echo ""

# 2. 检查端口监听
echo "2. 检查端口监听..."
echo "--- 端口5000 (Gunicorn) ---"
netstat -tlnp | grep 5000 || echo "端口5000未监听"
echo ""

echo "--- 端口80 (Nginx) ---"
netstat -tlnp | grep 80 || echo "端口80未监听"
echo ""

# 3. 检查进程
echo "3. 检查进程..."
echo "--- Gunicorn进程 ---"
ps aux | grep gunicorn || echo "未找到Gunicorn进程"
echo ""

echo "--- Nginx进程 ---"
ps aux | grep nginx || echo "未找到Nginx进程"
echo ""

# 4. 检查日志
echo "4. 检查日志..."
echo "--- Flask应用日志 (最近10行) ---"
if [ -f "/var/log/bigbrother_server/error.log" ]; then
    tail -10 /var/log/bigbrother_server/error.log
else
    echo "应用错误日志文件不存在"
fi
echo ""

echo "--- Nginx错误日志 (最近10行) ---"
if [ -f "/var/log/nginx/error.log" ]; then
    tail -10 /var/log/nginx/error.log
else
    echo "Nginx错误日志文件不存在"
fi
echo ""

echo "--- Nginx访问日志 (最近10行) ---"
if [ -f "/var/log/nginx/bigbrother_server_access.log" ]; then
    tail -10 /var/log/nginx/bigbrother_server_access.log
else
    echo "Nginx访问日志文件不存在"
fi
echo ""

# 5. 检查配置文件
echo "5. 检查配置文件..."
echo "--- Nginx配置 ---"
if [ -f "/etc/nginx/conf.d/bigbrother_server.conf" ]; then
    cat /etc/nginx/conf.d/bigbrother_server.conf
else
    echo "Nginx配置文件不存在"
fi
echo ""

echo "--- Gunicorn配置 ---"
if [ -f "/opt/bigbrother_server/gunicorn.conf.py" ]; then
    cat /opt/bigbrother_server/gunicorn.conf.py
else
    echo "Gunicorn配置文件不存在"
fi
echo ""

# 6. 测试连接
echo "6. 测试连接..."
echo "--- 测试本地Gunicorn连接 ---"
curl -I http://127.0.0.1:5000/health 2>/dev/null || echo "无法连接到Gunicorn"
echo ""

echo "--- 测试本地Nginx连接 ---"
curl -I http://127.0.0.1/health 2>/dev/null || echo "无法连接到Nginx"
echo ""

# 7. 检查防火墙
echo "7. 检查防火墙..."
echo "--- 防火墙状态 ---"
systemctl status firewalld --no-pager 2>/dev/null || echo "防火墙服务不存在"
echo ""

echo "--- 防火墙规则 ---"
firewall-cmd --list-all 2>/dev/null || echo "无法获取防火墙规则"
echo ""

# 8. 检查SELinux
echo "8. 检查SELinux..."
echo "--- SELinux状态 ---"
getenforce 2>/dev/null || echo "SELinux未安装"
echo ""

echo "=== 调试完成 ==="
echo ""
echo "常见解决方案:"
echo "1. 如果Gunicorn未运行: sudo systemctl start bigbrother_server.service"
echo "2. 如果Nginx未运行: sudo systemctl start nginx"
echo "3. 如果端口被占用: sudo netstat -tlnp | grep 5000"
echo "4. 如果防火墙阻止: sudo firewall-cmd --permanent --add-port=80/tcp && sudo firewall-cmd --reload"
echo "5. 如果SELinux阻止: sudo setsebool -P httpd_can_network_connect 1" 