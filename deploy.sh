#!/usr/bin/env bash

# AI Agents Stock deployment helper.
# Supports Linux and macOS with Docker Compose v2 or docker-compose.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_CMD=()

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

usage() {
    cat <<'EOF'
AI Agents Stock 部署脚本

用法:
  ./deploy.sh [command] [service]

命令:
  up | deploy      构建并启动全部服务，默认命令
  start            启动已创建的服务
  stop             停止服务，不删除容器
  restart          重启服务
  down             停止并删除容器，不删除数据卷
  build            仅构建镜像
  status | ps      查看 Compose 服务状态
  logs [service]   查看日志，可指定 backend/frontend/redis/mongo/tdx-api
  health           检查容器健康状态与 HTTP 入口
  config           静默校验 Docker Compose 配置
  help             显示帮助

常用示例:
  ./deploy.sh
  ./deploy.sh logs backend
  ./deploy.sh health
  ./deploy.sh restart
EOF
}

detect_os() {
    case "$(uname -s)" in
        Linux*) echo "Linux" ;;
        Darwin*) echo "macOS" ;;
        *) echo "Unknown" ;;
    esac
}

compose() {
    "${COMPOSE_CMD[@]}" "$@"
}

check_docker() {
    local require_daemon="${1:-1}"
    local current_os
    current_os="$(detect_os)"
    print_info "检查 Docker 环境，当前系统: ${current_os}"

    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker 未安装，请先安装 Docker。"
        print_info "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
    else
        print_error "Docker Compose 未安装。"
        print_info "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi

    if [ "$require_daemon" != "1" ]; then
        print_success "Docker CLI 可用: ${COMPOSE_CMD[*]}"
        return 0
    fi

    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker 服务未运行，尝试启动 Docker..."
        if [ "$current_os" = "Linux" ]; then
            if command -v systemctl >/dev/null 2>&1; then
                sudo systemctl start docker || true
            elif command -v service >/dev/null 2>&1; then
                sudo service docker start || true
            fi
        fi
    fi

    if ! docker info >/dev/null 2>&1; then
        print_error "Docker 服务不可用，请手动启动 Docker 后重试。"
        exit 1
    fi

    print_success "Docker 环境可用: ${COMPOSE_CMD[*]}"
}

ensure_env_file() {
    print_info "检查 .env 配置文件..."

    if [ ! -f .env ]; then
        if [ ! -f .env.example ]; then
            print_error ".env 与 .env.example 均不存在，无法继续部署。"
            exit 1
        fi

        cp .env.example .env
        print_warning "已从 .env.example 创建 .env。请尽快填写 DEEPSEEK_API_KEY 等配置。"

        if [ -t 0 ] && [ "${DEPLOY_ASSUME_YES:-0}" != "1" ]; then
            local reply
            read -r -p "是否继续启动服务？[y/N] " reply
            if [[ ! "$reply" =~ ^[Yy]$ ]]; then
                print_info "已取消部署。"
                exit 0
            fi
        fi
    fi

    local api_key
    api_key="$(grep -E '^DEEPSEEK_API_KEY=' .env 2>/dev/null | tail -n 1 | cut -d= -f2- || true)"
    api_key="${api_key%\"}"
    api_key="${api_key#\"}"
    api_key="${api_key%\'}"
    api_key="${api_key#\'}"

    if [ -z "$api_key" ] || [ "$api_key" = "your_actual_deepseek_api_key_here" ]; then
        print_warning "DEEPSEEK_API_KEY 仍是占位值，AI 分析接口会启动但无法正常生成报告。"
    fi

    print_success ".env 配置文件检查完成"
}

create_directories() {
    print_info "创建运行目录..."
    mkdir -p log data db config
    print_success "运行目录已准备"
}

set_permissions() {
    if [ "$(detect_os)" = "Linux" ]; then
        chmod 755 log data db config 2>/dev/null || true
    fi
}

env_value() {
    local key="$1"
    local default="$2"
    local value="${!key:-}"

    if [ -z "$value" ] && [ -f .env ]; then
        value="$(grep -E "^${key}=" .env 2>/dev/null | tail -n 1 | cut -d= -f2- || true)"
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
    fi

    if [ -z "$value" ]; then
        value="$default"
    fi

    printf '%s' "$value"
}

wait_for_container() {
    local container="$1"
    local max_attempts="${2:-90}"
    local required="${3:-1}"
    local attempt=1

    print_info "等待 ${container} 健康..."

    while [ "$attempt" -le "$max_attempts" ]; do
        local status
        local health

        status="$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || true)"
        health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container" 2>/dev/null || true)"

        if [ "$health" = "healthy" ]; then
            print_success "${container} healthy"
            return 0
        fi

        if [ -z "$health" ] && [ "$status" = "running" ]; then
            print_success "${container} running"
            return 0
        fi

        if [ "$status" = "exited" ] || [ "$status" = "dead" ]; then
            if [ "$required" = "1" ]; then
                print_error "${container} 状态异常: ${status}"
            else
                print_warning "${container} 状态异常: ${status}"
            fi
            docker logs --tail 80 "$container" || true
            [ "$required" = "1" ] && return 1 || return 0
        fi

        sleep 2
        attempt=$((attempt + 1))
    done

    if [ "$required" = "1" ]; then
        print_warning "${container} 健康检查超时，请查看日志定位问题。"
        return 1
    fi

    print_warning "${container} 暂未健康，继续启动主服务；行情源将由后端降级链路兜底。"
    return 0
}

wait_for_services() {
    local required_containers=(
        ai-agents-stock-redis
        ai-agents-stock-mongo
        ai-agents-stock-backend
        ai-agents-stock-frontend
    )

    wait_for_container ai-agents-stock-tdx-api 30 0

    for container in "${required_containers[@]}"; do
        wait_for_container "$container" 90 1
    done
}

curl_check() {
    local name="$1"
    local url="$2"

    if ! command -v curl >/dev/null 2>&1; then
        print_warning "未安装 curl，跳过 ${name} HTTP 检查: ${url}"
        return 0
    fi

    if curl -fsS --max-time 10 "$url" >/dev/null; then
        print_success "${name} 可访问: ${url}"
    else
        print_warning "${name} 暂不可访问: ${url}"
        return 1
    fi
}

health_check() {
    local backend_port
    local frontend_port
    local tdx_port

    backend_port="$(env_value BACKEND_PORT 8000)"
    frontend_port="$(env_value FRONTEND_PORT 3000)"
    tdx_port="$(env_value TDX_PORT 8080)"

    print_info "Compose 服务状态:"
    compose ps

    echo ""
    print_info "容器健康状态:"
    for container in \
        ai-agents-stock-redis \
        ai-agents-stock-mongo \
        ai-agents-stock-tdx-api \
        ai-agents-stock-backend \
        ai-agents-stock-frontend; do
        local status
        local health
        status="$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || echo "not-found")"
        health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container" 2>/dev/null || echo "not-found")"
        echo "  ${container}: ${status} / ${health}"
    done

    echo ""
    print_info "HTTP 入口检查:"
    curl_check "后端 API" "http://127.0.0.1:${backend_port}/health" || true
    curl_check "前端页面" "http://127.0.0.1:${frontend_port}/" || true
    curl_check "tdx-api" "http://127.0.0.1:${tdx_port}/api/health" || true
}

show_service_info() {
    local backend_port
    local frontend_port
    local tdx_port

    backend_port="$(env_value BACKEND_PORT 8000)"
    frontend_port="$(env_value FRONTEND_PORT 3000)"
    tdx_port="$(env_value TDX_PORT 8080)"

    echo ""
    echo "============================================"
    echo -e "${GREEN}AI Agents Stock 部署完成${NC}"
    echo "============================================"
    echo "前端页面:      http://127.0.0.1:${frontend_port}"
    echo "后端 API:      http://127.0.0.1:${backend_port}"
    echo "API 文档:      http://127.0.0.1:${backend_port}/docs"
    echo "后端健康检查:  http://127.0.0.1:${backend_port}/health"
    echo "tdx-api:       http://127.0.0.1:${tdx_port}/api/health"
    echo ""
    echo "常用命令:"
    echo "  查看状态:    ./deploy.sh status"
    echo "  查看日志:    ./deploy.sh logs backend"
    echo "  健康检查:    ./deploy.sh health"
    echo "  重启服务:    ./deploy.sh restart"
    echo "  停止服务:    ./deploy.sh down"
    echo ""
    echo "日志目录:      ./log"
    echo "本地数据目录:  ./data ./db"
    echo "Compose 数据卷: mongo-data redis-data tdx-data"
    echo "============================================"
}

deploy() {
    ensure_env_file
    create_directories
    set_permissions

    print_info "构建并启动服务..."
    compose up -d --build
    wait_for_services
    health_check
    show_service_info
}

main() {
    local command="${1:-up}"
    local service="${2:-}"
    local require_daemon=1

    case "$command" in
        help|-h|--help)
            usage
            exit 0
            ;;
        config)
            require_daemon=0
            ;;
    esac

    check_docker "$require_daemon"

    case "$command" in
        up|deploy)
            deploy
            ;;
        start)
            ensure_env_file
            compose start
            wait_for_services
            show_service_info
            ;;
        stop)
            compose stop
            ;;
        restart)
            compose restart
            wait_for_services
            health_check
            ;;
        down)
            compose down
            ;;
        build)
            ensure_env_file
            compose build
            ;;
        status|ps)
            compose ps
            ;;
        logs)
            if [ -n "$service" ]; then
                compose logs -f "$service"
            else
                compose logs -f
            fi
            ;;
        health)
            health_check
            ;;
        config)
            ensure_env_file
            compose config --quiet
            print_success "Docker Compose 配置校验通过"
            ;;
        *)
            print_error "未知命令: ${command}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
