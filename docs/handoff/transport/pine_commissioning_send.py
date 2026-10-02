from pine_commissioning_io import Page, INSPECT, THREAD
import json
import pathlib
import sys
import re
import os

p = Page()
if len(sys.argv) == 1:
    print(json.dumps(p.js('''(() => ({roles:Array.from(document.querySelectorAll('[data-message-author-role]')).slice(-4).map(e=>({role:e.getAttribute('data-message-author-role'),id:e.getAttribute('data-message-id'),len:e.innerText.length})),buttons:Array.from(document.querySelectorAll('[data-composer-body] button')).map(e=>({label:e.getAttribute('aria-label'),disabled:e.disabled}))}))()'''), indent=2))
    p.close()
    sys.exit(0)

read_only = '--read' in sys.argv[1:]
args = [a for a in sys.argv[1:] if a != '--read']
assert len(args) == 1, 'One exact request file required'
request_file = pathlib.Path(args[0]).resolve()
body = request_file.read_text(encoding='utf-8').strip()
match = re.search(r'^REQUEST_NONCE=([A-Za-z0-9_-]+)$', body, re.M)
assert match, 'Explicit REQUEST_NONCE required in exact request body'
nonce = match.group(1)
state_dir = pathlib.Path(os.environ.get('PINE_CONTROLLER_STATE_DIR', str(pathlib.Path.home() / '.hermes' / 'state' / 'pine-controller')))
state_dir.mkdir(parents=True, exist_ok=True)
lock = state_dir / 'send.lock'
if lock.exists():
    held = json.loads(lock.read_text(encoding='utf-8'))
    assert held['nonce'] == nonce and held['body'] == str(request_file) and held['thread'] == THREAD, 'Another request outstanding: READ it, never send again'
else:
    assert not read_only, 'Read-only recovery requires existing outstanding request lock'
    with lock.open('x', encoding='utf-8') as f:
        f.write(json.dumps({'nonce': nonce, 'body': str(request_file), 'thread': THREAD}))

p.js('''window.__pineEditor=()=>{
const es=Array.from(document.querySelectorAll('[data-composer-body] [contenteditable=true], form textarea')).filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return e.isConnected&&r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&r.bottom>0&&r.top<innerHeight&&!e.disabled&&!e.readOnly&&e.tabIndex>=0&&!e.closest('.writing-block-editor');});
if(es.length!==1)throw Error('Active composer not unique: '+es.length);return es[0];}; true''')
anchor_expr = '''(() => {const b=BODY,n=t=>t.replace(/\s/g,'');const ms=Array.from(document.querySelectorAll('[data-chatgpt-search-unit-key]'));const a=ms.find(e=>(e.getAttribute('data-chatgpt-search-unit-key')||'').endsWith(':user')&&n(e.innerText||e.textContent||'').includes(n(b)));return a?{id:a.getAttribute('data-chatgpt-search-message-ids'),cleared:(window.__pineEditor().value??window.__pineEditor().textContent??'').length===0}:null;})()'''.replace('BODY',json.dumps(body))
existing = p.js(anchor_expr)
if not existing:
    assert not read_only, 'Exact outbound anchor not rendered; preserved lock, NO resend in read-only mode'
    pre = p.js('''(() => {const e=window.__pineEditor(); return {len:(e.value??e.textContent??'').length,text:e.value??e.textContent??'',stop:!!document.querySelector('button[aria-label="Stop"],button[data-testid="stop-button"]')};})()''')
    print('COMPOSER_PRE=' + json.dumps(pre), flush=True)
    assert not pre['stop'], 'Existing GPT turn still generating; preserve everything'
    idle = p.js('''Array.from(document.querySelectorAll('[data-composer-body] button')).some(b=>!b.disabled&&/^(Send|Start Voice)$/i.test(b.getAttribute('aria-label')||'')) && !Array.from(document.querySelectorAll('button')).some(b=>/stop/i.test(b.getAttribute('aria-label')||''))''')
    assert idle, 'Positive idle composer state not proven; do not send'
    current = p.js('''window.__pineEditor().value??window.__pineEditor().innerText??'' ''').strip()
    if not current:
        p.js('window.__pineEditor().focus(); true')
        p.call('Input.insertText', text=body)
    else:
        assert ''.join(current.split()) == ''.join(body.split()), 'Operator text present; refuse'
    assert ''.join(p.js('''window.__pineEditor().value??window.__pineEditor().innerText??'' ''').split()) == ''.join(body.split()), 'Insertion not exact'
    clicked = p.js('''(() => {const e=window.__pineEditor();const f=e.closest('form');const bs=Array.from(f.querySelectorAll('button')).filter(b=>/send/i.test(b.getAttribute('aria-label')||'')||b.getAttribute('data-testid')==='send-button'||b.id==='composer-submit-button');if(bs.length!==1||bs[0].disabled)throw Error('Unique enabled send button absent');bs[0].click();return true;})()''')
    print('SEND_CLICK=' + str(clicked), flush=True)

delivery = p.js('''new Promise(resolve=>{let o,t;function check(){const a=ANCHOR;if(a&&a.id&&a.cleared){if(o)o.disconnect();clearTimeout(t);resolve(a);}}o=new MutationObserver(check);o.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true});t=setTimeout(()=>{o.disconnect();resolve(null);},30000);check();})'''.replace('ANCHOR',anchor_expr))
assert delivery and delivery.get('id') and delivery.get('cleared'), 'Outbound delivery NOT_PROVEN: lock held, never blind resend'
held=json.loads(lock.read_text(encoding='utf-8'))
held['anchor_id']=delivery['id']
lock.write_text(json.dumps(held),encoding='utf-8')
print('REQUEST_SENT_CONFIRMED=YES REQUEST_NONCE='+nonce+' ANCHOR_MESSAGE_ID='+delivery['id'],flush=True)

# Adopt the existing push-wait pattern: one held CDP websocket, DOM MutationObserver,
# catch-up first, exact outbound anchor, completed new assistant message only. No API polling.
waitjs = '''new Promise(resolve=>{
const body=BODY;
let timer, observer;
function finish(x){if(observer)observer.disconnect();clearTimeout(timer);resolve(x);}
function check(){
 const msgs=Array.from(document.querySelectorAll('[data-chatgpt-search-unit-key]'));
 const role=e=>(e.getAttribute('data-chatgpt-search-unit-key')||'').split(':').pop();
 const norm=t=>t.replace(/\s/g,'');
 const anchor=msgs.findIndex(e=>role(e)==='user'&&norm(e.innerText||e.textContent||'').includes(norm(body)));
 if(anchor<0)return;
 const e=window.__pineEditor(); const cleared=(e.value??e.textContent??'').length===0;
 const replies=msgs.slice(anchor+1).filter(e=>role(e)==='assistant'&&(e.innerText||'').trim());
 const stop=Array.from(document.querySelectorAll('button')).some(b=>/stop/i.test(b.getAttribute('aria-label')||''));
 const idle=Array.from(document.querySelectorAll('[data-composer-body] button')).some(b=>!b.disabled&&/^(Send|Start Voice)$/i.test(b.getAttribute('aria-label')||''));
 if(cleared&&replies.length&&!stop&&idle)finish({send_confirmed:true,turn_complete:true,anchor_id:msgs[anchor].getAttribute('data-chatgpt-search-message-ids'),reply:replies.map(e=>({id:e.getAttribute('data-chatgpt-search-message-ids'),text:e.innerText})),thread:location.href});
}
observer=new MutationObserver(check);observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true});timer=setTimeout(()=>finish({pending:true,reason:'PUSH_WAIT_EXPIRED'}),300000);check();
})'''.replace('BODY', json.dumps(body))
result = p.js(waitjs)
out = request_file.with_suffix('.reply.json')
out.write_text(json.dumps(result, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
if result.get('send_confirmed') and result.get('reply'):
    lock.unlink()
else:
    print('LOCK_HELD=YES; reply not proven; re-arm --read SAME_REQUEST_FILE', flush=True)
p.close()
