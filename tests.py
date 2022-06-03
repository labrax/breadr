
# execute all the tests

import unittest

from tests.basic import TestBasics, TestSlice
from tests.invalid_function_def import TestInputErrors
from tests.singleton import TestCrumbRepositorySingleton
from tests.test_graph import TestGraph

if __name__ == '__main__':
    unittest.main()
