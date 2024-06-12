from paramiko import SSHClient, AutoAddPolicy
from datetime import datetime
from select import select
from time import sleep

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect('192.168.70.14', username='highgo', password='iflow@123')
# i, o, e = ssh.exec_command('/home/highgo/hgdb/bin/initdb -W -D /tmp/data', get_pty=True)
# i.write('highgo@123\n')
# i.write('highgo@123\n')
# for c in iter(lambda: o.channel.recv(1).decode(), ''):
    # print(c, end='')
# shell = ssh.invoke_shell()
# shell.send('/home/highgo/hgdb/bin/initdb -W -D /tmp/data\n')
# for c in iter(lambda: shell.recv(1).decode(), ''):
#     print(c, end='')


# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.


import socket
import sys

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)


def posix_shell(chan):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = chan.recv(1024).decode()
                    if len(x) == 0:
                        sys.stdout.write("\r\n*** EOF\r\n")
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write(
        "Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n"
    )

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write("\r\n*** EOF ***\r\n\r\n")
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass


# shell = ssh.invoke_shell()
i, o, e = ssh.exec_command('rm -rf /tmp/data; /home/highgo/hgdb/bin/initdb -W -D /tmp/data', get_pty=True, timeout=10)
rs = ''
first = False
second = False
# for c in iter(lambda: o.channel.recv(1).decode(), ''):
#     rs += c
#     print(c, end='', flush=True)
#     if not first and 'password:' in rs.splitlines()[-1]:
#         i.write('highgo@123\n')
#         i.flush()
#         first = True
#     if not second and 'again:' in rs.splitlines()[-1]:
#         i.write('highgo@123\n')
#         i.flush()
#         second = True
start = datetime.now()
while (datetime.now() - start).seconds <= 10:
    r, w, e = select([o.channel], [], [])
    if o.channel in r:
        x = o.channel.recv(1024).decode()
        rs += x
        if len(x) == 0:
            break
        sys.stdout.write(x)
        sys.stdout.flush()
        if not first and 'password:' in rs.splitlines()[-1]:
            i.write('highgo@123\n')
            i.flush()
            first = True
        if not second and 'again:' in rs.splitlines()[-1]:
            i.write('highgo@123\n')
            i.flush()
            second = True
    # if o.channel.exit_status_ready():
        # break
    sleep(0.1)
    
else:
    raise TimeoutError('command not finished within 10s')
