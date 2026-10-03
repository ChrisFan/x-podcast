"""Export/upload Night Harbor using Xcode's existing personal-team signing account.

The individual API key is reserved for App Store Connect management: this
Xcode's altool rejects individual-key validation without an issuer ID.
"""
import argparse
import json
from pathlib import Path
import plistlib
import subprocess

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('action',choices=['export','upload'])
p.add_argument('--archive',type=Path,default=ROOT/'ios/build/release/NightHarbor-0.1.0-1.xcarchive')
a=p.parse_args()
c=json.loads((Path.home()/'.config/aipodcast/appstoreconnect/config.json').read_text())
assert c['teamId']=='DXH9X9Y868' and c['appAppleId']=='6818797321' and c['bundleId']=='com.pawlpixel.NightHarbor'
app=a.archive/'Products/Applications/NightHarbor.app'
info=plistlib.loads((app/'Info.plist').read_bytes())
assert info['CFBundleIdentifier']==c['bundleId']
profile=plistlib.loads(subprocess.run(['security','cms','-D','-i',str(app/'embedded.mobileprovision')],capture_output=True,check=True).stdout)
assert profile['TeamIdentifier']==[c['teamId']]
if a.action=='upload':
    response=json.loads(subprocess.run(['node',str(ROOT/'ios/release/asc.mjs'),'/v1/apps/6818797321?fields%5Bapps%5D=bundleId'],capture_output=True,text=True,check=True).stdout)
    assert response['body']['data']['attributes']['bundleId']==c['bundleId']
options=ROOT/'ios/release'/('UploadOptions.plist' if a.action=='upload' else 'ExportOptions.plist')
cmd=['xcodebuild','-exportArchive','-archivePath',str(a.archive),'-exportOptionsPlist',str(options),'-exportPath',str(ROOT/'ios/build/release'/a.action),'-allowProvisioningUpdates']
print(f"{a.action}: Night Harbor {info['CFBundleShortVersionString']} ({info['CFBundleVersion']})",flush=True)
raise SystemExit(subprocess.run(cmd).returncode)
