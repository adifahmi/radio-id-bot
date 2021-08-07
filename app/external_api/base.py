import requests

TIMEOUT = 5


def api(api_base, headers=None):
    S = requests.Session()

    # To fix "Connection pool is full, discarding connection: xxx"
    # see https://stackoverflow.com/q/23632794/4844294 for detail
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
    S.mount('http://', adapter)
    S.mount('https://', adapter)

    def req(method, endpoint, data=None, json_encoded=True, force_data=False, region=None):
        url = api_base() + endpoint
        if region is not None:
            url = api_base() % region + endpoint
        method = method.upper()
        print(f"START-{method} - {url}")
        try:
            if method == 'GET':
                resp = S.get(url, headers=headers, params=data, timeout=TIMEOUT)
            elif method == 'POST':
                if json_encoded and not force_data:
                    resp = S.post(url, headers=headers, json=data, timeout=TIMEOUT)
                else:
                    resp = S.post(url, headers=headers, data=data, timeout=TIMEOUT)
            elif method == 'PUT':
                resp = S.put(url, headers=headers, data=data, timeout=TIMEOUT)
            else:
                return None, {}, {'error': 'wrong-method'}

            print(f"END-{method} - {url} | {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text
                return data, {'error': '', 'status_code': resp.status_code}
            else:
                print(f"FAIL-{method} - {url} | status_code: {resp.status_code} | response: {resp.content}")
                return None, {'error': resp.content.decode('utf-8'), 'status_code': resp.status_code}
        except requests.RequestException as e:
            print(f"ERROR-{method} - {url} | exception: {e}")
            return None, {'error': str(e), 'status_code': 500}

    return req
