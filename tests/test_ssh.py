# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

import unittest
import doctest
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from xbot.plugins.ssh import ssh
from xbot.plugins.ssh.ssh import SSHConnection
from xbot.plugins.ssh.errors import SSHConnectError, SSHCommandError


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(ssh))
    return tests


class TestSSHConnection(unittest.TestCase):

    HOST = ''
    PORT = 22
    USER = ''
    PWD = ''

    conn = SSHConnection()

    def setenv(self, name: str, value: str) -> None:
        self.conn.exec(f'export {name}="{value}"')

    def getenv(self, name: str) -> str:
        return self.conn.exec(f'echo ${name}')

    @classmethod
    def setUpClass(cls) -> None:
        cls.conn.connect(cls.HOST, cls.USER, cls.PWD, cls.PORT)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.disconnect()

    def test_connect_error_pwd(self):
        conn = SSHConnection()
        with self.assertRaises(SSHConnectError) as cm:
            conn.connect(self.HOST, self.USER, self.PWD + 'shit', self.PORT)
        self.assertIn('please check whether the username and password are correct',
                      str(cm.exception))
        
    def test_connect_error_port(self):
        conn = SSHConnection()
        with self.assertRaises(SSHConnectError) as cm:
            conn.connect(self.HOST, self.USER, self.PWD, self.PORT + 1000)
        self.assertRegex(str(cm.exception),
                         r'.*please check whether the port is (opened|correct).*')
        
    def test_connect_error_ip(self):
        conn = SSHConnection()
        with self.assertRaises(SSHConnectError) as cm:
            conn.connect('128.0.0.1', self.USER, self.PWD, self.PORT)
        self.assertIn('please check whether the network is normal',
                      str(cm.exception))

    def test_cmd_whoami(self):
        self.conn.exec('whoami', expect=self.USER)

    def test_cmd_sudo(self):
        self.conn.sudo('whoami', expect='root')

    def test_cmd_interact(self):
        self.conn.exec("read -p 'input: '", prompts={'input:': 'hello'})

    def test_expect_0(self):
        self.conn.exec('ls /tmp', expect=0)
        with self.assertRaises(SSHCommandError):
            self.conn.exec('ls /errpath', expect=0)

    def test_expect_2(self):
        self.conn.exec('ls /errpath', expect=2)

    def test_expect_none(self):
        self.conn.exec('ls /tmp', expect=None)
        self.conn.exec('ls /errpath', expect=None)

    def test_expect_str(self):
        self.conn.exec('echo hello', expect='hello')
        with self.assertRaises(SSHCommandError):
            self.conn.exec('echo hello', expect='world')

    def test_timeout(self):
        with self.assertRaises(TimeoutError):
            self.conn.exec('sleep 3', timeout=1)

    def test_cmd_cd(self):
        with self.conn.cd('/tmp'):
            self.assertEqual(self.conn.exec('pwd'), '/tmp')


if __name__ == '__main__':
    unittest.main(verbosity=2)
