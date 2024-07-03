<p align="center">
  <br>中文 | <a href="README.md">English</a>
</p>

***

## 简介

`xbot.plugins.ssh` 是为 [xbot.framework](https://github.com/zhaowcheng/xbot.framework) 提供 ssh 和 sftp 支持的插件。

## 安装

使用 pip 安装:

```
pip install xbot.plugins.ssh
```

## 入门

```python
import os
import shutil

from xbot.plugins.ssh.ssh import SSHConnection
from xbot.plugins.ssh.sftp import SFTPConnection

# Modify the following information to your own before trying to run.
host = '192.168.8.8'
user = 'xbot'
pwd = 'xbot'

# Create ssh connection.
sshconn = SSHConnection()
sshconn.connect(host, user, pwd)

# Expect the return code of command is 0.
sshconn.exec('ls -l', expect=0)

# Expect the return code of command is 2.
sshconn.exec('ls /errpath', expect=2)

# Expect the output of command contains `username`.
sshconn.exec('whoami', expect=user)

# Don't check the result of command.
sshconn.exec('ls -l', expect=None)
sshconn.exec('ls /errpath', expect=None)

# Execute command with sudo.
sshconn.sudo('whoami', expect='root')

# Interactive command.
sshconn.exec("read -p 'input: '", prompts={'input:': 'hello'})

# Attributes and methods of SSHCommandResult.
cmd = 'echo -e "jack 20\ntom 30"'
result = sshconn.exec(cmd)
assert str(result) == 'jack 20\ntom 30'
assert result.rc == 0
assert result.cmd == cmd
assert result.getfield('tom', 2) == '30'
assert result.getcol(2) == ['20', '30']

# Create sftp connection.
sftpconn = SFTPConnection()
sftpconn.connect(host, user, pwd)

# Preparing for sftp testing.
lhome = os.environ.get('HOME') or os.environ['HOMEPATH']
lputdir = os.path.join(lhome, 'lputdir')
lgetdir = os.path.join(lhome, 'lgetdir')
rputdir = '/tmp/rputgetdir'
rgetdir = rputdir
if os.path.exists(lputdir):
    shutil.rmtree(lputdir)
if sftpconn.exists(rputdir):
    sshconn.exec(f'rm -rf {rputdir}')
sftpconn.makedirs(rputdir)
os.makedirs(os.path.join(lputdir, 'dir', 'subdir'))
os.system('whoami > %s' % os.path.join(lputdir, 'file'))
os.system('whoami > %s' % os.path.join(lputdir, 'dir', 'subfile'))

# Put directory.
l = os.path.join(lputdir, 'dir')
sftpconn.putdir(l, rputdir)
p1 = sftpconn.join(rputdir, 'dir', 'subdir')
assert sftpconn.exists(p1) == True
p2 = sftpconn.join(rputdir, 'dir', 'subfile')
assert sftpconn.exists(p2) == True

# Put file.
l = os.path.join(lputdir, 'file')
sftpconn.putfile(l, rputdir)
p1 = sftpconn.join(rputdir, 'file')
assert sftpconn.exists(p1) == True
sftpconn.putfile(l, rputdir, 'newfile')  # rename
p2 = sftpconn.join(rputdir, 'newfile')
assert sftpconn.exists(p2) == True

# Get directory.
r = sftpconn.join(rgetdir, 'dir')
sftpconn.getdir(r, lgetdir)
p1 = os.path.join(lgetdir, 'dir', 'subdir')
assert os.path.exists(p1) == True
p2 = os.path.join(lgetdir, 'dir', 'subfile')
assert os.path.exists(p2) == True

# Get file.
r = sftpconn.join(rgetdir, 'file')
sftpconn.getfile(r, lgetdir)
p1 = os.path.join(lgetdir, 'file')
assert os.path.exists(p1) == True
sftpconn.getfile(r, lgetdir, 'newfile')  # rename
p2 = os.path.join(lgetdir, 'newfile')
assert os.path.exists(p2) == True

# Open file.
p = sftpconn.join(rputdir, 'file')
with sftpconn.open(p, 'w') as fp:
    fp.write('xbot')
with sftpconn.open(p, 'r') as fp:
    assert fp.read().decode('utf-8') == 'xbot'
```

## 示例项目

展示如何在一个测试项目中使用本插件的示例：[demo](https://github.com/zhaowcheng/xbot.plugins.ssh/tree/master/demo)
