#!/bin/bash
# ============================================
# EC2 t3.medium Setup Script
# Run this on a fresh Amazon Linux 2023 / Ubuntu 22.04 instance
# ============================================
#
# Usage:
#   chmod +x ec2-setup.sh
#   sudo ./ec2-setup.sh
#
set -e

echo "============================================"
echo "  Content Studio Agent - EC2 Setup"
echo "  Instance: t3.medium (2 vCPU, 4 GB RAM)"
echo "============================================"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi

echo "Detected OS: $OS"

# --- Install Docker ---
echo ""
echo ">>> Installing Docker..."

if [ "$OS" = "amzn" ]; then
    # Amazon Linux 2023
    yum update -y
    yum install -y docker git
    systemctl start docker
    systemctl enable docker
    usermod -aG docker ec2-user

elif [ "$OS" = "ubuntu" ]; then
    # Ubuntu 22.04 / 24.04
    apt-get update
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git
    usermod -aG docker ubuntu
fi

# --- Install Docker Compose (standalone, if not bundled) ---
if ! command -v docker compose &> /dev/null; then
    echo ""
    echo ">>> Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="v2.32.4"
    curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

# --- Configure swap (useful for t3.medium with 4 GB RAM) ---
echo ""
echo ">>> Configuring 2 GB swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap configured: 2 GB"
else
    echo "Swap already exists, skipping."
fi

# --- Create app directory ---
APP_DIR="/opt/content-studio"
echo ""
echo ">>> Setting up app directory at ${APP_DIR}..."
mkdir -p ${APP_DIR}

# --- Configure Docker log rotation ---
echo ""
echo ">>> Configuring Docker log rotation..."
cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "50m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF
systemctl restart docker

# --- Print next steps ---
echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Next Steps:"
echo ""
echo "  1. Log out and back in (for docker group):"
echo "     exit"
echo "     ssh <your-instance>"
echo ""
echo "  2. Clone or copy your app to ${APP_DIR}:"
echo "     cd ${APP_DIR}"
echo "     git clone <your-repo-url> ."
echo ""
echo "  3. Create your .env file:"
echo "     cp env.example .env"
echo "     nano .env   # Add your API keys"
echo ""
echo "  4. Build and start:"
echo "     docker compose up -d --build"
echo ""
echo "  5. Check status:"
echo "     docker compose ps"
echo "     docker compose logs -f"
echo "     curl http://localhost:5001/health"
echo ""
echo "  6. Open port 5001 in your EC2 Security Group"
echo "     (or use port 80 by setting PORT=80 in .env)"
echo ""
echo "============================================"
