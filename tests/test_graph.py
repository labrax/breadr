
import unittest

import crumb.settings as settings
from crumb.bakery_items.slice import Slice
from crumb.repository import CrumbRepository
from crumb.slicers.slicers import delete_slicer

cr = CrumbRepository()

class TestGraph(unittest.TestCase):
    def test_node_creation(self):
        import tests.sample_crumbs
        
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

        # print([n1, n2, n3, n4, n5, n6])

        _n = s.add_node('minus')
        s.add_input_mapping('in', _n, 'a')
        s.remove_input_mapping('in', _n, 'a')

        s.add_input_mapping('in', n2, 'a')
        s.add_input_mapping('in2', n5, 'a')
        s.add_input_mapping('in3', n5, 'b')

        s.add_output_mapping('out', _n, None)
        s.remove_output_mapping('out', _n, None)
        s.remove_node(_n)

        s.add_output_mapping('out', n3, None)
        s.add_output_mapping('out2', n4, None)

        s.add_link(n1, None, n6, 'a')
        s.remove_link(n1, None, n6, 'a')
        s.add_link(n1, None, n6, 'a')
        s.add_link(n2, None, n6, 'b')

        s.add_link(n5, None, n3, 'a')
        s.add_link(n6, None, n3, 'b')

        # from pprint import pprint

        # pprint(s.nodes[n1]['node'].output)
        # pprint(s.nodes[n6]['node'].input)
        
        # pprint(s.crumbs)
        # pprint(s.nodes)

        # print(s._check_graph_circular())
        # print(s._check_input_complete(only_in_output=True))

        from crumb.slicers.slicers import delete_slicer
        delete_slicer() # ensure parallel will be used
        settings.multislicer = True
        ret = s.run(input={'in': 1, 'in2': 10, 'in3': 5})

        self.assertEqual(ret['out'], 16)
        self.assertEqual(ret['out2'], 5)
