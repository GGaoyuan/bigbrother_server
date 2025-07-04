# Gunicorn + Nginx 部署指南

本项目使用 **Gunicorn** 作为WSGI服务器，**Nginx** 作为反向代理，适用于OpenCloudOS生产环境。

## 🏗️ 架构说明

```
客户端请求 → Nginx (80端口) → Gunicorn (5000端口) → Flask应用
```

- **Nginx**: 处理静态文件、负载均衡、SSL终止
- **Gunicorn**: Python WSGI服务器，运行Flask应用
- **Flask**: Web应用框架

## 📁 配置文件

### 1. Gunicorn配置 (`gunicorn.conf.py`)
```python
# 服务器配置
bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"

# 日志配置
accesslog = "/var/log/bigbrother_server/access.log"
errorlog = "/var/log/bigbrother_server/error.log"
```

### 2. Nginx配置 (`nginx.conf`)
```nginx
upstream flask_app {
    server 127.0.0.1:5000;
    keepalive 32;
}

server {
    listen 80;
    location / {
        proxy_pass http://flask_app;
        # 代理头设置...
    }
}
```

## 🚀 快速部署

### 方式一：使用部署脚本（推荐）
```bash
# 给脚本执行权限
chmod +x deploy.sh start_gunicorn.sh

# 部署应用
sudo ./deploy.sh
```

### 方式二：手动部署
```bash
# 1. 安装依赖
sudo yum install -y python3 python3-pip nginx

# 2. 创建用户
sudo useradd -r -s /bin/bash -d /home/flask flask

# 3. 创建虚拟环境
sudo python3 -m venv /home/flask/venv
sudo chown -R flask:flask /home/flask/venv

# 4. 安装Python依赖
sudo -u flask /home/flask/venv/bin/pip install -r requirements.txt
sudo -u flask /home/flask/venv/bin/pip install gunicorn gevent

# 5. 部署应用
sudo mkdir -p /opt/bigbrother_server
sudo cp -r ./* /opt/bigbrother_server/
sudo chown -R flask:flask /opt/bigbrother_server

# 6. 配置Gunicorn
sudo cp gunicorn.conf.py /opt/bigbrother_server/
sudo chown flask:flask /opt/bigbrother_server/gunicorn.conf.py

# 7. 配置Nginx
sudo cp nginx.conf /etc/nginx/conf.d/bigbrother_server.conf
sudo nginx -t
sudo systemctl restart nginx

# 8. 启动Gunicorn
sudo ./start_gunicorn.sh start
```

## 🛠️ 管理命令

### Gunicorn管理
```bash
# 启动Gunicorn
sudo ./start_gunicorn.sh start

# 停止Gunicorn
sudo ./start_gunicorn.sh stop

# 重启Gunicorn
sudo ./start_gunicorn.sh restart

# 查看状态
sudo ./start_gunicorn.sh status

# 查看日志
sudo ./start_gunicorn.sh logs
```

### Nginx管理
```bash
# 启动Nginx
sudo systemctl start nginx

# 停止Nginx
sudo systemctl stop nginx

# 重启Nginx
sudo systemctl restart nginx

# 重载配置
sudo nginx -s reload

# 检查配置
sudo nginx -t

# 查看状态
sudo systemctl status nginx
```

### 系统服务管理
```bash
# 启用开机自启
sudo systemctl enable nginx
sudo systemctl enable bigbrother_server.service

# 查看服务状态
sudo systemctl status bigbrother_server.service
sudo systemctl status nginx

# 查看日志
sudo journalctl -u bigbrother_server.service -f
sudo journalctl -u nginx -f
```

## 📊 性能监控

### 1. 进程监控
```bash
# 查看Gunicorn进程
ps aux | grep gunicorn

# 查看端口占用
netstat -tlnp | grep 5000
netstat -tlnp | grep 80

# 查看系统资源
top -p $(pgrep gunicorn)
```

### 2. 日志监控
```bash
# 实时查看访问日志
tail -f /var/log/bigbrother_server/access.log

# 实时查看错误日志
tail -f /var/log/bigbrother_server/error.log

# 查看Nginx访问日志
tail -f /var/log/nginx/bigbrother_server_access.log

# 查看Nginx错误日志
tail -f /var/log/nginx/bigbrother_server_error.log
```

### 3. 健康检查
```bash
# 检查应用健康状态
curl http://localhost/health

# 检查响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost/

# 压力测试
ab -n 1000 -c 10 http://localhost/
```

## ⚙️ 配置优化

### Gunicorn优化
```python
# 根据CPU核心数调整worker数量
workers = multiprocessing.cpu_count() * 2 + 1

# 调整worker连接数
worker_connections = 1000

# 调整超时时间
timeout = 30
keepalive = 2

# 启用预加载应用
preload_app = True
```

### Nginx优化
```nginx
# 启用gzip压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 静态文件缓存
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# 连接池
upstream flask_app {
    server 127.0.0.1:5000;
    keepalive 32;
}
```

## 🔧 故障排除

### 1. Gunicorn启动失败
```bash
# 检查配置文件
python3 -m py_compile gunicorn.conf.py

# 检查应用文件
python3 -m py_compile app.py

# 手动启动测试
sudo -u flask bash -c "
    cd /opt/bigbrother_server
    source /home/flask/venv/bin/activate
    gunicorn -c gunicorn.conf.py app:app
"
```

### 2. Nginx配置错误
```bash
# 检查配置语法
nginx -t

# 查看错误日志
tail -f /var/log/nginx/error.log

# 重载配置
nginx -s reload
```

### 3. 端口冲突
```bash
# 查看端口占用
netstat -tlnp | grep :5000
netstat -tlnp | grep :80

# 杀死占用进程
sudo kill -9 <PID>
```

### 4. 权限问题
```bash
# 修复文件权限
sudo chown -R flask:flask /opt/bigbrother_server/
sudo chown -R flask:flask /home/flask/venv/
sudo chown flask:flask /var/log/bigbrother_server/
```

## 🔒 安全配置

### 1. 防火墙设置
```bash
# 只开放必要端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 2. SELinux配置
```bash
# 允许Nginx网络连接
sudo setsebool -P httpd_can_network_connect 1

# 设置文件上下文
sudo semanage fcontext -a -t httpd_exec_t "/opt/bigbrother_server(/.*)?"
sudo restorecon -Rv /opt/bigbrother_server/
```

### 3. 安全头设置
```nginx
# 在nginx.conf中已配置
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
```

## 📈 性能调优

### 1. 系统级优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 2. 应用级优化
```python
# 在gunicorn.conf.py中调整
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
```

## 🔄 更新部署

### 1. 代码更新
```bash
# 备份当前版本
sudo cp -r /opt/bigbrother_server /opt/bigbrother_server_backup

# 更新代码
sudo cp -r ./* /opt/bigbrother_server/
sudo chown -R flask:flask /opt/bigbrother_server/

# 重启服务
sudo ./start_gunicorn.sh restart
```

### 2. 配置更新
```bash
# 更新Gunicorn配置
sudo cp gunicorn.conf.py /opt/bigbrother_server/
sudo chown flask:flask /opt/bigbrother_server/gunicorn.conf.py

# 更新Nginx配置
sudo cp nginx.conf /etc/nginx/conf.d/bigbrother_server.conf
sudo nginx -t && sudo nginx -s reload

# 重启Gunicorn
sudo ./start_gunicorn.sh restart
```

## 📝 日志轮转

### 1. 配置logrotate
```bash
# 创建logrotate配置
sudo tee /etc/logrotate.d/bigbrother_server << EOF
/var/log/bigbrother_server/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 flask flask
    postrotate
        systemctl reload bigbrother_server.service
    endscript
}
EOF
```

### 2. 手动轮转
```bash
# 手动执行轮转
sudo logrotate -f /etc/logrotate.d/bigbrother_server
```

## 🎯 最佳实践

1. **监控**: 定期检查日志和系统资源
2. **备份**: 定期备份配置文件和代码
3. **更新**: 及时更新系统和依赖包
4. **测试**: 在生产环境部署前进行充分测试
5. **文档**: 记录配置变更和部署步骤

## 📞 支持

如果遇到问题，请检查：
1. 系统日志 (`journalctl`)
2. 应用日志 (`/var/log/bigbrother_server/`)
3. Nginx日志 (`/var/log/nginx/`)
4. 网络连接 (`netstat`, `curl`)
5. 权限设置 (`ls -la`, `chown`)

更多信息请参考：
- [Gunicorn官方文档](https://docs.gunicorn.org/)
- [Nginx官方文档](https://nginx.org/en/docs/)
- [OpenCloudOS官方文档](https://www.opencloudos.org/) 