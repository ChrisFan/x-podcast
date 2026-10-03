"""No database/provider required. Untrusted input never reaches SQL or echoes secrets."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from server.app import app

class InputValidation(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app,raise_server_exceptions=False)
        self.script=json.loads(Path('scripts/rainy-inn.json').read_text())
    def post(self,path,body):
        return self.client.post('/podcast/api'+path,json=body)
    def test_unicode_invite_is_forbidden_not_internal_error(self):
        with patch.dict('os.environ',{'PODCAST_INVITE_CODE':'operator-secret-invite'}):
            r=self.post('/auth/register',{'email':'validation@example.com','password':'do-not-echo-password','invite_code':'测试邀请码'})
        self.assertEqual(r.status_code,403)
        for secret in ('operator-secret-invite','do-not-echo-password','测试邀请码'):
            self.assertNotIn(secret,r.text)
    def test_nul_script_fields_rejected_before_database(self):
        for field in ('title','instructions'):
            with self.subTest(field=field):
                script={**self.script,field:'private-secret\x00bad'}
                r=self.post('/scripts/validate',{'script':script})
                self.assertEqual(r.status_code,422)
                self.assertNotIn('private-secret',r.text)
        self.script['segments'][0]['text']='private-secret\x00bad'
        self.assertEqual(self.post('/scripts/validate',{'script':self.script}).status_code,422)
    def test_nul_account_fields_rejected_before_database(self):
        for field in ('email','password','display_name','invite_code'):
            with self.subTest(field=field):
                body={'email':'validation@example.com','password':'do-not-echo-password',field:'private-secret\x00bad'}
                r=self.post('/auth/register',body)
                self.assertEqual(r.status_code,422)
                self.assertNotIn('private-secret',r.text)
                self.assertNotIn('do-not-echo-password',r.text)
    def test_unpaired_surrogate_rejected(self):
        body={'email':'validation@example.com','password':'private-secret-\ud800'}
        r=self.client.post('/podcast/api/auth/login',content=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        self.assertEqual(r.status_code,422)
        self.assertNotIn('private-secret',r.text)
    def test_normal_chinese_script_still_valid(self):
        r=self.post('/scripts/validate',{'script':self.script})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['script']['title'],self.script['title'])
if __name__=='__main__':unittest.main()
