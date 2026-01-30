#!/bin/bash
# Quick start script for Achievement Portfolio

set -e

echo "🎯 Achievement Portfolio - Quick Start"
echo "======================================"
echo ""

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please install Podman first."
    echo "   https://podman.io/getting-started/installation"
    exit 1
fi

# Check if podman-compose is installed
if ! command -v podman-compose &> /dev/null; then
    echo "⚠️  podman-compose is not installed. Installing..."
    pip3 install podman-compose || pip install podman-compose
    echo "✅ podman-compose installed"
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚙️  Setting up environment..."
    read -p "Admin username [admin]: " ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-admin}
    
    read -s -p "Admin password: " ADMIN_PASS
    echo
    read -s -p "Confirm password: " ADMIN_PASS_CONFIRM
    echo
    
    if [ "$ADMIN_PASS" != "$ADMIN_PASS_CONFIRM" ]; then
        echo "❌ Passwords do not match"
        exit 1
    fi
    
    if [ ${#ADMIN_PASS} -lt 6 ]; then
        echo "❌ Password must be at least 6 characters"
        exit 1
    fi
    
    JWT_SECRET=$(openssl rand -hex 32)
    
    cat > backend/.env << EOF
DATABASE_PATH=/app/data/portfolio.db
PORT=3000
NODE_ENV=production
JWT_SECRET=${JWT_SECRET}
ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}
FRONTEND_URL=http://localhost:5173
EOF
    echo "✅ Environment configured"
else
    echo "✅ Environment file exists"
fi

# Create data directory
mkdir -p data

echo ""
echo "🏗️  Building and starting containers..."
podman-compose -f podman/podman-compose.yml up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📱 Access your portfolio:"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:3000"
echo ""
echo "📋 Login credentials:"
echo "   Username: ${ADMIN_USER:-admin}"
echo "   (Use the password you set during setup)"
echo ""
echo "📚 Useful commands:"
echo "   Stop:   podman-compose -f podman/podman-compose.yml down"
echo "   Logs:   podman-compose -f podman/podman-compose.yml logs -f"
echo "   Status: podman ps"
echo ""
