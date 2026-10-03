"""Public HTTPS acceptance. Uses real Aliyun generation; credentials stay in .local."""
import json
import os
from pathlib import Path
import time
import uuid
import httpx

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'.local'
BASE='https://alu-designer.pawlpixel.com/podcast/api'
secrets=json.loads((PRIVATE/'deployment-secrets.json').read_text())
client=httpx.Client(base_url=BASE,timeout=40,trust_env=False)
results=[]


def save_private(name,data):
    fd=os.open(PRIVATE/name,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f: f.write(data)


def call(method,path,body=None,token=None,expect=200,headers=None):
    h=dict(headers or {})
    if token: h['Authorization']='Bearer '+token
    r=client.request(method,path,json=body,headers=h)
    if r.status_code!=expect:
        raise RuntimeError(f'{method} {path} returned {r.status_code}, expected {expect}')
    return r


def check(name):
    results.append(name)
    print('PASS '+name,flush=True)
    (ROOT/'acceptance/api-live-results.json').write_text(json.dumps({'passed':results},ensure_ascii=False,indent=2))


def login_or_register(email):
    body={'email':email,'password':secrets['acceptance_password'],'display_name':'夜航体验者','invite_code':secrets['invite_code']}
    r=client.post('/auth/register',json=body)
    if r.status_code==409:
        r=call('POST','/auth/login',{k:body[k] for k in ('email','password')})
    if r.status_code!=200: raise RuntimeError('Account setup failed: '+str(r.status_code))
    return r.json()['token']


def main():
    call('GET','/health')
    check('HTTPS API and worker health')
    call('GET','/podcasts',expect=401)
    token=login_or_register('mvp-owner@example.invalid')
    other=login_or_register('mvp-isolation@example.invalid')
    save_private('acceptance-session',token)
    check('registration/login and unauthenticated denial')
    catalog=call('GET','/catalog',token=token).json()
    assert catalog['script_schema'] and catalog['voices']
    script=json.loads((ROOT/'scripts/rainy-inn.json').read_text())
    script['title']='雨夜旅馆 · 云端首夜'
    call('POST','/scripts/validate',{'script':script},token=token)
    prefs=call('GET','/preferences',token=token).json()
    prefs['sleep_timer_minutes']=30
    call('PUT','/preferences',prefs,token=token)
    check('schema validation and persisted preferences')
    saved=PRIVATE/'acceptance-podcast.json'
    if saved.exists():
        pid=json.loads(saved.read_text())['id']
        podcast=call('GET','/podcasts/'+pid,token=token).json()
    else:
        podcast=call('POST','/podcasts',{'script':script,'scene':'rainy-inn'},token).json()
        pid=podcast['id']; save_private(saved.name,json.dumps({'id':pid}))
    for method,path,body in [('GET',f'/podcasts/{pid}',None),('GET',f'/podcasts/{pid}/audio',None),
                              ('DELETE',f'/podcasts/{pid}',None),('POST',f'/podcasts/{pid}/cancel',{})]:
        call(method,path,body,other,expect=404)
    check('cross-account detail/audio/delete/cancel rejected')
    key=call('POST','/tokens',{'name':'MCP MVP acceptance'},token).json()
    save_private('mcp-token',key['token'])
    save_private('mcp.env','AIPODCAST_API_URL='+BASE+'\nAIPODCAST_TOKEN='+key['token']+'\n')
    call('GET','/podcasts',token=key['token'])
    revoked=call('POST','/tokens',{'name':'revocation-test'},token).json()
    call('DELETE','/tokens/'+revoked['id'],token=token)
    call('GET','/podcasts',token=revoked['token'],expect=401)
    check('account-scoped MCP token creation and revocation')
    if podcast['status'] in ('draft','failed','cancelled'):
        action='generate' if podcast['status']=='draft' else 'retry'
        request={'request_id':str(uuid.uuid4())}
        first=call('POST',f'/podcasts/{pid}/{action}',request,token).json()
        again=call('POST',f'/podcasts/{pid}/{action}',request,token).json()
        assert first['id']==again['id']
        check('duplicate generation request reuses same podcast')
    deadline=time.monotonic()+900
    last=None
    while time.monotonic()<deadline:
        podcast=call('GET',f'/podcasts/{pid}',token=token).json()
        state=(podcast['status'],podcast['progress'])
        if state!=last:
            print('GENERATION',state,podcast['stage'],flush=True); last=state
        if podcast['status']=='ready': break
        if podcast['status'] in ('failed','cancelled'): raise RuntimeError('Real generation did not complete: '+str(podcast.get('error')))
        time.sleep(3)
    else: raise RuntimeError('Real generation still pending after acceptance observation window')
    assert podcast['duration_seconds']>0
    audio=call('GET',f'/podcasts/{pid}/audio',token=token,expect=206,headers={'Range':'bytes=0-1023'})
    assert len(audio.content)==1024 and 'audio/mpeg' in audio.headers.get('content-type','')
    check('real Aliyun generation, persisted ready state, authenticated MP3 Range')
    call('POST',f'/podcasts/{pid}/progress',{'position_seconds':42,'completed':False},token)
    assert call('GET',f'/podcasts/{pid}',token=token).json()['playback_position_seconds']==42
    events=call('GET',f'/podcasts/{pid}/events',token=token).json()['items']
    states={e['status'] for e in events}
    assert {'draft','queued','generating','mixing','ready'}<=states
    check('playback progress persisted and all lifecycle events recorded')
    output={'passed':results,'podcast_id':pid,'duration_seconds':podcast['duration_seconds'],'title':podcast['title'],'states':sorted(states)}
    (ROOT/'acceptance/api-live-results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
    print('Ready podcast ID:',pid,flush=True)


if __name__=='__main__': main()
