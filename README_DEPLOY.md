# OpenCloudOS Flask应用部署指南

本项目提供了两种部署方式，适用于OpenCloudOS系统。

## 部署方式

### 方式一：使用Python脚本部署（推荐）

```bash
# 给脚本执行权限
chmod +x app_deploy.py

# 使用root权限运行部署脚本
sudo python3 app_deploy.py
```

### 方式二：使用Bash脚本部署（快速）

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 使用root权限运行部署脚本
sudo ./deploy.sh
```

## 部署前准备

1. **系统要求**
   - OpenCloudOS 系统
   - Python 3.6+
   - Root权限

2. **网络要求**
   - 确保服务器能够访问外网下载依赖包
   - 确保80端口未被占用

## 部署内容

部署脚本会自动完成以下操作：

### 系统环境配置
- 更新系统包
- 安装Python3及相关开发工具
- 安装Nginx和Supervisor
- 创建专用Flask用户

### Python环境配置
- 创建Python虚拟环境
- 安装项目依赖
- 安装生产环境依赖（Gunicorn、Gevent、psutil）

### 应用部署
- 复制应用文件到 `/opt/bigbrother_server/`
- 配置Gunicorn服务器
- 创建systemd服务
- 配置Nginx反向代理

### 服务管理
- 启动并启用systemd服务
- 配置自动重启
- 创建健康检查脚本

## 部署后验证

### 1. 检查服务状态
```bash
# 检查Flask应用服务
systemctl status bigbrother_server.service

# 检查Nginx服务
systemctl status nginx
```

### 2. 测试应用访问
```bash
# 测试主页
curl http://localhost

# 测试健康检查
curl http://localhost/health
```

### 3. 查看日志
```bash
# 查看应用日志
journalctl -u bigbrother_server.service -f

# 查看Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 查看应用专用日志
tail -f /var/log/bigbrother_server/access.log
tail -f /var/log/bigbrother_server/error.log
```

## 常用管理命令

### 服务管理
```bash
# 启动服务
systemctl start bigbrother_server.service

# 停止服务
systemctl stop bigbrother_server.service

# 重启服务
systemctl restart bigbrother_server.service

# 查看服务状态
systemctl status bigbrother_server.service

# 启用开机自启
systemctl enable bigbrother_server.service
```

### 应用管理
```bash
# 查看应用进程
ps aux | grep gunicorn

# 查看端口占用
netstat -tlnp | grep 5000

# 测试应用响应
curl -I http://localhost/health
```

### 日志管理
```bash
# 实时查看应用日志
journalctl -u bigbrother_server.service -f

# 查看最近的日志
journalctl -u bigbrother_server.service --since "1 hour ago"

# 查看错误日志
journalctl -u bigbrother_server.service -p err
```

## 配置文件位置

- **应用目录**: `/opt/bigbrother_server/`
- **虚拟环境**: `/home/flask/venv/`
- **systemd服务**: `/etc/systemd/system/bigbrother_server.service`
- **Nginx配置**: `/etc/nginx/conf.d/bigbrother_server.conf`
- **日志目录**: `/var/log/bigbrother_server/`
- **Gunicorn配置**: `/opt/bigbrother_server/gunicorn.conf.py`

## 故障排除

### 1. 服务启动失败
```bash
# 查看详细错误信息
journalctl -u bigbrother_server.service -n 50

# 检查配置文件语法
python3 -m py_compile /opt/bigbrother_server/app.py
```

### 2. 端口被占用
```bash
# 查看端口占用情况
netstat -tlnp | grep 5000

# 杀死占用进程
sudo kill -9 <PID>
```

### 3. 权限问题
```bash
# 修复文件权限
sudo chown -R flask:flask /opt/bigbrother_server/
sudo chown -R flask:flask /home/flask/venv/
```

### 4. 依赖安装失败
```bash
# 手动安装依赖
sudo -u flask /home/flask/venv/bin/pip install -r requirements.txt
```

## 安全建议

1. **防火墙配置**
   ```bash
   # 只开放必要端口
   firewall-cmd --permanent --add-port=80/tcp
   firewall-cmd --reload
   ```

2. **SELinux配置**
   ```bash
   # 如果启用了SELinux，可能需要配置
   setsebool -P httpd_can_network_connect 1
   ```

3. **定期更新**
   ```bash
   # 定期更新系统和依赖
   yum update -y
   sudo -u flask /home/flask/venv/bin/pip install --upgrade -r requirements.txt
   ```

## 性能优化

1. **调整Gunicorn配置**
   - 根据CPU核心数调整worker数量
   - 调整worker_connections参数

2. **Nginx优化**
   - 启用gzip压缩
   - 配置静态文件缓存

3. **系统优化**
   - 调整文件描述符限制
   - 优化内存使用

## 备份和恢复

### 备份
```bash
# 备份应用文件
tar -czf backup_$(date +%Y%m%d).tar.gz /opt/bigbrother_server/

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz /etc/systemd/system/bigbrother_server.service /etc/nginx/conf.d/bigbrother_server.conf
```

### 恢复
```bash
# 恢复应用文件
tar -xzf backup_YYYYMMDD.tar.gz -C /

# 恢复配置文件
tar -xzf config_backup_YYYYMMDD.tar.gz -C /

# 重新加载服务
systemctl daemon-reload
systemctl restart bigbrother_server.service
systemctl restart nginx
```

## 联系支持

如果在部署过程中遇到问题，请检查：
1. 系统日志
2. 应用日志
3. 网络连接
4. 权限设置

更多信息请参考OpenCloudOS官方文档。 