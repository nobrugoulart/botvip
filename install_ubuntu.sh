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

# Check if we have write permissions to the current directory
if [ ! -w "$(pwd)" ]; then
    echo "Warning: You don't have write permissions to $(pwd)"
    echo "Choose an option:"
    echo "1. Create virtual environment in your home directory"
    echo "2. Try to fix permissions for the current directory"
    echo "3. Specify a different directory for the virtual environment"
    read -p "Enter your choice (1-3): " venv_choice
    
    case $venv_choice in
        1)
            VENV_PATH="$HOME/botvip_venv"
            echo "Creating virtual environment in $VENV_PATH"
            python3 -m venv "$VENV_PATH"
            source "$VENV_PATH/bin/activate"
            ;;
        2)
            echo "Attempting to fix permissions for $(pwd)"
            sudo chown -R $USER:$USER $(pwd)
            echo "Creating virtual environment in current directory"
            python3 -m venv venv
            source venv/bin/activate
            ;;
        3)
            read -p "Enter the path for the virtual environment: " custom_path
            echo "Creating virtual environment in $custom_path"
            python3 -m venv "$custom_path"
            source "$custom_path/bin/activate"
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
else
    # We have write permissions, proceed normally
    python3 -m venv venv
    source venv/bin/activate
fi

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