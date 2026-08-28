#!/bin/bash
# TradeMind Worker Deployment Script for AGX Xavier
# Target: AGX Xavier (L4T R32.1, Ubuntu 18.04)
# IP: 192.168.1.111
# User: dji

set -e

# Configuration
XAVIER_IP="192.168.1.111"
XAVIER_USER="dji"
PROJECT_NAME="trademind"
DEPLOY_DIR="/home/${XAVIER_USER}/${PROJECT_NAME}"

echo "=========================================="
echo "TradeMind Worker Deployment"
echo "Target: AGX Xavier @ ${XAVIER_IP}"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create deployment package
print_info "Creating deployment package..."
DEPLOY_PACKAGE="trademind-worker-deploy.tar.gz"

# Package necessary files
tar -czf ${DEPLOY_PACKAGE} \
    docker-compose.yml \
    .env \
    indicator-worker/ \
    factor-worker/ \
    backtest-worker/ \
    task-agent/ \
    monitor-agent/ \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.tar.gz'

print_info "Deployment package created: ${DEPLOY_PACKAGE}"

# Transfer to Xavier
print_info "Transferring to AGX Xavier..."
scp ${DEPLOY_PACKAGE} ${XAVIER_USER}@${XAVIER_IP}:/tmp/

# Execute remote deployment
print_info "Executing remote deployment..."
ssh ${XAVIER_USER}@${XAVIER_IP} << 'REMOTE_SCRIPT'
#!/bin/bash
set -e

PROJECT_NAME="trademind"
DEPLOY_DIR="/home/${USER}/${PROJECT_NAME}"
DEPLOY_PACKAGE="/tmp/trademind-worker-deploy.tar.gz"

echo "[REMOTE] Setting up deployment directory..."
mkdir -p ${DEPLOY_DIR}
cd ${DEPLOY_DIR}

# Extract package
echo "[REMOTE] Extracting package..."
tar -xzf ${DEPLOY_PACKAGE}

# Create necessary directories
mkdir -p data cache logs

# Set permissions
chmod +x deploy/*.sh 2>/dev/null || true

echo "[REMOTE] Deployment files extracted to ${DEPLOY_DIR}"
REMOTE_SCRIPT

print_info "Files transferred successfully!"

# Run setup script on Xavier
print_info "Running setup on AGX Xavier..."
ssh ${XAVIER_USER}@${XAVIER_IP} "bash ${DEPLOY_DIR}/deploy/setup-xavier.sh"

print_info "Deployment complete!"
print_info "Access Task Agent API: http://${XAVIER_IP}:8081"
print_info "Access Monitor Agent: http://${XAVIER_IP}:8082"

# Cleanup
rm -f ${DEPLOY_PACKAGE}
