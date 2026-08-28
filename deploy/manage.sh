#!/bin/bash
# Management script for TradeMind Worker on AGX Xavier

set -e

PROJECT_NAME="trademind"
DEPLOY_DIR="/home/${USER}/${PROJECT_NAME}"

cd ${DEPLOY_DIR}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
TradeMind Worker Management Script

Usage: $0 [COMMAND]

Commands:
    start       Start all services
    stop        Stop all services
    restart     Restart all services
    status      Show service status
    logs        Show logs (add service name for specific logs)
    scale       Scale a worker (e.g., scale indicator-worker 2)
    update      Pull latest images and restart
    cleanup     Remove unused containers and images
    backup      Backup data volumes
    stats       Show system resource usage
    shell       Open shell in a service container
    test        Run health tests
    help        Show this help

Examples:
    $0 start
    $0 logs indicator-worker
    $0 scale factor-worker 3
    $0 shell backtest-worker
EOF
}

start_services() {
    print_info "Starting TradeMind services..."
    sudo docker-compose up -d
    print_info "Services started"
    show_status
}

stop_services() {
    print_info "Stopping TradeMind services..."
    sudo docker-compose down
    print_info "Services stopped"
}

restart_services() {
    print_info "Restarting TradeMind services..."
    sudo docker-compose restart
    print_info "Services restarted"
    show_status
}

show_status() {
    echo "=========================================="
    echo "Service Status"
    echo "=========================================="
    sudo docker-compose ps
    
    echo ""
    echo "=========================================="
    echo "Resource Usage"
    echo "=========================================="
    sudo docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.PIDs}}" || true
}

show_logs() {
    if [ -z "$1" ]; then
        sudo docker-compose logs -f --tail=100
    else
        sudo docker-compose logs -f --tail=100 "$1"
    fi
}

scale_service() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        print_error "Usage: $0 scale <service> <count>"
        echo "Available services: indicator-worker, factor-worker, backtest-worker"
        exit 1
    fi
    
    SERVICE=$1
    COUNT=$2
    
    print_info "Scaling $SERVICE to $COUNT instances..."
    sudo docker-compose up -d --scale ${SERVICE}=${COUNT} --no-recreate ${SERVICE}
    print_info "Scaled successfully"
}

update_services() {
    print_info "Updating TradeMind services..."
    sudo docker-compose pull
    sudo docker-compose up -d --build
    print_info "Update complete"
}

cleanup_docker() {
    print_info "Cleaning up unused Docker resources..."
    sudo docker system prune -f
    sudo docker volume prune -f
    print_info "Cleanup complete"
}

backup_data() {
    BACKUP_DIR="${DEPLOY_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p ${BACKUP_DIR}
    
    print_info "Creating backup in ${BACKUP_DIR}..."
    
    # Backup Redis data
    sudo docker-compose exec redis redis-cli BGSAVE
    sudo cp -r data/redis ${BACKUP_DIR}/
    
    # Backup RabbitMQ data
    sudo docker-compose exec rabbitmq rabbitmqctl stop_app
    sudo docker-compose exec rabbitmq rabbitmqctl start_app
    
    # Backup configuration
    cp docker-compose.yml .env ${BACKUP_DIR}/
    
    print_info "Backup complete: ${BACKUP_DIR}"
}

show_stats() {
    echo "=========================================="
    echo "System Statistics"
    echo "=========================================="
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}'
    
    echo ""
    echo "Memory Usage:"
    free -h
    
    echo ""
    echo "Disk Usage:"
    df -h / ${DEPLOY_DIR}
    
    echo ""
    echo "Docker Stats:"
    sudo docker system df
    
    echo ""
    echo "GPU Stats:"
    if command -v tegrastats > /dev/null; then
        tegrastats --interval 100 --count 1
    else
        echo "tegrastats not available"
    fi
}

open_shell() {
    if [ -z "$1" ]; then
        print_error "Usage: $0 shell <service-name>"
        echo "Available services:"
        sudo docker-compose ps --services
        exit 1
    fi
    
    SERVICE=$1
    print_info "Opening shell in ${SERVICE}..."
    sudo docker-compose exec ${SERVICE} /bin/bash
}

run_tests() {
    print_info "Running health tests..."
    
    # Test RabbitMQ
    echo "Testing RabbitMQ..."
    if curl -s http://localhost:15672/api/overview -u trademind:<TRADEMIND_XAVIER_PASSWORD> > /dev/null; then
        echo "✓ RabbitMQ is responding"
    else
        echo "✗ RabbitMQ test failed"
    fi
    
    # Test Redis
    echo "Testing Redis..."
    if sudo docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        echo "✓ Redis is responding"
    else
        echo "✗ Redis test failed"
    fi
    
    # Test Task Agent
    echo "Testing Task Agent..."
    if curl -s http://localhost:8081/health > /dev/null; then
        echo "✓ Task Agent is responding"
    else
        echo "✗ Task Agent test failed"
    fi
    
    # Test Monitor Agent
    echo "Testing Monitor Agent..."
    if curl -s http://localhost:8082/health > /dev/null; then
        echo "✓ Monitor Agent is responding"
    else
        echo "✗ Monitor Agent test failed"
    fi
}

# Main command handler
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    scale)
        scale_service "$2" "$3"
        ;;
    update)
        update_services
        ;;
    cleanup)
        cleanup_docker
        ;;
    backup)
        backup_data
        ;;
    stats)
        show_stats
        ;;
    shell)
        open_shell "$2"
        ;;
    test|tests)
        run_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
