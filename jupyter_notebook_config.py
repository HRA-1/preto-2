import sys
import os

c = get_config()

# Server settings
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True

# Disable authentication for development
c.ServerApp.token = ''
c.ServerApp.password = ''

# Add src to Python path (works for both Docker and local)
# Docker: /app/src, Local: relative to config file
if os.path.exists('/app/src'):
    src_path = '/app/src'
else:
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))

if src_path not in sys.path:
    sys.path.insert(0, src_path)
