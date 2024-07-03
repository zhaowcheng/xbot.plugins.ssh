from lib.testcase import TestCase


class tc_ssh(TestCase):
    """
    Testcase using SSHConnection.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['ssh']

    def setup(self):
        """
        Prepare test environment.
        """
        self.ssh = self.testbed.get_conn('ssh', 'normal')

    def step1(self):
        """
        Execute command `whoami`, expect `name` of the normal user.
        """
        username = self.testbed.get("host.users[?role=='normal']")[0]['name']
        self.ssh.exec('whoami', expect=username)
        
    def step2(self):
        """
        Execute command `sudo whoami`, expect `root`.
        """
        self.ssh.sudo('whoami', expect='root')

    def step3(self):
        """
        Execute a interactive command.
        """
        self.ssh.exec("read -p 'input: '", prompts={'input:': 'hello'})

    def step4(self):
        """
        Execute a command and expect no error.
        """
        self.ssh.exec('ls /tmp', expect=0)

    def step5(self):
        """
        Execute a command and expect return code is 2.
        """
        self.ssh.exec('ls /errpath', expect=2)

    def step5(self):
        """
        Execute a command and expect nothing.
        """
        self.ssh.exec('ls /tmp', expect=None)
        self.ssh.exec('ls /errpath', expect=None)

    def step6(self):
        """
        Execute a command and expect a specific output.
        """
        self.ssh.exec('echo hello', expect='hello')

    def step7(self):
        """
        Execute a command with cd context manager.
        """
        with self.ssh.cd('/tmp'):
            self.ssh.exec('pwd', expect='/tmp')

    def teardown(self):
        """
        Clean up test environment.
        """
        pass
