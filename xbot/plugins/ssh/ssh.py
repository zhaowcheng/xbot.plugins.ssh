# Copyright (c) 2023-2024, zhaowcheng <zhaowcheng@163.com>

"""
SSH module.
"""

import textwrap
import threading
import socket

from typing import Generator, Optional, Union
from datetime import datetime
from select import select
from contextlib import contextmanager

from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import (AuthenticationException, 
                                    NoValidConnectionsError, 
                                    SSHException)

from xbot.framework.logger import getlogger, ExtraAdapter
from xbot.plugins.ssh.errors import SSHConnectError, SSHCommandError
from xbot.plugins.ssh.utils import (remove_ansi_escape_chars, 
                                    remove_unprintable_chars)


logger = getlogger(__name__)


class SSHCommandResult(str):
    """
    Result of SSH command.
    """
    def __new__(cls, out: str, rc: int = 0, cmd: str = '') -> str:
        """
        :param out: output.
        :param rc: return code.
        :param cmd: command.
        """
        out = remove_ansi_escape_chars(out)
        out = remove_unprintable_chars(out)
        out = '\n'.join(out.splitlines())
        o = str.__new__(cls, out.strip())
        o.__rc = rc
        o.__cmd = cmd
        return o
    
    @property
    def rc(self) -> int:
        """
        Return code.
        """
        return self.__rc
    
    @property
    def cmd(self) -> str:
        """
        Command.
        """
        return self.__cmd

    def getfield(
        self,
        key: str,
        col: int,
        sep: str = None
    ) -> Optional[str]:
        """
        Get a specified field from the output.

        :param key: string to filter a line.
        :param col: column number in the filtered line.
        :param sep: char to split the filtered line.

        >>> r = SSHCommandResult('''\\
        ... UID        PID   CMD
        ... postgres   45    /opt/pgsql/bin/postgres
        ... postgres   51    postgres: checkpointer process
        ... postgres   52    postgres: writer process
        ... postgres   53    postgres: wal writer process''', 0, '')
        >>> r.getfield('/opt/pgsql', 2)
        '45'
        >>> r.getfield('checkpointer', 1, sep=':')
        'postgres   51    postgres'
        """
        matchline = ''
        lines = self.splitlines()
        if isinstance(key, str):
            for line in self.splitlines():
                if key in line:
                    matchline = line
        elif isinstance(key, int):
            matchline = lines[key-1]
        if matchline:
            fields = matchline.split(sep)
            return fields[col-1].strip()

    def getcol(
        self,
        col: int,
        sep: str = None
    ) -> list:
        """
        Get a specified column from the output.

        :param col: column number.
        :param sep: char to split lines.

        >>> r = SSHCommandResult('''\\
        ... UID        PID   CMD
        ... postgres   45    /opt/pgsql/bin/postgres
        ... postgres   51    postgres: checkpointer process
        ... postgres   52    postgres: writer process
        ... postgres   53    postgres: wal writer process''', 0, '')
        >>> r.getcol(2)
        ['PID', '45', '51', '52', '53']
        """
        fields = []
        for line in self.splitlines():
            segs = line.split(sep)
            if col <= len(segs):
                fields.append(segs[col-1])
        return fields


class SSHConnection(object):
    """
    SSH connection.
    """
    def __init__(self, shenvs: dict = {}):
        """
        :param shenvs: shell environment variables for method `exec`.
            `LANG` defaults to `en_US.UTF-8`.
            `LANGUAGE` defaults to `en_US.UTF-8`.
        """
        self._logger = ExtraAdapter(logger, {})
        self._sshclient = SSHClient()
        self._sshclient.set_missing_host_key_policy(AutoAddPolicy())
        self._shenvs = shenvs
        for k, v in {'LANG': 'en_US.UTF-8',
                     'LANGUAGE': 'en_US.UTF-8'}.items():
            self._shenvs[k] = self._shenvs.get(k, v)
        self._password = None
        self._cdlock = threading.Lock()
        self._cwd = ''

    def connect(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 22,
        timeout: int = 5
    ) -> None:
        """
        Open the connection.

        :param host: hostname or ip.
        :param user: user name.
        :param password: user password.
        :param port: SSH port.
        :param timeout: connect timeout(s).
        """
        transport = self._sshclient.get_transport()
        if transport and transport.active:
            return
        self._logger.extra['prefix'] = f'ssh://{user}@{host}:{port}'
        self._logger.info('Connecting...')
        try:
            self._sshclient.connect(host, port=port, username=user, 
                                    password=password, timeout=timeout)
            self._password = password
        except AuthenticationException:
            raise SSHConnectError(
                f'Authentication failed when SSH connect to {host} with user `{user}`, '
                f'please check whether the username and password are correct.'
            ) from None
        except socket.timeout:
            raise SSHConnectError(
                f'Timed out when SSH connect to {host}({timeout}s), '
                'please check whether the network is normal.'
            ) from None
        except NoValidConnectionsError:
            raise SSHConnectError(
                f'Could not connect to port {port} on {host}, '
                'please check whether the port is opened.'
            ) from None
        except SSHException as e:
            msg = str(e)
            if 'Error reading SSH protocol banner' in msg:
                raise SSHConnectError(
                    f'Read SSH protocol banner failed when connect to port {port} '
                    f'on {host}, please check whether the port is correct.'
                ) from None
            raise e from None

    def disconnect(self) -> None:
        """
        Close the connection.
        """
        self._sshclient.close()

    def exec(
        self,
        cmd: str,
        expect: Union[int, str, None] = 0,
        timeout: int = 15,
        prompts: dict = {},
        shenvs: dict = {}
    ) -> SSHCommandResult:
        """
        Execute a command on the SSH server.

        :param cmd: the command to be executed.
        :param expect: expected result of command execution.
            0: expect the return code of command is 0.
            'hello': expect the str 'hello' to appear in the output.
            None : do not check the result of command execution.
        :param timeout: command timeout (seconds).
        :param prompts: prompts and answers for interactive command.
        :param shenvs: shell environment variables for command.
        :return: output(stdout and stderr) of command.

        :raises: 
            `.SSHCommandError` -- if the result is not as expected.
            `TimeoutError` -- if the command execution is timedout.

        >>> exec('cd /home')  # successful                          # doctest: +SKIP
        >>> exec('cd /errpath')  # SSHCommandError                  # doctest: +SKIP
        >>> exec('cd /errpath', expect=1)  # no error               # doctest: +SKIP
        >>> exec('cd /errpath', expect=None)  # no error            # doctest: +SKIP
        >>> exec('echo hello', expect='hello')  # successful        # doctest: +SKIP
        >>> exec('echo hello', expect='world')  # SSHCommandError   # doctest: +SKIP
        >>> exec('sudo whoami', prompts={'password:': 'mypwd'})     # doctest: +SKIP
        """
        if self._cwd:
            cmd = f'cd {self._cwd} && {cmd}'
        extra = {'hook': {}}
        self._logger.info(f"Command: '{cmd}', Expect: '{expect}'", extra=extra)
        envs = self._shenvs.copy()
        envs.update(shenvs)
        stdin, stdout, _ = self._sshclient.exec_command(cmd, get_pty=True, environment=envs)
        start = datetime.now()
        output = ''
        encoding = envs['LANG'].split('.')[-1]
        while (datetime.now() - start).seconds <= timeout:
            rlist, _, _ = select([stdout.channel], [], [], 0.1)
            if stdout.channel in rlist:
                data = stdout.channel.recv(1024).decode(encoding=encoding, errors='ignore')
                output += data
                if data == '':
                    break
            if prompts and output:
                lastline = output.splitlines()[-1]
                written = None
                for k, v in prompts.items():
                    if k in lastline:
                        stdin.write(v + '\n')
                        stdin.flush()
                        written = k
                        break
                if written:
                    prompts.pop(written)
        else:
            result = SSHCommandResult(output, rc=-1)
            extra['hook']['more'] = result
            raise TimeoutError(f"Command '{cmd}' timedout({timeout}s):\n{result}")
        result = SSHCommandResult(output, rc=stdout.channel.recv_exit_status(), cmd=cmd)
        extra['hook']['more'] = result
        if expect != None:
            if (isinstance(expect, int) and expect != result.rc) or \
                    (isinstance(expect, str) and expect not in result):
                msg = textwrap.dedent(f"""\
                Expections not met:
                Command: {cmd}
                Excpect: {expect}
                ReturnCode: {result.rc}
                Output:
                    {output}
                """)
                raise SSHCommandError(msg)
        return result

    def sudo(self, cmd, *args, **kwargs) -> SSHCommandResult:
        """
        Execute a command with sudo, arguments are same to `exec`.
        """
        kwargs['prompts'] = {'[sudo] password': self._password}
        return self.exec(f'sudo {cmd}', *args, **kwargs)

    @contextmanager
    def cd(self, path) -> Generator[None, str, None]:
        """
        change current directory.

        >>> with cd('/my/workdir'):     # doctest: +SKIP
        ...     d = exec('pwd')         # doctest: +SKIP
        ...                             # doctest: +SKIP
        >>> d                           # doctest: +SKIP
        '/my/workdir'                   # doctest: +SKIP
        """
        self._cdlock.acquire()
        try:
            self._cwd = path
            yield
        finally:
            self._cwd = ''
            self._cdlock.release()

