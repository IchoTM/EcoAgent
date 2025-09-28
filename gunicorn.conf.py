import os

# Get the port from environment variable or default to 8000
port = int(os.environ.get('PORT', '8000'))
bind = f"0.0.0.0:{port}"

# Number of worker processes
workers = 4

# Timeout for requests
timeout = 120

# Enable proxy headers parsing for Cloudflare
forwarded_allow_ips = '*'
proxy_allow_ips = '*'

# Security settings
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'https',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Allow for longer keepalive
keepalive = 65

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
