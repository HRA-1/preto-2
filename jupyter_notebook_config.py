import sys

c = get_config()

# Server settings
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True

# Disable authentication for development
c.ServerApp.token = ''
c.ServerApp.password = ''

# Add src to Python path
sys.path.insert(0, '/app/src')
