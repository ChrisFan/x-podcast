"""Real PostgreSQL HTTP lifecycle tests; deterministic audio only inside tests.
Run: .venv/bin/python -m unittest server.test_integration -v
Uses .local/server.env when DATABASE_URL absent; cleans only its unique test users.
Never run concurrently with a production worker on the same database.
"""
import json,os,tempfile,time,unittest,uuid
from pathlib import Path
from unittest.mock import patch
import numpy as np
from fastapi.testclient import TestClient
import podcast
if not os.environ.get('DATABASE_URL'): podcast.load_env(Path('.local/server.env'))
os.environ['PODCAST_DATA_DIR']=tempfile.mkdtemp(prefix='night-harbor-test-')
from server import app as service

def clip(*args,**kwargs):
    sr=24000;t=np.arange(sr//4)/sr
    return (.12*np.sin(2*np.pi*200*t)).astype(np.float32),sr,{'cached':False}

@unittest.skipUnless(os.environ.get('DATABASE_URL'),'Real PostgreSQL DATABASE_URL required')
class Lifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock=patch.object(podcast,'get_clip',clip);cls.mock.start()
        cls.client=TestClient(service.app);cls.client.__enter__();cls.users=[]
        cls.a=cls.signup('a');cls.b=cls.signup('b')
        cls.script=json.loads(Path('scripts/rainy-inn.json').read_text());cls.script['segments']=cls.script['segments'][:1];cls.script['segments'][0]['pause_after_seconds']=0
        cls.script['mix'].update(intro_seconds=0,tail_seconds=1,fade_out_seconds=1)
    @classmethod
    def signup(cls,tag):
        r=cls.client.post('/podcast/api/auth/register',json={'email':f'test-{tag}-{uuid.uuid4()}@example.com','password':'only-test-password','invite_code':os.environ.get('PODCAST_INVITE_CODE','')})
        assert r.status_code==200,r.text
        data=r.json();cls.users.append(data['user']['id']);return {'Authorization':'Bearer '+data['token']}
    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None);cls.mock.stop()
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL']) as c:
            for uid in cls.users:c.execute('DELETE FROM accounts WHERE id=%s',(uid,))
    def call(self,method,path,body=None,headers=None):
        return self.client.request(method,'/podcast/api'+path,json=body,headers=headers or self.a)
    def new(self):
        r=self.call('POST','/podcasts',{'script':self.script,'scene':'rainy-inn'});self.assertEqual(r.status_code,200,r.text);return r.json()['id']
    def wait(self,pid,status):
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            data=self.call('GET','/podcasts/'+pid).json()
            if data['status']==status:return data
            time.sleep(.15)
        self.fail(str(data))
    def test_lifecycle_range_isolation_and_progress(self):
        pid=self.new();path='/podcasts/'+pid;req={'request_id':str(uuid.uuid4())}
        self.assertEqual(self.call('GET',path,headers=self.b).status_code,404)
        self.assertEqual(self.call('POST',path+'/generate',req).status_code,200)
        self.assertEqual(self.call('POST',path+'/generate',req).status_code,200)
        ready=self.wait(pid,'ready');self.assertGreater(ready['duration_seconds'],0)
        with service.db() as c:self.assertEqual(c.execute('SELECT count(*) n FROM jobs WHERE podcast_id=%s',(pid,)).fetchone()['n'],1)
        r=self.client.get('/podcast/api'+path+'/audio',headers={**self.a,'Range':'bytes=0-99'});self.assertEqual(r.status_code,206);self.assertEqual(len(r.content),100)
        self.assertEqual(self.call('GET',path+'/audio',headers=self.b).status_code,404)
        self.assertEqual(self.call('GET',path+'/events',headers=self.b).status_code,404)
        self.assertEqual(self.call('POST',path+'/progress',{'position_seconds':.5,'completed':False}).status_code,200)
        self.assertEqual(self.call('GET',path).json()['playback_position_seconds'],.5)
        self.call('DELETE',path);self.assertEqual(self.call('GET',path+'/audio').status_code,404)
    def test_cancel_and_delete_during_provider(self):
        import threading
        entered=threading.Event();release=threading.Event()
        def slow(*a,**k):entered.set();release.wait(4);return clip()
        with patch.object(podcast,'get_clip',slow):
            pid=self.new();self.call('POST',f'/podcasts/{pid}/generate',{'request_id':str(uuid.uuid4())});self.assertTrue(entered.wait(3))
            self.assertEqual(self.call('POST',f'/podcasts/{pid}/cancel').json()['status'],'cancelled')
            self.call('DELETE',f'/podcasts/{pid}');release.set();time.sleep(.5)
            self.assertEqual(self.call('GET',f'/podcasts/{pid}').status_code,404)
            with service.db() as c:self.assertEqual(c.execute('SELECT status FROM podcasts WHERE id=%s',(pid,)).fetchone()['status'],'cancelled')
    def test_failure_retry_and_edit(self):
        with patch.object(podcast,'get_clip',side_effect=podcast.PodcastError('test provider failure')):
            pid=self.new();self.call('POST',f'/podcasts/{pid}/generate',{'request_id':str(uuid.uuid4())});self.wait(pid,'failed')
        self.call('POST',f'/podcasts/{pid}/retry',{'request_id':str(uuid.uuid4())});self.wait(pid,'ready')
        self.assertEqual(self.call('PATCH',f'/podcasts/{pid}',{'script':self.script}).status_code,409)
    def test_tokens_preferences_and_limits(self):
        t=self.call('POST','/tokens',{'name':'test MCP'}).json();headers={'Authorization':'Bearer '+t['token']}
        self.assertEqual(self.call('GET','/podcasts',headers=headers).status_code,200)
        self.assertEqual(self.call('POST','/tokens',{'name':'forbidden'},headers=headers).status_code,403)
        self.call('DELETE','/tokens/'+t['id']);self.assertEqual(self.call('GET','/podcasts',headers=headers).status_code,401)
        prefs={'voice':'Ethan','scene':'rainy-inn','ambience_dbfs':-42,'sleep_timer_minutes':15}
        self.assertEqual(self.call('PUT','/preferences',prefs).json(),prefs)
        self.assertEqual(self.call('GET','/preferences').json(),prefs)
        bad=json.loads(json.dumps(self.script));bad['voice']='UnapprovedVoice'
        self.assertEqual(self.call('POST','/scripts/validate',{'script':bad}).status_code,422)
        bad['voice']='Serena';bad['segments']=[{**bad['segments'][0],'id':str(i),'text':'字'*600} for i in range(5)]
        self.assertEqual(self.call('POST','/scripts/validate',{'script':bad}).status_code,422)
        r=self.client.post('/podcast/api/scripts/validate',content=b'x'*140000,headers={'Content-Type':'application/json'});self.assertEqual(r.status_code,413)
    def test_db_outage_settles_failed_without_repeating_provider(self):
        self.check_db_outage_settlement(cancel=False)
    def test_db_outage_does_not_revive_cancelled_job(self):
        self.check_db_outage_settlement(cancel=True)
    def check_db_outage_settlement(self,cancel):
        import threading
        from psycopg import OperationalError
        lost=threading.Event();recovered=threading.Event();provider_calls=[]
        real_transition=service.transition
        pid=self.new()
        def provider(*a,**k):
            provider_calls.append(1)
            return clip()
        def disrupted(job,status,*a,**k):
            if str(job['podcast_id'])==pid and (status=='mixing' or lost.is_set()) and not recovered.is_set():
                lost.set()
                raise OperationalError('simulated database outage')
            return real_transition(job,status,*a,**k)
        with patch.object(podcast,'get_clip',provider),patch.object(service,'transition',disrupted):
            self.call('POST',f'/podcasts/{pid}/generate',{'request_id':str(uuid.uuid4())})
            self.assertTrue(lost.wait(5),'worker must reach outage after one provider call')
            if cancel:
                self.assertEqual(self.call('POST',f'/podcasts/{pid}/cancel').json()['status'],'cancelled')
            recovered.set()
            self.wait(pid,'cancelled' if cancel else 'failed')
            # Allow one further queue iteration to expose an accidental replay.
            time.sleep(1)
            self.assertEqual(self.call('GET',f'/podcasts/{pid}').json()['status'],'cancelled' if cancel else 'failed')
            self.assertEqual(len(provider_calls),1,'database recovery must not repeat a paid TTS call')
    def test_owner_mutations_are_isolated(self):
        pid=self.new();path='/podcasts/'+pid
        for method,suffix,body in [('PATCH','',{'script':self.script}),('DELETE','',None),('POST','/cancel',None),('POST','/generate',{'request_id':str(uuid.uuid4())}),('POST','/retry',{'request_id':str(uuid.uuid4())}),('POST','/progress',{'position_seconds':0,'completed':False})]:
            self.assertEqual(self.call(method,path+suffix,body,headers=self.b).status_code,404,(method,suffix))
        self.assertEqual(self.call('GET',path).json()['status'],'draft')
    def test_request_id_cross_podcast_conflict(self):
        a,b=self.new(),self.new();r={'request_id':str(uuid.uuid4())}
        self.call('POST',f'/podcasts/{a}/generate',r)
        self.assertEqual(self.call('POST',f'/podcasts/{b}/generate',r).status_code,409)
if __name__=='__main__':unittest.main()
