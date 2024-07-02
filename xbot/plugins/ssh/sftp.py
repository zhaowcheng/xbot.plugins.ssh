# Copyright (c) 2023-2024, zhaowcheng <zhaowcheng@163.com>

"""
SFTP module
"""

import os
import stat

from typing import Generator
from contextlib import contextmanager

from paramiko import Transport, SFTPClient, SFTPFile

from xbot.framework.logger import getlogger, ExtraAdapter


logger = getlogger(__name__)


class SFTPConnection(object):
    """
    SFTP connection.
    """
    def __init__(self):
        self._sftpclient = None
        self._logger = ExtraAdapter(logger, {})

    def connect(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 22
    ) -> None:
        """
        Open the connection.
        """
        if self._sftpclient and self._sftpclient.sock.active:
            return
        self._logger.extra['prefix'] = f'sftp://{user}@{host}:{port}'
        self._logger.info('Connecting...')
        t = Transport((host, port))
        t.connect(username=user, password=password)
        self._sftpclient = SFTPClient.from_transport(t)

    def disconnect(self) -> None:
        """
        Close the connection.
        """
        self._sftpclient.close()

    def getfile(self, rfile: str, ldir: str, filename: str = None) -> None:
        """
        Get `rfile` from SFTP server into `ldir`.
        
        :param rfile: remote file.
        :param ldir: local dir.
        :param filename: specify when you want to rename.

        >>> getfile('/tmp/myfile', '/home')  # /home/myfile
        >>> getfile('/tmp/myfile', 'D:\\')  # D:\\myfile
        >>> getfile('/tmp/myfile', '/home', 'newfile')  # /home/newfile
        """
        ldir = os.path.join(ldir, '')
        filename = filename or self.basename(rfile)
        lfile = os.path.join(ldir, filename)
        self._logger.info(f'Getting file {lfile} <= {rfile}')
        self._sftpclient.get(rfile, lfile)

    def putfile(self, lfile: str, rdir: str, filename: str = None) -> None:
        """
        Put `lfile` into the `rdir` of SFTP server.

        :param lfile: local file.
        :param rdir: remote dir.
        :param filename: specify when you want to rename.

        >>> putfile('/home/myfile', '/tmp')  # /tmp/myfile
        >>> putfile('D:\\myfile', '/tmp')  # /tmp/myfile
        >>> putfile('/home/myfile', '/tmp', 'newfile')  # /tmp/newfile
        """
        rdir = self.join(rdir, '')
        filename = filename or os.path.basename(lfile)
        rfile = self.join(rdir, filename)
        self._logger.info(f'Putting file {lfile} => {rfile}')
        self._sftpclient.put(lfile, rfile)
            
    def getdir(self, rdir: str, ldir: str) -> None:
        """
        Get `rdir` from SFTP server into `ldir`.
        
        :param rdir: remote dir.
        :param ldir: local dir.

        >>> getdir('/tmp/mydir', '/home')  # /home/mydir
        >>> getdir('/tmp/mydir', 'D:\\')  # D:\\mydir
        """
        rdir = self.normpath(rdir)
        ldir = os.path.join(ldir, '')
        self._logger.info(f'Getting dir {ldir} <= {rdir}')
        for top, dirs, files in self.walk(rdir):
            basename = self.basename(top)
            ldir = os.path.join(ldir, basename)
            if not os.path.exists(ldir):
                os.makedirs(ldir)
            for f in files:
                r = self.join(top, f)
                l = os.path.join(ldir, f)
                self._sftpclient.get(r, l)
            for d in dirs:
                l = os.path.join(ldir, d)
                if not os.path.exists(l):
                    os.makedirs(l)

    def putdir(self, ldir: str, rdir: str) -> None:
        """
        Put `ldir` into the `rdir` of SFTP server.

        :param ldir: local dir.
        :param rdir: remote dir.

        >>> putdir('/tmp/mydir', '/home')  # /home/mydir
        >>> putdir('D:\\mydir', '/home')  # /home/mydir
        """
        ldir = os.path.normpath(ldir)
        rdir = self.join(rdir, '')
        self._logger.info(f'Putting dir {ldir} => {rdir}')
        for top, dirs, files in os.walk(os.path.normpath(ldir)):
            basename = os.path.basename(top)
            rdir = self.join(rdir, basename)
            if not self.exists(rdir):
                self.makedirs(rdir)
            for f in files:
                l = os.path.join(top, f)
                r = self.join(rdir, f)
                self._sftpclient.put(l, r)
            for d in dirs:
                r = self.join(rdir, d)
                if not self.exists(r):
                    self.makedirs(r)

    def join(self, *paths: str) -> str:
        """
        Similar to os.path.join().
        """
        paths = [p.rstrip('/') for p in paths]
        return '/'.join(paths)

    def normpath(self, path: str) -> str:
        """
        Similar to os.path.normpath().
        """
        segs = [s.strip('/') for s in path.split('/')]
        path = self.join(*segs)
        return path.rstrip('/')

    def basename(self, path: str) -> str:
        """
        Similar to os.path.basename().
        """
        return path.rsplit('/', 1)[-1]

    def exists(self, path: str) -> str:
        """
        Similar to os.path.exists().
        """
        try:
            self._sftpclient.stat(path)
            return True
        except FileNotFoundError:
            return False

    def walk(self, path: str):
        """
        Similar to os.walk().
        """
        dirs, files =  [], []
        for a in self._sftpclient.listdir_attr(path):
            if stat.S_ISDIR(a.st_mode):
                dirs.append(a.filename)
            else:
                files.append(a.filename)
        yield path, dirs, files

        for d in dirs:
            for w in self.walk(self.join(path, d)):
                yield w

    def makedirs(self, path: str) -> str:
        """
        Similar to os.makedirs().
        """
        self._logger.info('Makedirs %s' % path)
        curpath = '/'
        for p in path.split('/'):
            curpath = self.join(curpath, p)
            if not self.exists(curpath):
                self._sftpclient.mkdir(curpath)

    @contextmanager
    def open(self, filepath: str, mode: str = 'r') -> Generator[SFTPFile, str, None]:
        """
        Similar to builtin open().
        """
        self._logger.info('Open %s with mode=%s' % (filepath, mode))
        f = self._sftpclient.open(filepath, mode)
        try:
            yield f
        finally:
            f.close()
