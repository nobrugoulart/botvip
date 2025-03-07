#!/bin/bash

# Exit on any error
set -e

echo "Starting Bot VIP System Installation..."

# Check if running as root
if [ "$(id -u)" = "0" ]; then
    echo "Error: This script should not be run as root"
    exit 1
fi

# Function to check command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed. Installing..."
        sudo apt-get install -y $1
    fi
}

# Update package list and install system dependencies
echo "Updating system and installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git nginx

# Check required commands
check_command python3
check_command pip3
check_command git

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip wheel

# Install Python dependencies with error handling
echo "Installing Python packages..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
TELEGRAM_TOKEN=your_telegram_token
MERCADOPAGO_ACCESS_TOKEN=your_mercadopago_token
VIP_GROUP_ID=your_group_id
ADMIN_USER_ID=your_admin_id
PAYMENT_AMOUNT=29.90
EOL
    echo "Created .env file. Please edit it with your actual credentials."
fi

# Create systemd service for the bot
echo "Creating bot systemd service..."
sudo tee /etc/systemd/system/botvip.service > /dev/null << EOL
[Unit]
Description=Bot VIP Telegram Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:$PATH
ExecStart=$(pwd)/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Configure Nginx for the web panel
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/botvip > /dev/null << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/botvip /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Reload systemd and enable services
echo "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable botvip
sudo systemctl start botvip

echo "
Installation completed successfully!

Important next steps:
1. Edit the .env file with your credentials: nano .env
2. Access the web panel at: http://your-server-ip
3. Monitor the bot service: sudo systemctl status botvip
4. View logs: sudo journalctl -u botvip

For support, visit: https://github.com/seu-usuario/botvip"