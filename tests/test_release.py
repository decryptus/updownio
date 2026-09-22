"""Exercise release selection in disposable git repositories."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path('.github/scripts/release.py').resolve()


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init','-b','main')
        self.git('config','user.email','test@example.org')
        self.git('config','user.name','Test')
        for name in ['VERSION','RELEASE']:(self.root/name).write_text('0.1.0\n')
        self.git('add','.')
        self.git('commit','-m','initial')
        self.sha=self.git('rev-parse','HEAD').strip()
        self.git('update-ref','refs/remotes/origin/main',self.sha)

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,text=True,stderr=subprocess.DEVNULL)

    def select(self,tag='',ref='refs/heads/main',event='push',success=True):
        output=self.root/'output'
        output.write_text('')
        env=dict(os.environ,GITHUB_OUTPUT=str(output),GITHUB_REF=ref,GITHUB_EVENT_NAME=event,RELEASE_TAG=tag)
        proc=subprocess.run([sys.executable,str(SCRIPT)],cwd=self.root,env=env,capture_output=True,text=True)
        if success:self.assertEqual(proc.returncode,0,proc.stderr)
        else:self.assertNotEqual(proc.returncode,0)
        return dict(line.split('=',1) for line in output.read_text().splitlines())

    def test_new_version_and_same_commit_retry(self):
        self.assertEqual(self.select(),{'tag':'v0.1.0','sha':self.sha,'create':'true','publish':'true'})
        self.git('tag','v0.1.0')
        self.assertEqual(self.select()['create'],'false')
        self.assertEqual(self.select()['publish'],'true')

    def test_later_commit_skips_but_manual_retries_original(self):
        self.git('tag','v0.1.0')
        (self.root/'README').write_text('later')
        self.git('add','.');self.git('commit','-m','docs')
        self.assertEqual(self.select()['publish'],'false')
        selected=self.select(tag='v0.1.0',event='workflow_dispatch')
        self.assertEqual(selected['sha'],self.sha)
        self.assertEqual(selected['publish'],'true')

    def test_pushed_tag(self):
        self.git('tag','v0.1.0')
        self.assertEqual(self.select(ref='refs/tags/v0.1.0')['publish'],'true')
        self.select(ref='refs/tags/v0.2.0',success=False)

    def test_invalid_version_and_manual_context(self):
        (self.root/'VERSION').write_text('wrong')
        self.select(success=False)
        self.select(tag='v0.1.0',event='push',success=False)
        self.select(tag='bad',event='workflow_dispatch',success=False)

    def test_unmerged_tag_rejected(self):
        self.git('checkout','-b','unmerged')
        (self.root/'README').write_text('unmerged')
        self.git('add','.');self.git('commit','-m','unmerged');self.git('tag','v0.1.0')
        self.select(ref='refs/tags/v0.1.0',success=False)
        self.git('checkout','main')
        self.select(tag='v0.1.0',event='workflow_dispatch',success=False)
