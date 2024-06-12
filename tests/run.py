"""
Run tests.
"""

import unittest
import argparse

from pathlib import Path

from test_ssh import TestSSHConnection
from test_sftp import TestSFTPConnection


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', required=True, 
                        help='hostname or ip to test.')
    parser.add_argument('-u', '--user', required=True, 
                        help='username for host.')
    parser.add_argument('-p', '--password', required=True, 
                        help='password for host.')
    parser.add_argument('-P', '--port', type=int, default=22,
                        help='ssh port for host.')
    return parser


if __name__ == '__main__':
    args = create_parser().parse_args()
    TestSSHConnection.HOST = args.host
    TestSSHConnection.USER = args.user
    TestSSHConnection.PWD = args.password
    TestSSHConnection.PORT = args.port
    TestSFTPConnection.HOST = args.host
    TestSFTPConnection.USER = args.user
    TestSFTPConnection.PWD = args.password
    TestSFTPConnection.PORT = args.port
    startdir = Path(__file__).parent
    testsuit = unittest.TestLoader().discover(startdir)
    unittest.TextTestRunner(verbosity=2).run(testsuit)
