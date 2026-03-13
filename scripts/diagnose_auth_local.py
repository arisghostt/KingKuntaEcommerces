import os
import sys
import django
import json

# Ensure project root is on sys.path so Django can import settings
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.test import Client
c = Client()

payload = {"username": "admin", "password": "admin"}
resp = c.post('/api/auth/token/', data=json.dumps(payload), content_type='application/json')
print('status_code:', resp.status_code)
print('content-type:', resp['Content-Type'])
print('body:', resp.content.decode())
print('json:', end=' ')
try:
    print(resp.json())
except Exception as e:
    print('not json:', e)
