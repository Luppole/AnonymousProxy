import requests

proxy = {
    'http': 'http://127.0.0.1:8888',
    'https': 'http://127.0.0.1:8888',
}

try:
    response = requests.get('https://www.google.com/', proxies=proxy)
    print('HTTP Response:', response.status_code)

    response = requests.get('https://www.google.com/', proxies=proxy, verify=False)
    print('HTTPS Response:', response.status_code)
except Exception as e:
    print('Error:', e)
