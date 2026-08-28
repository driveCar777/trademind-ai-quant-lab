#!/bin/bash
# Setup script for AGX Xavier (L4T R32.1, Ubuntu 18.04)
# This script runs on the Xavier device

set -e

PROJECT_NAME="trademind"
DEPLOY_DIR="/home/${USER}/${PROJECT_NAME}"

echo "=========================================="
echo "TradeMind Worker Setup on AGX Xavier"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

cd ${DEPLOY_DIR}

# Check system resources
print_info "Checking system resources..."
echo "CPU: $(nproc) cores"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $4}') available"

# Check Docker installation
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Installing Docker..."
    
    # Install Docker for ARM64
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ${USER}
    
    print_warn "Docker installed. Please log out and log back in, then re-run this script."
    exit 0
fi

# Check Docker Compose
print_info "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_warn "Docker Compose not found. Installing..."
    
    # Install docker-compose for ARM64
    sudo apt-get update
    sudo apt-get install -y python3-pip
    sudo pip3 install docker-compose
fi

# Verify Docker is running
print_info "Verifying Docker daemon..."
if ! sudo docker info &> /dev/null; then
    print_error "Docker daemon not running. Starting..."
    sudo systemctl start docker
    sleep 2
fi

# Check NVIDIA Container Toolkit
print_info "Checking NVIDIA Container Toolkit..."
if ! sudo docker run --rm --gpus all nvcr.io/nvidia/l4t-base:r32.1 nvidia-smi &> /dev/null 2>&1; then
    print_warn "NVIDIA Container Toolkit may not be properly configured."
    print_warn "Please ensure JetPack is installed with nvidia-docker2."
fi

# Create necessary directories
print_info "Creating directories..."
mkdir -p data/redis data/rabbitmq data/backtest-results
mkdir -p logs cache

# Set permissions
print_info "Setting permissions..."
sudo chown -R ${USER}:${USER} data/ logs/ cache/

# Update .env file for Xavier
print_info "Configuring environment..."
if [ -f ".env" ]; then
    # Update worker name for this device
    sed -i "s/WORKER_NAME=.*/WORKER_NAME=AGX-Xavier-Worker-01/" .env
    sed -i "s/WORKER_LOCATION=.*/WORKER_LOCATION=Xavier-Edge/" .env
    
    print_info "Environment configured"
fi

# Pull base images (optional - can be slow on Xavier)
print_info "Checking base images..."
print_warn "Base image pulling can take a long time on Xavier. Continue? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    print_info "Pulling base images..."
    sudo docker pull nvcr.io/nvidia/l4t-pytorch:r32.1-py3 || true
    sudo docker pull arm64v8/rabbitmq:3.9-management-alpine || true
    sudo docker pull arm64v8/redis:6.2-alpine || true
fi

# Build images
print_info "Building TradeMind images..."
print_warn "This may take 30-60 minutes on Xavier depending on network speed..."

# Build in order of dependency
sudo -E docker-compose build --parallel

print_info "Build complete!"

# Start services
print_info "Starting TradeMind services..."
sudo -E docker-compose up -d

# Wait for services to start
print_info "Waiting for services to initialize..."
sleep 10

# Check service status
print_info "Checking service status..."
sudo docker-compose ps

# Verify RabbitMQ
print_info "Verifying RabbitMQ..."
until curl -s http://localhost:15672/api/overview -u trademind:<TRADEMIND_XAVIER_PASSWORD> > /dev/null 2>&1; do
    echo "Waiting for RabbitMQ..."
    sleep 2
done
print_info "RabbitMQ is ready"

# Verify Redis
print_info "Verifying Redis..."
until sudo docker-compose exec -T redis redis-cli ping | grep -q PONG; do
    echo "Waiting for Redis..."
    sleep 2
done
print_info "Redis is ready"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - RabbitMQ Management: http://$(hostname -I | awk '{print $1}'):15672"
echo "  - Task Agent API:      http://$(hostname -I | awk '{print $1}'):8081"
echo "  - Monitor Agent:       http://$(hostname -I | awk '{print $1}'):8082"
echo ""
echo "Default credentials:"
echo "  RabbitMQ: trademind / <TRADEMIND_XAVIER_PASSWORD>"
echo ""
echo "Useful commands:"
echo "  View logs:   sudo docker-compose logs -f"
echo "  Stop all:    sudo docker-compose down"
echo "  Restart:     sudo docker-compose restart"
echo "  Scale:       sudo docker-compose up -d --scale indicator-worker=2"
echo ""
echo "Waiting for Master server connection..."
echo ""
