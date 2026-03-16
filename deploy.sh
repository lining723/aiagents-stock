#!/bin/bash

# ============================================
# AI Agents Stock 部署脚本
# 功能：Docker 构建及启动
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# 函数：打印信息
# ============================================
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# 函数：检查 Docker 是否安装
# ============================================
check_docker() {
    print_info "检查 Docker 安装状态..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装！请先安装 Docker。"
        print_info "Docker 安装指南：https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装！请先安装 Docker Compose。"
        print_info "Docker Compose 安装指南：https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker 环境检查通过"
}

# ============================================
# 函数：检查 .env 文件
# ============================================
check_env_file() {
    print_info "检查环境配置文件..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，正在从 .env.example 创建..."
        
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env 文件已创建"
            print_warning "请编辑 .env 文件，配置您的 API Key 等信息！"
            echo ""
            read -p "是否继续部署？(y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "部署已取消"
                exit 0
            fi
        else
            print_error ".env.example 文件也不存在！请确保项目文件完整。"
            exit 1
        fi
    else
        print_success ".env 文件存在"
    fi
}

# ============================================
# 函数：创建必要的目录
# ============================================
create_directories() {
    print_info "创建必要的目录..."
    
    mkdir -p log
    mkdir -p data
    
    print_success "目录创建完成"
}

# ============================================
# 函数：停止旧容器
# ============================================
stop_old_containers() {
    print_info "停止旧容器..."
    
    if docker-compose ps &> /dev/null; then
        docker-compose down || true
    elif docker compose ps &> /dev/null; then
        docker compose down || true
    fi
    
    print_success "旧容器已停止"
}

# ============================================
# 函数：构建并启动
# ============================================
build_and_start() {
    print_info "开始构建并启动服务..."
    
    if docker-compose --version &> /dev/null; then
        docker-compose up -d --build
    else
        docker compose up -d --build
    fi
    
    print_success "构建完成"
}

# ============================================
# 函数：等待服务启动
# ============================================
wait_for_service() {
    print_info "等待服务启动..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker ps --format '{{.Names}}' | grep -q "agentsstock1"; then
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' agentsstock1 2>/dev/null || echo "unknown")
            
            if [ "$health_status" = "healthy" ]; then
                print_success "服务已启动并健康运行"
                return 0
            elif [ "$health_status" = "starting" ]; then
                print_info "服务正在启动中..."
            else
                print_info "检查服务状态..."
            fi
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_warning "服务启动检查超时，请手动检查容器状态"
}

# ============================================
# 函数：显示服务信息
# ============================================
show_service_info() {
    echo ""
    echo "============================================"
    echo -e "${GREEN}🎉 部署成功！${NC}"
    echo "============================================"
    echo ""
    echo -e "📱 访问地址：${BLUE}http://localhost:8503${NC}"
    echo ""
    echo "📋 常用命令："
    echo "  查看日志：    docker logs -f agentsstock1"
    echo "  停止服务：    docker-compose down"
    echo "  重启服务：    docker-compose restart"
    echo "  查看状态：    docker ps"
    echo ""
    echo "📝 日志文件位置："
    echo "  宿主机：      ./log/app.log"
    echo "  容器内：      /app/log/app.log"
    echo ""
    echo "============================================"
}

# ============================================
# 主函数
# ============================================
main() {
    echo ""
    echo "============================================"
    echo "  AI Agents Stock 部署脚本"
    echo "============================================"
    echo ""
    
    # 执行检查
    check_docker
    check_env_file
    create_directories
    
    # 停止旧容器
    stop_old_containers
    
    # 构建并启动
    build_and_start
    
    # 等待服务启动
    wait_for_service
    
    # 显示信息
    show_service_info
}

# 执行主函数
main "$@"
