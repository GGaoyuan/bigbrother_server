# Flask应用部署管理文档

本项目提供了两个核心脚本来管理Flask应用在OpenCloudOS系统中的部署和关闭。

## 📁 文件说明

- **`app_deploy.py`** - Flask应用部署脚本
- **`app_shutdown.py`** - Flask应用关闭脚本

## 🏗️ 架构说明

```
客户端请求 → Nginx (80端口) → Gunicorn (5000端口) → Flask应用
```

- **Nginx**: 反向代理，处理静态文件
- **Gunicorn**: WSGI服务器，运行Flask应用
- **Flask**: Web应用框架

## 🚀 部署应用

### 前置要求

1. **系统要求**
   - OpenCloudOS 系统
   - Python 3.6+
   - Root权限

2. **网络要求**
   - 确保服务器能够访问外网下载依赖包
   - 确保80端口未被占用

### 部署步骤

1. **给脚本执行权限**
   ```bash
   chmod +x app_deploy.py app_shutdown.py
   ```

2. **执行部署**
   ```bash
   sudo python3 app_deploy.py
   ```

### 部署过程

部署脚本会自动执行以下操作：

1. **系统环境检查**
   - 检查Python版本
   - 验证root权限

2. **安装系统依赖**
   - 更新系统包
   - 安装Python3及相关开发工具
   - 安装Nginx和Supervisor

3. **创建应用环境**
   - 创建专用Flask用户
   - 创建Python虚拟环境
   - 安装项目依赖

4. **部署应用**
   - 复制应用文件到 `/opt/bigbrother_server/`
   - 配置Gunicorn服务器
   - 创建systemd服务

5. **配置Web服务器**
   - 配置Nginx反向代理
   - 设置安全头
   - 配置静态文件处理

6. **启动服务**
   - 启动Flask应用服务
   - 启动Nginx服务
   - 创建健康检查脚本

### 部署完成

部署成功后，你会看到类似以下的输出：

```
=== 部署完成 ===
应用名称: bigbrother_server
访问地址: http://localhost
应用端口: 5000
服务名称: bigbrother_server.service

常用命令:
  查看服务状态: systemctl status bigbrother_server.service
  重启服务: systemctl restart bigbrother_server.service
  查看日志: journalctl -u bigbrother_server.service -f
  查看nginx状态: systemctl status nginx
  健康检查: curl http://localhost/health
```

## 🛠️ 管理应用

### 查看应用状态

```bash
# 检查服务状态
systemctl status bigbrother_server.service

# 检查Nginx状态
systemctl status nginx

# 查看应用进程
ps aux | grep gunicorn

# 检查端口占用
netstat -tlnp | grep 5000
```

### 重启应用

```bash
# 重启Flask应用
systemctl restart bigbrother_server.service

# 重启Nginx
systemctl restart nginx

# 重载Nginx配置
nginx -s reload
```

### 查看日志

```bash
# 查看应用日志
journalctl -u bigbrother_server.service -f

# 查看Nginx访问日志
tail -f /var/log/nginx/bigbrother_server_access.log

# 查看Nginx错误日志
tail -f /var/log/nginx/bigbrother_server_error.log

# 查看应用专用日志
tail -f /var/log/bigbrother_server/access.log
tail -f /var/log/bigbrother_server/error.log
```

### 健康检查

```bash
# 检查应用健康状态
curl http://localhost/health

# 检查主页
curl http://localhost

# 检查测试页面
curl http://localhost/testaaa
```

## 🛑 关闭应用

### 基本关闭（保留用户）

```bash
sudo python3 app_shutdown.py
```

这会：
- 停止所有相关服务
- 删除应用文件和配置
- 保留Flask用户和虚拟环境

### 完全清理

```bash
sudo python3 app_shutdown.py --all
```

这会：
- 执行基本关闭的所有操作
- 删除Flask用户
- 删除虚拟环境
- 完全清理所有相关文件

### 检查应用状态

```bash
python3 app_shutdown.py --status
```

这会显示：
- 服务运行状态
- 进程信息
- 端口占用情况
- 文件存在状态

### 查看帮助

```bash
python3 app_shutdown.py --help
```

## 📊 配置文件位置

部署后，以下文件会被创建：

| 类型 | 路径 | 说明 |
|------|------|------|
| 应用目录 | `/opt/bigbrother_server/` | 应用文件存放位置 |
| 虚拟环境 | `/home/flask/venv/` | Python虚拟环境 |
| 系统服务 | `/etc/systemd/system/bigbrother_server.service` | systemd服务配置 |
| Nginx配置 | `/etc/nginx/conf.d/bigbrother_server.conf` | Nginx反向代理配置 |
| 日志目录 | `/var/log/bigbrother_server/` | 应用日志 |
| Gunicorn配置 | `/opt/bigbrother_server/gunicorn.conf.py` | Gunicorn服务器配置 |

## 🔧 故障排除

### 1. 部署失败

**问题**: `yum update -y` 卡住
**解决**: 
- 检查网络连接
- 检查yum源配置
- 脚本已改为实时输出，可以看到详细进度

**问题**: 权限错误
**解决**:
```bash
# 修复文件权限
sudo chown -R flask:flask /opt/bigbrother_server/
sudo chown -R flask:flask /home/flask/venv/
```

### 2. 应用无法启动

**问题**: 端口被占用
**解决**:
```bash
# 查看端口占用
netstat -tlnp | grep 5000

# 杀死占用进程
sudo kill -9 <PID>
```

**问题**: 依赖安装失败
**解决**:
```bash
# 手动安装依赖
sudo -u flask /home/flask/venv/bin/pip install -r requirements.txt
```

### 3. Nginx配置错误

**问题**: Nginx启动失败
**解决**:
```bash
# 检查配置语法
nginx -t

# 查看错误日志
tail -f /var/log/nginx/error.log
```

### 4. 服务无法访问

**问题**: 防火墙阻止
**解决**:
```bash
# 开放端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --reload
```

## 🔒 安全建议

### 1. 防火墙配置
```bash
# 只开放必要端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### 2. SELinux配置
```bash
# 允许Nginx网络连接
setsebool -P httpd_can_network_connect 1
```

### 3. 定期更新
```bash
# 更新系统
yum update -y

# 更新Python依赖
sudo -u flask /home/flask/venv/bin/pip install --upgrade -r requirements.txt
```

## 📈 性能优化

### 1. Gunicorn优化
```python
# 在gunicorn.conf.py中调整
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000
max_requests = 1000
```

### 2. Nginx优化
```nginx
# 启用gzip压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 静态文件缓存
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 3. 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
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
sudo systemctl restart bigbrother_server.service
```

### 2. 配置更新
```bash
# 更新Gunicorn配置
sudo cp gunicorn.conf.py /opt/bigbrother_server/
sudo chown flask:flask /opt/bigbrother_server/gunicorn.conf.py

# 更新Nginx配置
sudo cp nginx.conf /etc/nginx/conf.d/bigbrother_server.conf
sudo nginx -t && sudo nginx -s reload

# 重启应用
sudo systemctl restart bigbrother_server.service
```

## 📝 日志管理

### 1. 配置日志轮转
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