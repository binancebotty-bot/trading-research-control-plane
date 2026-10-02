import json
import subprocess
import urllib.request
import websocket
import os

BASE = 'https://api.github.com/repos/binancebotty-bot/trading-research-control-plane'
THREAD = os.environ.get('PINE_TARGET_THREAD', '6abf60c8-4598-83eb-bc80-57a926d80b2e')
assert THREAD == '6abf60c8-4598-83eb-bc80-57a926d80b2e', 'Hermes may contact ONLY the bound Pine Controller; oversight is human-only'

def github(path, body=None):
    r = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    credentials = dict(x.split('=', 1) for x in r.stdout.splitlines() if '=' in x)
    headers = {'Authorization': 'Bearer ' + credentials['password'], 'Accept': 'application/vnd.github+json', 'User-Agent': 'Hermes-Pine-Commissioning'}
    data = None if body is None else json.dumps(body).encode()
    if data is not None:
        headers['Content-Type'] = 'application/json'
    return json.load(urllib.request.urlopen(urllib.request.Request(BASE + path, headers=headers, data=data), timeout=30))

def post(body):
    result = github('/issues/1/comments', {'body': body})
    verified = github('/issues/comments/' + str(result['id']))
    assert verified['body'] == body
    print('POST_VERIFIED=' + str(result['id']), flush=True)
    return verified

class Page:
    def __init__(self):
        targets = json.load(urllib.request.urlopen('http://127.0.0.1:9223/json/list', timeout=10))
        matches = [t for t in targets if t.get('type') == 'page' and t.get('url', '').split('?')[0].endswith('/c/' + THREAD)]
        assert len(matches) == 1, 'Exact Pine target must be unique'
        self.ws = websocket.create_connection(matches[0]['webSocketDebuggerUrl'], suppress_origin=True, timeout=330)
        self.n = 0
    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            result = json.loads(self.ws.recv())
            if result.get('id') == self.n:
                if 'error' in result:
                    raise RuntimeError(result['error'])
                return result['result']
    def js(self, expression):
        result = self.call('Runtime.evaluate', expression=expression, returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in result:
            raise RuntimeError(result['exceptionDetails'])
        return result['result'].get('value')
    def close(self):
        self.ws.close()

SELECTOR = '[data-composer-body] [contenteditable=true], form textarea'
INSPECT = '''(() => {
const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return e.isConnected&&r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&r.bottom>0&&r.top<innerHeight;};
return {url:location.href,stop:!!document.querySelector('button[aria-label="Stop"],button[data-testid="stop-button"]'),editors:Array.from(document.querySelectorAll('[contenteditable=true],textarea')).map(e=>({tag:e.tagName,role:e.getAttribute('role'),class:e.className,composer:!!e.closest('[data-composer-body]'),visible:visible(e),writable:!e.disabled&&!e.readOnly,tabIndex:e.tabIndex,len:(e.value??e.textContent??'').length,prefix:(e.value??e.textContent??'').slice(0,100),suffix:(e.value??e.textContent??'').slice(-100)}))};})()'''

if __name__ == '__main__':
    p = Page()
    print(json.dumps(p.js(INSPECT), ensure_ascii=False, indent=2))
    p.close()
