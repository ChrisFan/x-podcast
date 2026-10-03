"""Night Harbor API. Run exactly one uvicorn process; one bounded TTS worker."""
from __future__ import annotations
import hashlib,hmac,json,os,re,secrets,threading,time,uuid
from contextlib import asynccontextmanager
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI,Depends,Header,HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool
import podcast
from .models import *
ROOT=Path(__file__).resolve().parents[1]
podcast.load_env(ROOT/'.env')
DATA=Path(os.environ.get('PODCAST_DATA_DIR',str(ROOT/'output'/'service'))).resolve()
BASE=os.environ.get('PODCAST_PUBLIC_BASE_URL','http://127.0.0.1:3211/podcast/api').rstrip('/')
PREFIX='/podcast/api'
pool=None
stop=threading.Event()
ACTIVE=('queued','generating','mixing')

def db(): return pool.connection()
def event(c,pid,status,stage): c.execute('INSERT INTO events(podcast_id,status,stage) VALUES(%s,%s,%s)',(pid,status,stage))
def password_hash(value,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(value.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()
def user(row): return {k:str(row[k]) for k in ('id','email','display_name')}
def fail(code,message): raise HTTPException(code,message)
def auth(authorization:Annotated[str|None,Header()]=None):
    if not authorization or not authorization.startswith('Bearer '): fail(401,'请先登录')
    with db() as c:
        row=c.execute('SELECT a.*,c.id credential_id,c.kind FROM credentials c JOIN accounts a ON a.id=c.user_id WHERE token_hash=%s AND (expires_at IS NULL OR expires_at>now())',(token_hash(authorization[7:]),)).fetchone()
        if not row: fail(401,'登录已过期或令牌已撤销')
        c.execute('UPDATE credentials SET last_used_at=now() WHERE id=%s',(row['credential_id'],))
    return row
Auth=Annotated[dict,Depends(auth)]
def session_only(a):
    if a['kind']!='session': fail(403,'请在 App 或网页中管理账户令牌')
def owned(c,pid,uid,lock=False):
    row=c.execute('SELECT * FROM podcasts WHERE id=%s AND user_id=%s AND deleted_at IS NULL'+(' FOR UPDATE' if lock else ''),(pid,uid)).fetchone()
    if not row: fail(404,'播客不存在')
    return row
def serialize(row):
    result={k:row[k] for k in ('id','scene','status','progress','stage','error','duration_seconds','created_at','updated_at','script','playback_position_seconds','completed')}
    result.update(title=row['script']['title'],voice=row['script']['voice'])
    if row['status']=='ready':
        result.update(audio_url=f'{BASE}/podcasts/{row["id"]}/audio',download_url=f'{BASE}/podcasts/{row["id"]}/audio',narration_url=f'{BASE}/podcasts/{row["id"]}/audio?variant=narration')
    return result

def issue(c,uid,kind,name):
    token='nh_'+secrets.token_urlsafe(36); tid=uuid.uuid4()
    expiry=datetime.now(timezone.utc)+timedelta(days=30) if kind=='session' else None
    c.execute('INSERT INTO credentials(id,user_id,token_hash,kind,name,expires_at) VALUES(%s,%s,%s,%s,%s,%s)',(tid,uid,token_hash(token),kind,name,expiry))
    return tid,token

@asynccontextmanager
async def lifespan(app):
    global pool
    if not os.environ.get('DATABASE_URL'): raise RuntimeError('DATABASE_URL is required; run server/schema.sql as migration owner first')
    DATA.mkdir(parents=True,exist_ok=True)
    pool=ConnectionPool(os.environ['DATABASE_URL'],min_size=1,max_size=3,kwargs={'row_factory':dict_row},open=True)
    pool.wait()
    # Unknown paid request outcome must never be replayed automatically after a crash.
    with db() as c:
        rows=c.execute("UPDATE podcasts SET status='failed',stage='制作中断，可手动重试',error='服务重启导致制作中断；重试会复用已保存段落，未保存段落可能重新计费',updated_at=now() WHERE status IN ('generating','mixing') AND deleted_at IS NULL RETURNING id").fetchall()
        c.execute("UPDATE jobs SET status='failed',updated_at=now() WHERE status IN ('generating','mixing')")
        for r in rows: event(c,r['id'],'failed','制作中断，可手动重试')
    stop.clear(); worker=threading.Thread(target=worker_loop,daemon=True,name='tts-worker'); worker.start()
    yield
    stop.set(); worker.join(timeout=1)
    # Do not close pool under a still-finishing network call; process shutdown owns cleanup.
    if not worker.is_alive(): pool.close()

app=FastAPI(title='夜航 Night Harbor',lifespan=lifespan,docs_url=PREFIX+'/docs',openapi_url=PREFIX+'/openapi.json')
@app.middleware('http')
async def request_limit(request,call_next):
    if request.method in ('POST','PUT','PATCH'):
        try: length=int(request.headers.get('content-length','0'))
        except ValueError: return JSONResponse({'detail':'请求长度无效'},400)
        if length>131072: return JSONResponse({'detail':'请求最多 128 KiB'},413)
        size=0; chunks=[]
        async for chunk in request.stream():
            size+=len(chunk)
            if size>131072: return JSONResponse({'detail':'请求最多 128 KiB'},413)
            chunks.append(chunk)
        request._body=b''.join(chunks)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    if request.url.path.startswith(PREFIX): response.headers['Cache-Control']='no-store'
    return response
@app.exception_handler(RequestValidationError)
async def validation_error(request,error):
    # Do not echo user input (especially passwords/tokens).
    hints=['.'.join(str(x) for x in e['loc'][1:])+': '+e['msg'] for e in error.errors()[:5]]
    return JSONResponse({'detail':'；'.join(hints)},422)
@app.get(PREFIX+'/health')
def health():
    with db() as c: c.execute('SELECT 1')
    return {'ok':True,'worker_alive':any(t.name=='tts-worker' and t.is_alive() for t in threading.enumerate())}
# Process-local bounds suffice with a single worker/process; never retain credentials.
auth_attempts={}; auth_lock=threading.Lock()
def rate_limit(request):
    key=request.client.host if request.client else 'local'; now=time.monotonic()
    with auth_lock:
        times=[t for t in auth_attempts.get(key,[]) if now-t<300]
        if len(times)>=30: fail(429,'尝试过于频繁，请五分钟后再试')
        if len(auth_attempts)>10000: auth_attempts.clear()
        auth_attempts[key]=times+[now]
@app.post(PREFIX+'/auth/register')
def register(body:Register,request:Request):
    rate_limit(request)
    invite=os.environ.get('PODCAST_INVITE_CODE','')
    if invite and not hmac.compare_digest(body.invite_code.encode('utf-8'),invite.encode('utf-8')): fail(403,'邀请码不正确')
    email=body.email.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): fail(422,'请输入有效邮箱')
    uid=uuid.uuid4()
    with db() as c:
        row=c.execute('INSERT INTO accounts(id,email,display_name,password_hash) VALUES(%s,%s,%s,%s) ON CONFLICT(email) DO NOTHING RETURNING *',(uid,email,body.display_name.strip(),password_hash(body.password))).fetchone()
        if not row: fail(409,'该邮箱已注册')
        _,token=issue(c,uid,'session','登录会话')
    return {'token':token,'user':user(row)}
@app.post(PREFIX+'/auth/login')
def login(body:Login,request:Request):
    rate_limit(request)
    with db() as c:
        row=c.execute('SELECT * FROM accounts WHERE email=%s',(body.email.strip().lower(),)).fetchone()
        stored=row['password_hash'] if row else '00'*16+':'+'00'*64
        if not hmac.compare_digest(password_hash(body.password,stored.split(':')[0]),stored): fail(401,'邮箱或密码不正确')
        _,token=issue(c,row['id'],'session','登录会话')
    return {'token':token,'user':user(row)}
@app.get(PREFIX+'/auth/me')
def me(a:Auth): return user(a)
@app.post(PREFIX+'/auth/logout')
def logout(a:Auth):
    with db() as c: c.execute('DELETE FROM credentials WHERE id=%s',(a['credential_id'],))
    return {'ok':True}
@app.get(PREFIX+'/catalog')
def catalog():
    return {'voices':[{'id':'Serena','name':'Serena · 温柔女声','description':'柔和自然的普通话女声'},{'id':'Ethan','name':'Ethan · 温暖男声','description':'沉稳自然的普通话男声'}], 'scenes':[{'id':'rainy-inn','name':'雨夜旅馆','description':'窗边、暖灯与细雨。环境声为本地合成雨声，非实地录音。'}], 'script_schema':Script.model_json_schema(),'preferences_schema':Preferences.model_json_schema(),'defaults':Preferences().model_dump(),'sample_script':json.loads((ROOT/'scripts/rainy-inn.json').read_text())}
class Validate(Strict): script:Script
@app.post(PREFIX+'/scripts/validate')
def validate_script(body:Validate):
    return {'valid':True,'script':body.script.model_dump(),'characters':sum(len(s.text) for s in body.script.segments),'segments':len(body.script.segments)}
@app.get(PREFIX+'/preferences')
def preferences(a:Auth):
    with db() as c: row=c.execute('SELECT value FROM preferences WHERE user_id=%s',(a['id'],)).fetchone()
    return row['value'] if row else Preferences().model_dump()
@app.put(PREFIX+'/preferences')
def set_preferences(body:Preferences,a:Auth):
    value=body.model_dump()
    with db() as c: c.execute('INSERT INTO preferences(user_id,value) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET value=excluded.value',(a['id'],Jsonb(value)))
    return value
@app.get(PREFIX+'/tokens')
def tokens(a:Auth):
    session_only(a)
    with db() as c: rows=c.execute("SELECT id,name,created_at,last_used_at FROM credentials WHERE user_id=%s AND kind='api' ORDER BY created_at DESC",(a['id'],)).fetchall()
    return {'items':rows}
@app.post(PREFIX+'/tokens')
def create_token(body:TokenCreate,a:Auth):
    session_only(a)
    with db() as c:
        c.execute('SELECT id FROM accounts WHERE id=%s FOR UPDATE',(a['id'],))
        if c.execute("SELECT count(*) n FROM credentials WHERE user_id=%s AND kind='api'",(a['id'],)).fetchone()['n']>=20: fail(409,'最多保留 20 个连接令牌')
        tid,token=issue(c,a['id'],'api',body.name)
    return {'id':tid,'token':token}
@app.delete(PREFIX+'/tokens/{tid}')
def delete_token(tid:uuid.UUID,a:Auth):
    session_only(a)
    with db() as c: c.execute("DELETE FROM credentials WHERE id=%s AND user_id=%s AND kind='api'",(tid,a['id']))
    return {'ok':True}
@app.get(PREFIX+'/podcasts')
def listing(a:Auth):
    with db() as c: rows=c.execute('SELECT * FROM podcasts WHERE user_id=%s AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 200',(a['id'],)).fetchall()
    return {'items':[serialize(r) for r in rows]}
@app.post(PREFIX+'/podcasts')
def create(body:Create,a:Auth):
    pid=uuid.uuid4()
    with db() as c:
        c.execute('SELECT id FROM accounts WHERE id=%s FOR UPDATE',(a['id'],))
        if c.execute('SELECT count(*) n FROM podcasts WHERE user_id=%s AND deleted_at IS NULL',(a['id'],)).fetchone()['n']>=200: fail(409,'MVP 最多保留 200 份播客，请先删除旧作品')
        row=c.execute('INSERT INTO podcasts(id,user_id,script,scene) VALUES(%s,%s,%s,%s) RETURNING *',(pid,a['id'],Jsonb(body.script.model_dump()),body.scene)).fetchone(); event(c,pid,'draft','草稿已保存')
    return serialize(row)
@app.get(PREFIX+'/podcasts/{pid}')
def get(pid:uuid.UUID,a:Auth):
    with db() as c: return serialize(owned(c,pid,a['id']))
@app.patch(PREFIX+'/podcasts/{pid}')
def patch(pid:uuid.UUID,body:Patch,a:Auth):
    with db() as c:
        row=owned(c,pid,a['id'],True)
        if row['status'] not in ('draft','failed','cancelled'): fail(409,'只有草稿、失败或取消的作品可修改')
        row=c.execute("UPDATE podcasts SET script=%s,scene=%s,status='draft',stage='草稿已保存',progress=0,error=NULL,updated_at=now() WHERE id=%s RETURNING *",(Jsonb(body.script.model_dump() if body.script else row['script']),body.scene or row['scene'],pid)).fetchone(); event(c,pid,'draft','草稿已保存')
    return serialize(row)
def enqueue(pid,body,a,retry=False):
    with db() as c:
        row=owned(c,pid,a['id'],True)
        c.execute('SELECT id FROM accounts WHERE id=%s FOR UPDATE',(a['id'],))
        old=c.execute('SELECT * FROM jobs WHERE user_id=%s AND request_id=%s',(a['id'],body.request_id)).fetchone()
        if old:
            if old['podcast_id']!=pid: fail(409,'request_id 已被另一个作品使用')
            return serialize(row)
        if row['status'] in ACTIVE: return serialize(row)
        if row['status'] not in (('failed','cancelled') if retry else ('draft',)): fail(409,'当前状态不可开始制作，请使用重试或新建草稿')
        # Serialize account-level quota checks across multiple podcasts.
        c.execute('SELECT id FROM accounts WHERE id=%s FOR UPDATE',(a['id'],))
        if c.execute("SELECT count(*) n FROM jobs WHERE user_id=%s AND status IN ('queued','generating','mixing')",(a['id'],)).fetchone()['n']>=3: fail(429,'同时最多排队三份作品')
        c.execute('INSERT INTO jobs(id,podcast_id,user_id,request_id) VALUES(%s,%s,%s,%s)',(uuid.uuid4(),pid,a['id'],body.request_id))
        row=c.execute("UPDATE podcasts SET status='queued',progress=0,stage='等待制作',error=NULL,updated_at=now() WHERE id=%s RETURNING *",(pid,)).fetchone(); event(c,pid,'queued','等待制作')
    return serialize(row)
@app.post(PREFIX+'/podcasts/{pid}/generate')
def generate(pid:uuid.UUID,body:Generate,a:Auth): return enqueue(pid,body,a)
@app.post(PREFIX+'/podcasts/{pid}/retry')
def retry(pid:uuid.UUID,body:Generate,a:Auth): return enqueue(pid,body,a,True)
@app.post(PREFIX+'/podcasts/{pid}/cancel')
def cancel(pid:uuid.UUID,a:Auth):
    with db() as c:
        row=owned(c,pid,a['id'],True)
        if row['status'] in ACTIVE:
            row=c.execute("UPDATE podcasts SET status='cancelled',stage='已取消',updated_at=now() WHERE id=%s RETURNING *",(pid,)).fetchone()
            c.execute("UPDATE jobs SET status='cancelled',updated_at=now() WHERE podcast_id=%s AND status IN ('queued','generating','mixing')",(pid,)); event(c,pid,'cancelled','已取消；正在执行的供应商请求可能仍会计费')
    return serialize(row)
@app.delete(PREFIX+'/podcasts/{pid}')
def delete(pid:uuid.UUID,a:Auth):
    with db() as c:
        owned(c,pid,a['id'],True)
        c.execute("UPDATE podcasts SET deleted_at=now(),status='cancelled',updated_at=now() WHERE id=%s",(pid,)); c.execute("UPDATE jobs SET status='cancelled',updated_at=now() WHERE podcast_id=%s AND status IN ('queued','generating','mixing')",(pid,))
    return {'ok':True}
@app.post(PREFIX+'/podcasts/{pid}/progress')
def progress(pid:uuid.UUID,body:Playback,a:Auth):
    with db() as c:
        row=owned(c,pid,a['id'],True)
        position=min(body.position_seconds,row['duration_seconds'] or body.position_seconds)
        c.execute('UPDATE podcasts SET playback_position_seconds=%s,completed=%s WHERE id=%s',(position,body.completed,pid))
    return {'ok':True}
@app.get(PREFIX+'/podcasts/{pid}/events')
def events(pid:uuid.UUID,a:Auth):
    with db() as c:
        owned(c,pid,a['id']); rows=c.execute('SELECT status,stage,created_at FROM events WHERE podcast_id=%s ORDER BY id',(pid,)).fetchall()
    return {'items':rows}
@app.get(PREFIX+'/podcasts/{pid}/audio')
def audio(pid:uuid.UUID,a:Auth,variant:Literal['mix','narration']='mix'):
    with db() as c: row=owned(c,pid,a['id'])
    if row['status']!='ready': fail(409,'音频尚未制作完成')
    folder=Path(row['output_dir']); name='podcast' if variant=='mix' else 'narration'
    path=folder/(name+'.mp3')
    if not path.exists(): path=folder/(name+'.wav')
    if not path.is_file(): fail(404,'音频文件不存在，请联系管理员')
    return FileResponse(path,media_type='audio/mpeg' if path.suffix=='.mp3' else 'audio/wav',filename=row['script']['title']+path.suffix,content_disposition_type='inline')

# Worker checks current job identity before every transition; old runs cannot revive retries.
def transition(job,status,stage,progress=None,**values):
    with db() as c:
        row=c.execute('SELECT * FROM podcasts WHERE id=%s FOR UPDATE',(job['podcast_id'],)).fetchone()
        current=c.execute('SELECT status FROM jobs WHERE id=%s',(job['id'],)).fetchone()
        if not row or row['deleted_at'] or row['status'] not in ACTIVE or not current or current['status'] not in ACTIVE: return False
        fields={'status':status,'stage':stage,**values}
        if progress is not None: fields['progress']=progress
        sets=','.join(k+'=%s' for k in fields)
        c.execute('UPDATE podcasts SET '+sets+',updated_at=now() WHERE id=%s',(*fields.values(),job['podcast_id']))
        c.execute('UPDATE jobs SET status=%s,updated_at=now() WHERE id=%s',(status,job['id'])); event(c,job['podcast_id'],status,stage)
    return True

def worker_loop():
    # Keep the same job until a failed-state write can be acknowledged. A DB
    # outage must never trigger another paid provider call or leave it active
    # indefinitely after the connection returns.
    pending_failure=None
    while not stop.wait(.7):
        job=None
        try:
            if pending_failure is not None:
                transition(pending_failure,'failed','制作中断，可手动重试',
                           error='数据库连接中断；已保存的段落会在手动重试时复用')
                # False means cancelled/deleted/otherwise terminal: discard it
                # without changing the newer lifecycle state.
                pending_failure=None
                continue
            with db() as c:
                job=c.execute("SELECT j.* FROM jobs j JOIN podcasts p ON p.id=j.podcast_id WHERE j.status='queued' AND p.status='queued' AND p.deleted_at IS NULL ORDER BY j.created_at LIMIT 1").fetchone()
            if not job: continue
            run_job(job)
        except Exception:
            if pending_failure is None and job is not None:
                pending_failure=job
            # No raw provider/DB exceptions: those can contain script or connection secrets.
            import logging
            logging.getLogger('night_harbor').error('Worker database operation failed; waiting to settle the current job safely')

def run_job(job):
    try:
        if not transition(job,'generating','准备声音',1): return
        with db() as c: row=c.execute('SELECT script FROM podcasts WHERE id=%s',(job['podcast_id'],)).fetchone()
        script=row['script']; region=os.environ.get('DASHSCOPE_REGION','beijing')
        if region not in podcast.ENDPOINTS: raise podcast.PodcastError('TTS 地域配置无效')
        cache=DATA/str(job['user_id'])/'cache'; cache.mkdir(parents=True,exist_ok=True)
        clips=[]
        for i,segment in enumerate(script['segments']):
            if stop.is_set(): raise podcast.PodcastError('服务正在重启，请稍后重试')
            if not transition(job,'generating',f'正在录制第 {i+1}/{len(script["segments"])} 段',int(i/len(script['segments'])*85)+1): return
            clips.append(podcast.get_clip(script,segment,region,cache,True))
        if not transition(job,'mixing','正在铺入雨声与留白',88): return
        output=DATA/str(job['user_id'])/str(job['podcast_id'])/str(job['id'])
        report=podcast.render(script,clips,output,False,None)
        import shutil,subprocess
        ffmpeg=os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
        if ffmpeg:
            for name in ('podcast','narration'):
                subprocess.run([ffmpeg,'-nostdin','-loglevel','error','-y','-i',str(output/(name+'.wav')),'-codec:a','libmp3lame','-b:a','64k',str(output/(name+'.mp3'))],check=True,timeout=180,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        transition(job,'ready','今晚的声音准备好了',100,duration_seconds=report['duration_seconds'],output_dir=str(output),error=None)
    except Exception as error:
        message=str(error) if isinstance(error,podcast.PodcastError) else '音频制作失败；请稍后重试，已完成的段落会复用'
        transition(job,'failed','制作未完成',error=message[:500])

app.mount('/podcast',StaticFiles(directory=ROOT/'web',html=True),name='studio')
