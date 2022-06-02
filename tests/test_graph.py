
import unittest

from crumb import crumb
from crumb.repository import CrumbRepository
from crumb.graph import Node

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

        cr = CrumbRepository()
        self.assertIn('get5', cr.crumbs)
        self.assertIn('add15', cr.crumbs)
        self.assertIn('minus', cr.crumbs)

        n1 = Node(cr.crumbs['get5'])
        n2 = Node(cr.crumbs['add15'])
        n3 = Node(cr.crumbs['minus'])

        print([n1, n2, n3])