from typing import Union

from xbot.framework import testbed
from xbot.plugins.ssh.ssh import SSHConnection
from xbot.plugins.ssh.sftp import SFTPConnection


class TestBed(testbed.TestBed):
    """
    TestBed for ssh demo.
    """
    def __init__(self, filepath: str):
        """
        :param filepath: testbed filepath.
        """
        super().__init__(filepath)
        self._conns = {
            'ssh': {},
            'sftp': {}
        }

    def get_conn(
        self, 
        typ: str,
        role: str
    ) -> Union[SSHConnection, SFTPConnection]:
        """
        Get specific connection to the specified role.

        :param typ: connection type, 'ssh' or 'sftp'.
        :param role: user role.
        """
        typs = ('ssh', 'sftp')
        if typ not in typs:
            raise ValueError(f'Invalid connection type: {typ}, should be one of {typs}.')
        for user in self.get('host.users'):
            if user['role'] == role:
                if role not in self._conns[typ]:
                    conn = SSHConnection() if typ == 'ssh' else SFTPConnection()
                    conn.connect(self.get('host.ip'), 
                                 user['name'], 
                                 user['password'], 
                                 port=self.get('host.sshport'))
                    self._conns[typ][role] = conn
                return self._conns[typ][role]
        raise ValueError(f'No such user: role={role}')

    
