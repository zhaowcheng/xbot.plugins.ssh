# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

import unittest
import doctest
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from xbot.plugins.ssh import utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


if __name__ == '__main__':
    unittest.main(verbosity=2)
