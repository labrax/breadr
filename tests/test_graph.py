
import unittest

from crumb import crumb
from crumb.repository import CrumbRepository
from crumb.node import Node

cr = CrumbRepository()

class TestGraph(unittest.TestCase):
    def test_node_creation(self):
        @crumb(output=int, name='get5')
        def get5():
            return 5

        @crumb(input={'a': int}, output=int, name='add15')
        def add15(a, b=15):
            return a + b

        @crumb(input={'a': int, 'b': int}, output='int', name='minus')
        def minus(a, b):
            return a - b
        
        self.assertIn('get5', cr.crumbs)
        self.assertIn('add15', cr.crumbs)
        self.assertIn('minus', cr.crumbs)

        n1 = Node(cr.get_crumb('get5'))
        n2 = Node(cr.get_crumb('add15'))
        n3 = Node(cr.get_crumb('minus'))
        n4 = Node(cr.get_crumb('get5'))
        
        print([n1, n2, n3, n4])