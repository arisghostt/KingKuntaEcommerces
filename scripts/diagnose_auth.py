import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

url = 'http://127.0.0.1:8000/api/auth/token/'
# adjust username/password as needed
payload = {'username': 'admin', 'password': 'admin'}

try:
    r = requests.post(url, json=payload, timeout=5)
    print('status_code:', r.status_code)
    print('headers:', r.headers.get('content-type'))
    print('text:', r.text)
except Exception as e:
    print('request error:', e)
