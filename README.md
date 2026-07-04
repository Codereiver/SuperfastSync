# SuperfastSync

A simple file server benchmarking application for testing upload/download performance with metric tracking.

## Features

- 🚀 Simple file upload and download interface
- 📊 Performance benchmarking (upload/download speeds)
- 🌐 Client tracking (IP, reverse DNS, AS lookup)
- 📈 Historical dashboard for metrics
- 🎨 Modern, responsive web UI with drag-and-drop
- 🔒 Authentication to prevent unauthorized access

## Authentication & Security

The application requires login to access all features. Default credentials (development only):
- **Username:** `admin`
- **Password:** `admin`

### Security Configuration

**CRITICAL:** Before deploying to production, you MUST set these environment variables:

```bash
# Generate a secure secret key
export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Set strong credentials
export AUTH_USERNAME=your_username
export AUTH_PASSWORD=your_secure_password

# Disable debug mode (REQUIRED for production)
export DEBUG=false

# Run the application
uv run python -m app.server
```

**Security Features:**
- Session-based authentication with 24-hour timeout
- Secure session cookies (HttpOnly, SameSite)
- Constant-time credential comparison (prevents timing attacks)
- DNS lookup timeout protection
- Path traversal protection for file operations

See [SECURITY.md](SECURITY.md) for complete security documentation.

## Quick Start (Local Development)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/SuperfastSync.git
cd SuperfastSync

# Install dependencies
uv sync

# Run the application
uv run python -m app.server
```

The application will be available at `http://localhost:5000`

## Local Testing with Multipass (macOS)

Multipass provides a quick way to test deployment on a clean Ubuntu VM before deploying to AWS.

### Install Multipass

```bash
# Install via Homebrew
brew install multipass
```

### Launch and Setup VM

```bash
# Create an Ubuntu VM with 20GB disk and 2GB RAM
multipass launch --name superfastsync --disk 20G --memory 2G

# Mount your local project directory into the VM (for live development)
multipass mount /Users/peterlee/Documents/Yorcadia/Codereiver/SuperfastSync superfastsync:/home/ubuntu/SuperfastSync

# Shell into the VM
multipass shell superfastsync
```

### Deploy in the VM

Once inside the VM, follow the Ubuntu deployment instructions:

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Check available Python version (Ubuntu 22.04 has Python 3.10+)
python3 --version

# Install Python and pip (if needed)
sudo apt install python3 python3-pip python3-venv -y

# Install uv (it will use the system Python)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Navigate to project (mounted from your Mac)
cd /home/ubuntu/SuperfastSync

# Install dependencies (uv will handle Python version requirements)
uv sync

# Create storage directory
mkdir -p storage

# Run the application
uv run python -m app.server
```

### Access from Your Mac

```bash
# Get the VM's IP address (run from Mac terminal, not inside VM)
multipass info superfastsync
```

The output will show an IPv4 address like `192.168.64.x`. Access the application at:
- `http://192.168.64.x:5000` (direct Flask access)
- Or set up nginx inside the VM and use `https://192.168.64.x`

### Useful Multipass Commands

```bash
# Stop the VM
multipass stop superfastsync

# Start the VM
multipass start superfastsync

# Restart the VM
multipass restart superfastsync

# Get VM info (including IP address)
multipass info superfastsync

# List all VMs
multipass list

# Unmount the project directory
multipass umount superfastsync

# Delete the VM when done
multipass delete superfastsync
multipass purge
```

### Benefits of Multipass for Testing

- **Clean environment**: Test deployment on a fresh Ubuntu system
- **Live development**: Edit files on your Mac, test immediately in the VM
- **No git needed**: Changes are instant via mounted directory
- **Quick iteration**: Destroy and recreate VMs easily
- **AWS-like**: Ubuntu environment similar to AWS EC2

## AWS Linux Deployment

### Prerequisites

A fresh AWS Linux instance (Amazon Linux 2023, Ubuntu 22.04+, or similar)

### Installation Steps

```bash
# Update system packages
sudo yum update -y  # For Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # For Ubuntu

# Check Python version (needs 3.10+)
python3 --version

# Install Python and dependencies
# For Amazon Linux 2023:
sudo yum install python3 python3-pip -y
# OR for Ubuntu 22.04+ (comes with Python 3.10):
sudo apt install python3 python3-pip python3-venv -y

# If you need Python 3.11+ specifically (optional):
# For Ubuntu, you may need to add deadsnakes PPA:
# sudo add-apt-repository ppa:deadsnakes/ppa -y
# sudo apt update
# sudo apt install python3.11 python3.11-venv -y

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH for current session
export PATH="$HOME/.cargo/bin:$PATH"

# Make it permanent (add to ~/.bashrc)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

# Clone the repository
git clone https://github.com/yourusername/SuperfastSync.git
cd SuperfastSync

# Install dependencies
uv sync

# Create storage directory (if not exists)
mkdir -p storage

# Run the application
uv run python -m app.server
```

### Running in Production

For production deployment, use a process manager and reverse proxy:

```bash
# Option 1: Run with nohup (simple background process)
nohup uv run python -m app.server > app.log 2>&1 &

# Option 2: Use systemd service (recommended)
# Create a service file at /etc/systemd/system/superfastsync.service
```

#### Example systemd service file:

```ini
[Unit]
Description=SuperfastSync File Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/SuperfastSync
Environment="PATH=/home/ec2-user/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
Environment="SECRET_KEY=your_64_char_random_hex_string_here"
Environment="AUTH_USERNAME=your_username"
Environment="AUTH_PASSWORD=your_secure_password"
Environment="DEBUG=false"
ExecStart=/home/ec2-user/.cargo/bin/uv run python -m app.server
Restart=always

[Install]
WantedBy=multi-user.target
```

**IMPORTANT:** Generate and set:
- `SECRET_KEY`: Run `python3 -c 'import secrets; print(secrets.token_hex(32))'`
- `AUTH_USERNAME` and `AUTH_PASSWORD`: Your secure credentials
- `DEBUG`: Must be `false` in production

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable superfastsync
sudo systemctl start superfastsync

# Check status
sudo systemctl status superfastsync
```

### Security Groups (AWS)

Ensure your AWS security group allows inbound traffic:
- **Port 443** - HTTPS access to the application
- **Port 80** - HTTP access (optional, can redirect to HTTPS)
- **Port 22** - SSH access for management

**Note:** Do not expose port 5000 - Flask will only be accessible via nginx on the same machine.

### Nginx Reverse Proxy with SSL

#### Install and Configure Nginx

```bash
# Install nginx
sudo yum install nginx -y  # For Amazon Linux
# OR
sudo apt install nginx -y  # For Ubuntu

# Start and enable nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Create Self-Signed SSL Certificate

```bash
# Create directory for SSL certificates
sudo mkdir -p /etc/nginx/ssl

# Generate self-signed certificate (valid for 365 days)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/superfastsync.key \
  -out /etc/nginx/ssl/superfastsync.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-server-ip-or-domain"

# Secure the private key
sudo chmod 600 /etc/nginx/ssl/superfastsync.key
sudo chmod 644 /etc/nginx/ssl/superfastsync.crt
```

#### Configure Nginx

Create the configuration file:

```bash
# For Amazon Linux / RHEL
sudo nano /etc/nginx/conf.d/superfastsync.conf

# For Ubuntu
sudo nano /etc/nginx/sites-available/superfastsync
# Then create symlink:
# sudo ln -s /etc/nginx/sites-available/superfastsync /etc/nginx/sites-enabled/
```

**Nginx configuration (`superfastsync.conf`):**

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name _;

    # SSL certificate configuration
    ssl_certificate /etc/nginx/ssl/superfastsync.crt;
    ssl_certificate_key /etc/nginx/ssl/superfastsync.key;

    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # No file size limit for uploads
    client_max_body_size 0;

    # Proxy settings for Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # For large file uploads
        proxy_request_buffering off;
        proxy_buffering off;

        # Increase timeouts for large file transfers
        proxy_read_timeout 3600;
        proxy_connect_timeout 3600;
        proxy_send_timeout 3600;
    }
}
```

#### Enable and Test Nginx Configuration

```bash
# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

#### Accessing the Application

Your application will now be available at:
- `https://your-server-ip-or-domain` (HTTPS - recommended)
- `http://your-server-ip-or-domain` (HTTP - redirects to HTTPS)

**Note:** Browsers will show a security warning for self-signed certificates. Click "Advanced" and proceed to accept the certificate. For production use with a real domain, consider using Let's Encrypt for a free trusted certificate.

## Configuration

(To be documented as configuration options are added)

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details

## Documentation

For detailed architecture and development guidelines, see [CLAUDE.md](CLAUDE.md)
