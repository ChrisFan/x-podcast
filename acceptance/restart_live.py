"""Bounded real-provider interruption and manual recovery acceptance."""
import json
import subprocess
import time
import uuid
from api_live import ROOT, PRIVATE, call

token=(PRIVATE/'acceptance-session').read_text().strip()
main_id=json.loads((PRIVATE/'acceptance-podcast.json').read_text())['id']
before=call('GET','/podcasts/'+main_id,token=token).json()
script=json.loads((ROOT/'scripts/rainy-inn.json').read_text())
script['id']='restart-'+uuid.uuid4().hex[:10]
script['title']='重启恢复验收（自动清理）'
script['segments']=script['segments'][:2]
script['segments'][0]['text']='此刻，屋檐下的雨声轻轻落着。'+script['segments'][0]['text']
script['mix'].update(intro_seconds=1,tail_seconds=4,fade_out_seconds=3)
pid=call('POST','/podcasts',{'script':script,'scene':'rainy-inn'},token).json()['id']
call('POST',f'/podcasts/{pid}/generate',{'request_id':str(uuid.uuid4())},token)
for _ in range(60):
    p=call('GET',f'/podcasts/{pid}',token=token).json()
    if p['status']=='generating': break
    time.sleep(.25)
else: raise RuntimeError('Did not observe generating')
subprocess.run(['ssh','-i',str(ROOT.home()/'.ssh/alu-designer-deploy'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','deploy@120.55.99.193','sudo -n systemctl restart aipodcast.service'],check=True)
for _ in range(30):
    try:
        call('GET','/health'); break
    except Exception: time.sleep(1)
after=call('GET','/podcasts/'+main_id,token=token).json()
assert after['status']==before['status']=='ready'
assert after['script']==before['script']
assert after['playback_position_seconds']==before['playback_position_seconds']
p=call('GET',f'/podcasts/{pid}',token=token).json()
assert p['status']=='failed',p['status']
events=call('GET',f'/podcasts/{pid}/events',token=token).json()['items']
time.sleep(3)
assert call('GET',f'/podcasts/{pid}',token=token).json()['status']=='failed'
assert len(call('GET',f'/podcasts/{pid}/events',token=token).json()['items'])==len(events)
print('PASS interrupted generation becomes failed and stays idle; account, ready audio, script and progress persist',flush=True)
call('POST',f'/podcasts/{pid}/retry',{'request_id':str(uuid.uuid4())},token)
for _ in range(150):
    p=call('GET',f'/podcasts/{pid}',token=token).json()
    if p['status']=='ready': break
    if p['status']=='failed': raise RuntimeError('Explicit recovery failed')
    time.sleep(2)
else: raise RuntimeError('Recovery observation timed out')
call('GET',f'/podcasts/{pid}/audio',token=token,expect=206,headers={'Range':'bytes=0-1023'})
call('DELETE',f'/podcasts/{pid}',token=token)
(ROOT/'acceptance/restart-results.json').write_text(json.dumps({'passed':True,'interrupted_job_failed':True,'no_automatic_requeue':True,'existing_account_script_audio_and_progress_persisted':True,'explicit_retry_ready':True,'duration_seconds':p['duration_seconds'],'test_podcast_deleted':True},indent=2))
print('PASS explicit retry produces real audio; temporary episode removed',flush=True)
