import os

# Get the port from environment variable or default to 10000
port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"

# Number of worker processes
workers = 4

# Timeout for requests
timeout = 120

# Enable proxy headers parsing for Cloudflare
forwarded_allow_ips = '*'
proxy_allow_ips = '*'
