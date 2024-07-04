import os
import shutil

from xbot.framework.utils import assertx

from lib.testcase import TestCase


class tc_sftp(TestCase):
    """
    Testcase using SFTPConnection.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['sftp']

    def setup(self):
        """
        Prepare test environment.
        """
        self.sftp = self.testbed.get_conn('sftp', 'normal')
        self.lhome = os.environ.get('HOME') or os.environ['HOMEPATH']
        self.lputdir = os.path.join(self.lhome, 'lputdir')
        self.lgetdir = os.path.join(self.lhome, 'lgetdir')
        self.rputdir = '/tmp/rputgetdir'
        self.rgetdir = self.rputdir
        for d in (self.lputdir, self.lgetdir):
            if os.path.exists(d):
                shutil.rmtree(d)
        self.sftp.makedirs(self.rputdir)
        os.makedirs(os.path.join(self.lputdir, 'dir', 'subdir'))
        os.system('whoami > %s' % os.path.join(self.lputdir, 'file'))
        os.system('whoami > %s' % os.path.join(self.lputdir, 'dir', 'subfile'))

    def step1(self):
        """
        Test `putdir` method.
        """
        l = os.path.join(self.lputdir, 'dir')
        self.sftp.putdir(l, self.rputdir)
        p1 = self.sftp.join(self.rputdir, 'dir', 'subdir')
        assertx(self.sftp.exists(p1), '==', True)
        p2 = self.sftp.join(self.rputdir, 'dir', 'subfile')
        assertx(self.sftp.exists(p2), '==', True)

    def step2(self):
        """
        Test `putfile` method.
        """
        l = os.path.join(self.lputdir, 'file')
        self.sftp.putfile(l, self.rputdir)
        p1 = self.sftp.join(self.rputdir, 'file')
        assertx(self.sftp.exists(p1), '==', True)
        # rename
        self.sftp.putfile(l, self.rputdir, 'newfile')
        p2 = self.sftp.join(self.rputdir, 'newfile')
        assertx(self.sftp.exists(p2), '==', True)

    def step3(self):
        """
        Test `getdir` method.
        """
        r = self.sftp.join(self.rgetdir, 'dir')
        self.sftp.getdir(r, self.lgetdir)
        p1 = os.path.join(self.lgetdir, 'dir', 'subdir')
        assertx(os.path.exists(p1), '==', True)
        p2 = os.path.join(self.lgetdir, 'dir', 'subfile')
        assertx(os.path.exists(p2), '==', True)
    
    def step4(self):
        """
        Test `getfile` method.
        """
        r = self.sftp.join(self.rgetdir, 'file')
        self.sftp.getfile(r, self.lgetdir)
        p1 = os.path.join(self.lgetdir, 'file')
        assertx(os.path.exists(p1), '==', True)
        # rename
        self.sftp.getfile(r, self.lgetdir, 'newfile')
        p2 = os.path.join(self.lgetdir, 'newfile')
        assertx(os.path.exists(p2), '==', True)

    def step5(self):
        """
        Test `open` method.
        """
        p = self.sftp.join(self.rputdir, 'file')
        with self.sftp.open(p, 'w') as fp:
            fp.write('xbot')
        with self.sftp.open(p, 'r') as fp:
            assertx(fp.read().decode('utf-8'), '==', 'xbot')

    def teardown(self):
        """
        Clean up test environment.
        """
        shutil.rmtree(self.lputdir)
        shutil.rmtree(self.lgetdir)

