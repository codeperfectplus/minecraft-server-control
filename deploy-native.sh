#!/bin/bash

#############################################
# Mineboard Native Deployment Script
# Standalone installer - clones repo and deploys
#############################################

set -e

# Configuration
REPO_URL="https://github.com/codeperfectplus/mineboard.git"
TEMP_DIR="/tmp/mineboard-installer-$$"
INSTALL_DIR="/opt/mineboard"
SERVICE_NAME="mineboard"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
APP_USER="mineboard"
APP_PORT="${PORT:-5090}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
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

# Show usage
show_usage() {
    echo ""
    echo "Mineboard Native Deployment Script"
    echo "Usage: sudo bash deploy-native.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install     Install Mineboard"
    echo "  --uninstall   Uninstall Mineboard"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo bash deploy-native.sh --install"
    echo "  sudo bash deploy-native.sh --uninstall"
    echo ""
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check if Git is installed
check_git() {
    print_info "Checking Git installation..."
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Installing..."
        apt-get update && apt-get install -y git || {
            print_error "Failed to install git. Please install it manually."
            exit 1
        }
    fi
    print_success "Git is installed"
}

# Check if Python 3.8+ is installed
check_python() {
    print_info "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION is installed"
    
    # Check for pip
    if ! python3 -m pip --version &> /dev/null; then
        print_warning "pip not found, attempting to install..."
        python3 -m ensurepip --default-pip 2>/dev/null || print_warning "Could not install pip automatically"
    fi
    
    print_success "Python environment is ready"
}

# Clone repository
clone_repo() {
    print_info "Cloning Mineboard repository..."
    
    if [ -d "$TEMP_DIR" ]; then
        print_warning "Cleaning up old temporary directory..."
        rm -rf "$TEMP_DIR"
    fi
    
    git clone "$REPO_URL" "$TEMP_DIR" || {
        print_error "Failed to clone repository"
        exit 1
    }
    
    print_success "Repository cloned successfully"
}

# Create application user
create_user() {
    print_info "Creating application user: $APP_USER"
    
    if id "$APP_USER" &>/dev/null; then
        print_warning "User $APP_USER already exists"
    else
        useradd --system --no-create-home --shell /bin/false $APP_USER
        print_success "User $APP_USER created"
    fi
}

# Create installation directory
create_install_dir() {
    print_info "Creating installation directory: $INSTALL_DIR"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists"
        print_info "Stopping service if running..."
        systemctl stop $SERVICE_NAME 2>/dev/null || true
        print_info "Removing existing directory..."
        rm -rf "$INSTALL_DIR"
    fi
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/data"
    print_success "Installation directory created"
}

# Copy application files
copy_files() {
    print_info "Copying application files..."
    
    cd "$TEMP_DIR"
    
    # Copy all files except .git, __pycache__, venv, etc.
    rsync -av --progress \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='venv' \
        --exclude='data' \
        --exclude='minecraft-data' \
        --exclude='docker-compose.yml' \
        --exclude='Dockerfile' \
        "$TEMP_DIR/" "$INSTALL_DIR/" || {
            # Fallback to cp if rsync is not available
            print_warning "rsync not found, using cp instead..."
            cp -r "$TEMP_DIR/"* "$INSTALL_DIR/" 2>/dev/null || true
            find "$TEMP_DIR" -name ".*" ! -name "." ! -name ".." -exec cp -r {} "$INSTALL_DIR/" \; 2>/dev/null || true
        }
    
    print_success "Files copied successfully"
}

# Create virtual environment and install dependencies
setup_python_env() {
    print_info "Creating Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Try to create venv, if it fails, continue anyway
    if python3 -m venv venv 2>/dev/null; then
        print_success "Virtual environment created"
    else
        print_warning "Could not create venv, trying with --without-pip flag..."
        python3 -m venv --without-pip venv 2>/dev/null || {
            print_warning "venv creation failed, will try to install dependencies globally"
            mkdir -p venv/bin
            ln -sf $(which python3) venv/bin/python
            ln -sf $(which pip3) venv/bin/pip 2>/dev/null || true
        }
    fi
    
    print_info "Installing Python dependencies..."
    if [ -f "$INSTALL_DIR/venv/bin/pip" ]; then
        "$INSTALL_DIR/venv/bin/pip" install --upgrade pip 2>/dev/null || true
        "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    else
        print_warning "Using system pip to install dependencies..."
        python3 -m pip install -r "$INSTALL_DIR/requirements.txt" --user
    fi
    
    print_success "Python dependencies installed"
}

# Create .env file if it doesn't exist
create_env_file() {
    print_info "Checking .env file..."
    
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        print_info "Creating .env file..."
        cat > "$INSTALL_DIR/.env" << EOF
# Mineboard Configuration
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | base64)

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
PORT=$APP_PORT

# Database Path
DB_PATH=/opt/mineboard/data/data.db

# Optional: Set default admin credentials
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=changeme

# Optional: Set URL prefix if running behind a reverse proxy
# URL_PREFIX=/mineboard
EOF
        chmod 600 "$INSTALL_DIR/.env"
        print_success ".env file created with random SECRET_KEY"
    else
        print_success ".env file already exists"
    fi
}

# Update app.py to use environment port
update_app_py() {
    print_info "Updating app.py for production..."
    
    # Check if app.py needs updating
    if ! grep -q "if __name__ == '__main__':" "$INSTALL_DIR/app.py"; then
        cat >> "$INSTALL_DIR/app.py" << 'EOF'

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5090))
    app.run(host='0.0.0.0', port=port, debug=False)
EOF
        print_success "app.py updated for production"
    else
        print_info "app.py already configured"
    fi
}

# Set proper permissions
set_permissions() {
    print_info "Setting file permissions..."
    
    chown -R $APP_USER:$APP_USER "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    chmod 600 "$INSTALL_DIR/.env"
    chmod -R 775 "$INSTALL_DIR/data"
    
    print_success "Permissions set successfully"
}

# Install systemd service
install_service() {
    print_info "Installing systemd service..."
    
    # Copy service file
    cp "$INSTALL_DIR/mineboard-native.service" "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Systemd service installed"
}

# Enable and start service
start_service() {
    print_info "Enabling and starting Mineboard service..."
    
    # Enable service to start on boot
    systemctl enable $SERVICE_NAME
    
    # Start the service
    systemctl start $SERVICE_NAME
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check status
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Mineboard service is running!"
    else
        print_error "Failed to start Mineboard service"
        print_info "Check logs with: journalctl -u $SERVICE_NAME -f"
        systemctl status $SERVICE_NAME --no-pager
        exit 1
    fi
}

# Cleanup temp directory
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        print_info "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
        print_success "Cleanup complete"
    fi
}

# Display final information
show_install_info() {
    echo ""
    echo "======================================"
    print_success "Mineboard Deployment Complete!"
    echo "======================================"
    echo ""
    echo "Installation Directory: $INSTALL_DIR"
    echo "Service Name: $SERVICE_NAME"
    echo "Running as User: $APP_USER"
    echo ""
    echo "Access Mineboard at: http://localhost:$APP_PORT"
    echo ""
    echo "======================================"
    echo "  Login Information"
    echo "======================================"
    echo ""
    echo "On first visit, you'll be prompted to create an admin account."
    echo ""
    echo "If default credentials are set in .env file:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    echo "⚠️  IMPORTANT: Change the default password after first login!"
    echo ""
    echo "======================================"
    echo "  Service Management"
    echo "======================================"
    echo ""
    echo "  Start:   sudo systemctl start $SERVICE_NAME"
    echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
    echo "  Restart: sudo systemctl restart $SERVICE_NAME"
    echo "  Status:  sudo systemctl status $SERVICE_NAME"
    echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    print_info "Configure your RCON settings in the Settings page to connect to your Minecraft server!"
    echo ""
}

# Uninstall function
uninstall() {
    echo ""
    echo "======================================"
    echo "  Uninstalling Mineboard"
    echo "======================================"
    echo ""
    
    print_info "Stopping service..."
    systemctl stop $SERVICE_NAME 2>/dev/null || true
    
    print_info "Disabling service..."
    systemctl disable $SERVICE_NAME 2>/dev/null || true
    
    print_info "Removing service file..."
    rm -f $SERVICE_FILE
    
    print_info "Removing application files..."
    rm -rf $INSTALL_DIR
    
    print_info "Removing application user..."
    userdel $APP_USER 2>/dev/null || true
    
    print_info "Reloading systemd..."
    systemctl daemon-reload
    
    echo ""
    print_success "Mineboard has been uninstalled successfully!"
    echo ""
}

# Install function
install() {
    echo ""
    echo "======================================"
    echo "  Mineboard Native Deployment"
    echo "  (Without Docker)"
    echo "======================================"
    echo ""
    
    check_root
    check_git
    check_python
    clone_repo
    create_user
    create_install_dir
    copy_files
    setup_python_env
    create_env_file
    update_app_py
    set_permissions
    install_service
    start_service
    cleanup
    show_install_info
}

# Main script logic
main() {
    case "${1:-}" in
        --install)
            install
            ;;
        --uninstall)
            check_root
            uninstall
            ;;
        --help)
            show_usage
            ;;
        *)
            print_error "Invalid option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
