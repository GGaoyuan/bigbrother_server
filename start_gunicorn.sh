#!/bin/bash
# Gunicorn启动脚本

set -e

# 配置变量
APP_NAME="bigbrother_server"
APP_DIR="/opt/$APP_NAME"
VENV_DIR="/home/flask/venv"
CONFIG_FILE="$APP_DIR/gunicorn.conf.py"
PID_FILE="/var/run/$APP_NAME.pid"
LOG_DIR="/var/log/$APP_NAME"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
}

# 检查应用目录
check_app_dir() {
    if [ ! -d "$APP_DIR" ]; then
        log_error "应用目录不存在: $APP_DIR"
        log_info "请先运行部署脚本"
        exit 1
    fi
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "虚拟环境不存在: $VENV_DIR"
        log_info "请先运行部署脚本"
        exit 1
    fi
}

# 创建日志目录
create_log_dir() {
    if [ ! -d "$LOG_DIR" ]; then
        log_info "创建日志目录: $LOG_DIR"
        mkdir -p "$LOG_DIR"
        chown flask:flask "$LOG_DIR"
    fi
}

# 检查进程是否运行
check_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "应用已在运行 (PID: $PID)"
            return 0
        else
            log_warn "PID文件存在但进程不存在，删除PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# 启动Gunicorn
start_gunicorn() {
    log_info "启动Gunicorn服务器..."
    
    cd "$APP_DIR"
    
    # 使用flask用户启动
    sudo -u flask bash -c "
        cd $APP_DIR
        source $VENV_DIR/bin/activate
        gunicorn -c $CONFIG_FILE app:app
    " &
    
    # 等待进程启动
    sleep 3
    
    # 检查是否启动成功
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "Gunicorn启动成功 (PID: $PID)"
            log_info "应用地址: http://localhost"
            log_info "健康检查: http://localhost/health"
        else
            log_error "Gunicorn启动失败"
            exit 1
        fi
    else
        log_error "PID文件未创建，启动可能失败"
        exit 1
    fi
}

# 停止Gunicorn
stop_gunicorn() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "停止Gunicorn进程 (PID: $PID)"
            kill -TERM "$PID"
            
            # 等待进程结束
            for i in {1..10}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    log_info "Gunicorn已停止"
                    rm -f "$PID_FILE"
                    return 0
                fi
                sleep 1
            done
            
            # 强制杀死进程
            log_warn "强制停止Gunicorn进程"
            kill -KILL "$PID"
            rm -f "$PID_FILE"
        else
            log_warn "进程不存在，删除PID文件"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "PID文件不存在，应用可能未运行"
    fi
}

# 重启Gunicorn
restart_gunicorn() {
    log_info "重启Gunicorn服务器..."
    stop_gunicorn
    sleep 2
    start_gunicorn
}

# 查看状态
show_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "Gunicorn正在运行 (PID: $PID)"
            echo "进程信息:"
            ps -p "$PID" -o pid,ppid,cmd,etime
            echo ""
            echo "端口监听:"
            netstat -tlnp | grep 5000 || echo "端口5000未监听"
        else
            log_warn "PID文件存在但进程不存在"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "Gunicorn未运行"
    fi
}

# 查看日志
show_logs() {
    if [ -d "$LOG_DIR" ]; then
        log_info "显示最近的日志..."
        echo "=== 访问日志 ==="
        tail -20 "$LOG_DIR/access.log" 2>/dev/null || echo "访问日志不存在"
        echo ""
        echo "=== 错误日志 ==="
        tail -20 "$LOG_DIR/error.log" 2>/dev/null || echo "错误日志不存在"
    else
        log_error "日志目录不存在: $LOG_DIR"
    fi
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            check_root
            check_app_dir
            check_venv
            create_log_dir
            if check_process; then
                exit 0
            fi
            start_gunicorn
            ;;
        stop)
            check_root
            stop_gunicorn
            ;;
        restart)
            check_root
            restart_gunicorn
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动Gunicorn服务器"
            echo "  stop    - 停止Gunicorn服务器"
            echo "  restart - 重启Gunicorn服务器"
            echo "  status  - 查看服务器状态"
            echo "  logs    - 查看日志"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 