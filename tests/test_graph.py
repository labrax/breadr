
import unittest

from crumb import crumb
from crumb.slice import Slice
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

        @crumb(input={'a': int, 'b': int}, output=int, name='minus')
        def minus(a, b):
            return a - b
        
        self.assertIn('get5', cr.crumbs)
        self.assertIn('add15', cr.crumbs)
        self.assertIn('minus', cr.crumbs)

        # n1 = Node(cr.get_crumb('get5'))
        # n2 = Node(cr.get_crumb('add15'))
        # n3 = Node(cr.get_crumb('minus'))
        # n4 = Node(cr.get_crumb('get5'))

        s = Slice('test')
        s.add_input('in', int)
        s.remove_input('in')
        s.add_input('in', int)

        s.add_output('out', int)
        s.remove_output('out')
        s.add_output('out', int)

        s.add_input('in2', int)
        s.add_input('in3', int)
        s.add_output('out2', int)

        s.add_crumb('get5', cr.get_crumb('get5'))
        s.add_crumb('add15', cr.get_crumb('add15'))
        s.add_crumb('minus', cr.get_crumb('minus'))

        n1 = s.add_node('get5')
        n2 = s.add_node('add15')
        n3 = s.add_node('minus')
        n4 = s.add_node('get5')
        n5 = s.add_node('minus')
        n6 = s.add_node('minus')

        s.add_input_mapping('in', n2, 'a')
        s.add_input_mapping('in2', n5, 'a')
        s.add_input_mapping('in3', n5, 'b')

        s.add_output_mapping('out', n3, None)
        s.add_output_mapping('out2', n4, None)

        s.add_link(n1, None, n6, 'a')
        s.add_link(n2, None, n6, 'b')

        s.add_link(n5, None, n3, 'a')
        s.add_link(n6, None, n3, 'b')

        from pprint import pprint

        pprint(s.nodes[n1].output)
        pprint(s.nodes[n6].input)
        
        pprint(s.crumbs)
        pprint(s.nodes)

        print(s._check_graph_circular())
        print(s._check_input_complete(only_in_output=True))

        


