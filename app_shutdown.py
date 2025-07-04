#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用关闭脚本
用于停止和清理已部署的Flask应用
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class FlaskShutdown:
    def __init__(self):
        self.app_name = "bigbrother_server"
        self.service_name = f"{self.app_name}.service"
        self.user = "flask"
        self.app_dir = f"/opt/{self.app_name}"
        self.venv_dir = f"/home/{self.user}/venv"
        
    def run_command(self, command, check=False, shell=True):
        """执行系统命令"""
        print(f"执行命令: {command}")
        try:
            result = subprocess.run(command, shell=shell, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                print(f"输出: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {e}")
            if result.stderr:
                print(f"错误输出: {result.stderr}")
            return e
    
    def check_root_permission(self):
        """检查root权限"""
        if os.geteuid() != 0:
            print("错误: 请使用root权限运行此脚本")
            sys.exit(1)
    
    def stop_services(self):
        """停止服务"""
        print("=== 停止服务 ===")
        
        # 停止Flask应用服务
        print("停止Flask应用服务...")
        self.run_command(f"systemctl stop {self.service_name}")
        self.run_command(f"systemctl disable {self.service_name}")
        
        # 停止Nginx（可选）
        print("停止Nginx服务...")
        self.run_command("systemctl stop nginx")
        self.run_command("systemctl disable nginx")
        
        # 停止Supervisor（可选）
        print("停止Supervisor服务...")
        try:
            result = subprocess.run(['systemctl', 'list-unit-files', 'supervisord.service'], 
                                  capture_output=True, text=True)
            if 'supervisord.service' in result.stdout:
                self.run_command("systemctl stop supervisord")
                self.run_command("systemctl disable supervisord")
            else:
                print("supervisor服务不存在，跳过")
        except Exception as e:
            print(f"检查supervisor服务时出错: {e}")
    
    def remove_systemd_service(self):
        """删除systemd服务"""
        print("=== 删除systemd服务 ===")
        
        service_path = f"/etc/systemd/system/{self.service_name}"
        if os.path.exists(service_path):
            print(f"删除服务文件: {service_path}")
            os.remove(service_path)
            self.run_command("systemctl daemon-reload")
        else:
            print(f"服务文件不存在: {service_path}")
    
    def remove_nginx_config(self):
        """删除Nginx配置"""
        print("=== 删除Nginx配置 ===")
        
        nginx_config_path = f"/etc/nginx/conf.d/{self.app_name}.conf"
        if os.path.exists(nginx_config_path):
            print(f"删除Nginx配置: {nginx_config_path}")
            os.remove(nginx_config_path)
        else:
            print(f"Nginx配置文件不存在: {nginx_config_path}")
    
    def remove_application_files(self):
        """删除应用文件"""
        print("=== 删除应用文件 ===")
        
        if os.path.exists(self.app_dir):
            print(f"删除应用目录: {self.app_dir}")
            shutil.rmtree(self.app_dir)
        else:
            print(f"应用目录不存在: {self.app_dir}")
    
    def remove_logs(self):
        """删除日志文件"""
        print("=== 删除日志文件 ===")
        
        log_dir = f"/var/log/{self.app_name}"
        if os.path.exists(log_dir):
            print(f"删除日志目录: {log_dir}")
            shutil.rmtree(log_dir)
        else:
            print(f"日志目录不存在: {log_dir}")
        
        # 删除Nginx相关日志
        nginx_logs = [
            f"/var/log/nginx/{self.app_name}_access.log",
            f"/var/log/nginx/{self.app_name}_error.log"
        ]
        
        for log_file in nginx_logs:
            if os.path.exists(log_file):
                print(f"删除Nginx日志: {log_file}")
                os.remove(log_file)
    
    def remove_virtual_environment(self):
        """删除虚拟环境"""
        print("=== 删除虚拟环境 ===")
        
        if os.path.exists(self.venv_dir):
            print(f"删除虚拟环境: {self.venv_dir}")
            shutil.rmtree(self.venv_dir)
        else:
            print(f"虚拟环境不存在: {self.venv_dir}")
    
    def remove_user(self):
        """删除Flask用户"""
        print("=== 删除Flask用户 ===")
        
        # 检查用户是否存在
        result = subprocess.run(['id', self.user], capture_output=True)
        if result.returncode == 0:
            print(f"删除用户: {self.user}")
            self.run_command(f"userdel -r {self.user}")
        else:
            print(f"用户不存在: {self.user}")
    
    def remove_supervisor_config(self):
        """删除Supervisor配置"""
        print("=== 删除Supervisor配置 ===")
        
        supervisor_config = f"/etc/supervisord.d/{self.app_name}.ini"
        if os.path.exists(supervisor_config):
            print(f"删除Supervisor配置: {supervisor_config}")
            os.remove(supervisor_config)
        else:
            print(f"Supervisor配置文件不存在: {supervisor_config}")
        
        # 检查supervisor目录是否存在
        supervisor_dir = "/etc/supervisord.d"
        if os.path.exists(supervisor_dir):
            print(f"Supervisor配置目录存在: {supervisor_dir}")
        else:
            print("Supervisor配置目录不存在，跳过supervisor清理")
    
    def cleanup_pid_files(self):
        """清理PID文件"""
        print("=== 清理PID文件 ===")
        
        pid_file = f"/var/run/{self.app_name}.pid"
        if os.path.exists(pid_file):
            print(f"删除PID文件: {pid_file}")
            os.remove(pid_file)
        else:
            print(f"PID文件不存在: {pid_file}")
    
    def kill_remaining_processes(self):
        """杀死残留进程"""
        print("=== 杀死残留进程 ===")
        
        # 查找并杀死gunicorn进程
        try:
            result = subprocess.run(['pgrep', '-f', 'gunicorn'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"杀死进程: {pid}")
                        self.run_command(f"kill -9 {pid}")
        except Exception as e:
            print(f"查找进程时出错: {e}")
    
    def show_cleanup_summary(self):
        """显示清理总结"""
        print("\n=== 清理完成 ===")
        print("已删除的内容:")
        print(f"  - 应用目录: {self.app_dir}")
        print(f"  - 虚拟环境: {self.venv_dir}")
        print(f"  - 系统服务: {self.service_name}")
        print(f"  - Nginx配置: /etc/nginx/conf.d/{self.app_name}.conf")
        print(f"  - 日志目录: /var/log/{self.app_name}")
        print(f"  - Flask用户: {self.user}")
        print("\n注意:")
        print("  - Nginx和Supervisor服务已停止，如需使用请手动启动")
        print("  - 系统依赖包未删除，如需清理请手动执行: yum remove nginx supervisor")
    
    def shutdown(self, remove_user=False):
        """执行完整关闭流程"""
        print("开始关闭Flask应用...")
        
        try:
            self.check_root_permission()
            
            # 确认操作
            print(f"\n警告: 此操作将完全删除Flask应用 '{self.app_name}'")
            if remove_user:
                print("包括删除用户和虚拟环境")
            else:
                print("保留用户和虚拟环境")
            
            confirm = input("确定要继续吗? (y/N): ")
            if confirm.lower() != 'y':
                print("操作已取消")
                return
            
            # 执行关闭流程
            self.stop_services()
            self.kill_remaining_processes()
            self.cleanup_pid_files()
            self.remove_systemd_service()
            self.remove_nginx_config()
            self.remove_supervisor_config()
            self.remove_application_files()
            self.remove_logs()
            
            if remove_user:
                self.remove_virtual_environment()
                self.remove_user()
            
            self.show_cleanup_summary()
            
        except Exception as e:
            print(f"关闭过程中出现错误: {e}")
            sys.exit(1)
    
    def status_check(self):
        """检查应用状态"""
        print("=== 应用状态检查 ===")
        
        # 检查服务状态
        print("检查服务状态...")
        self.run_command(f"systemctl status {self.service_name}")
        
        # 检查进程
        print("\n检查进程...")
        self.run_command("ps aux | grep gunicorn")
        
        # 检查端口
        print("\n检查端口...")
        self.run_command("netstat -tlnp | grep 5000")
        
        # 检查文件
        print("\n检查文件...")
        files_to_check = [
            self.app_dir,
            self.venv_dir,
            f"/etc/systemd/system/{self.service_name}",
            f"/etc/nginx/conf.d/{self.app_name}.conf"
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print(f"✓ {file_path}")
            else:
                print(f"✗ {file_path}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("""
Flask应用关闭脚本

用法:
    python3 app_shutdown.py              # 关闭应用（保留用户）
    python3 app_shutdown.py --all        # 完全清理（包括用户）
    python3 app_shutdown.py --status     # 检查应用状态
    python3 app_shutdown.py --help       # 显示帮助信息

选项:
    --all     完全清理，包括删除Flask用户和虚拟环境
    --status  检查应用当前状态
    --help    显示帮助信息

注意: 建议使用root权限运行此脚本
            """)
            return
        elif sys.argv[1] == "--status":
            shutdown = FlaskShutdown()
            shutdown.status_check()
            return
        elif sys.argv[1] == "--all":
            shutdown = FlaskShutdown()
            shutdown.shutdown(remove_user=True)
            return
    
    # 默认关闭（保留用户）
    shutdown = FlaskShutdown()
    shutdown.shutdown(remove_user=False)

if __name__ == "__main__":
    main()
