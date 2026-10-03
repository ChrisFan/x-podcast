#!/usr/bin/env python3
"""Run simulator acceptance with credentials injected into an ephemeral xctestrun.
The build/results directory is private and gitignored. No secrets are printed.
"""
import argparse, json, plistlib, subprocess, os, shutil
from datetime import datetime
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--credentials-file',required=True,type=Path)
p.add_argument('--email',default='mvp-owner@example.invalid')
p.add_argument('--api',default='https://alu-designer.pawlpixel.com/podcast/api')
p.add_argument('--ready-title')
p.add_argument('--layout-only',action='store_true',help='Only check mini player and tab navigation')
p.add_argument('--device',default='4342D402-D677-4AC2-9BDA-062E8FB33957')
a=p.parse_args(); root=Path(__file__).resolve().parent
credentials=json.loads(a.credentials_file.read_text())
env={'NIGHT_HARBOR_TEST_EMAIL':a.email,'NIGHT_HARBOR_TEST_PASSWORD':credentials['acceptance_password'],'NIGHT_HARBOR_TEST_API':a.api}
if a.ready_title: env['NIGHT_HARBOR_TEST_READY_TITLE']=a.ready_title
original=next(p for p in (root/'build/Build/Products').glob('*.xctestrun') if not p.name.startswith('LiveAcceptance'))
config=plistlib.loads(original.read_bytes())
def inject(value):
    if isinstance(value,dict):
        if 'TestBundlePath' in value and 'NightHarborUITests' in value['TestBundlePath']: value.setdefault('EnvironmentVariables',{}).update(env)
        for child in value.values(): inject(child)
    elif isinstance(value,list):
        for child in value: inject(child)
inject(config)
private=original.parent/f'LiveAcceptance-{os.getpid()}.xctestrun'
private.write_bytes(plistlib.dumps(config)); os.chmod(private,0o600)
try:
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    log=root/f'build/live-acceptance-{stamp}.log'
    with log.open('w') as out:
        result=subprocess.run(['xcodebuild','test-without-building','-collect-test-diagnostics','never','-xctestrun',str(private),'-destination',f'platform=iOS Simulator,id={a.device}','-only-testing:NightHarborUITests/NightHarborUITests/'+('testLiveMiniPlayerNavigation' if a.layout_only else 'testLiveAccountDraftAndPlayback'),'-resultBundlePath',str(root/f'build/LiveAcceptance-{stamp}.xcresult')],stdout=out,stderr=subprocess.STDOUT)
    if result.returncode == 0:
        exported=root/f'build/attachments-{stamp}'
        subprocess.run(['xcrun','xcresulttool','export','attachments','--path',str(root/f'build/LiveAcceptance-{stamp}.xcresult'),'--output-path',str(exported)],check=True,stdout=subprocess.DEVNULL)
        evidence=root/'evidence'; evidence.mkdir(exist_ok=True)
        names=['Tonight','Editor','Library','Live draft lifecycle','Live player','Offline cached player','Logout hides cached library','End of track stopped','Mini player above tabs']
        for test in json.loads((exported/'manifest.json').read_text()):
            for attachment in test.get('attachments',[]):
                label=attachment.get('suggestedHumanReadableName','')
                for name in names:
                    source=exported/attachment['exportedFileName']
                    if label.startswith(name) and source.suffix.lower()=='.png': shutil.copyfile(source,evidence/(name.lower().replace(' ','-')+('-'+a.device if a.layout_only else '')+'.png'))
        if a.layout_only:
            (evidence/('mini-player-layout-'+a.device+'.json')).write_text(json.dumps({'passed':True,'device':a.device,'result_bundle':str(root/f'build/LiveAcceptance-{stamp}.xcresult'),'checks':['start tonight and collapse full player','mini player stays above all three tab buttons','all tabs are hittable and switch selection','mini player reopens full player'],'boundaries':['Simulator verification only; not yet released to TestFlight']},ensure_ascii=False,indent=2)+'\n')
        else:
            (evidence/'native-acceptance.json').write_text(json.dumps({'passed':True,'device':a.device,'api':a.api,'ready_title':a.ready_title,'result_bundle':str(root/f'build/LiveAcceptance-{stamp}.xcresult'),'checks':['real login with Keychain','create and delete cloud draft'] + (['cloud audio download','seek and background playback with advancing clock','20 second episode naturally finishes and stops','end of track timer selection','cached playback with network denied and advancing clock','logout hides account cache'] if a.ready_title else []),'boundaries':['Lockscreen remote controls and physical device not tested','15/30/45/60 minute timer expiry and fade not waited through']},ensure_ascii=False,indent=2)+'\n')
    print(f'Live UI acceptance exit={result.returncode}; private log: {log}')
    raise SystemExit(result.returncode)
finally:
    private.unlink(missing_ok=True)
