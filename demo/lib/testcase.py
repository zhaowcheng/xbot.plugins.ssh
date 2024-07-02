from xbot.framework import testcase

from .testbed import TestBed


class TestCase(testcase.TestCase):
    """
    TestCase for ssh demo.
    """
    @property
    def testbed(self) -> TestBed:
        """
        TestBed instance.
        """
        return self.__testbed
