"""
Tests the creation of a Slice from scratch
"""
from crumb.settings import Settings
from crumb.bakery_items.slice import Slice
from crumb.repository import CrumbRepository
from crumb.slicers.slicers import delete_slicer

cr = CrumbRepository()


def test_graph_parallel() -> None:
    """
    Tests running a Slice in parallel
    """
    try:
        import tests.sample_crumbs  # pylint: disable=import-outside-toplevel
        assert tests.sample_crumbs.get5() == 5
    except ImportError:
        import sample_crumbs  # pylint: disable=import-outside-toplevel
        assert sample_crumbs.get5() == 5
    # did we load what we wanted?
    # print(cr.crumbs)
    assert 'get5' in cr.crumbs
    assert 'add15' in cr.crumbs
    assert 'minus' in cr.crumbs
    # n1 = Node(cr.get_crumb('get5'))
    # n2 = Node(cr.get_crumb('add15'))
    # n3 = Node(cr.get_crumb('minus'))
    # n4 = Node(cr.get_crumb('get5'))
    slice = Slice('test')
    # add and remove in
    slice.add_input('in', int)
    slice.remove_input('in')
    slice.add_input('in', int)
    # add and remove out
    slice.add_output('out', int)
    slice.remove_output('out')
    slice.add_output('out', int)
    # ins/outs
    slice.add_input('in2', int)
    slice.add_input('in3', int)
    slice.add_output('out2', int)
    # add crumbs
    slice.add_bakery_item('get5', cr.get_crumb('get5'))
    slice.add_bakery_item('add15', cr.get_crumb('add15'))
    slice.add_bakery_item('minus', cr.get_crumb('minus'))
    # add nodes
    node_1 = slice.add_node('get5')
    node_2 = slice.add_node('add15')
    node_3 = slice.add_node('minus')
    node_4 = slice.add_node('get5')
    node_5 = slice.add_node('minus')
    node_6 = slice.add_node('minus')
    # print([n1, n2, n3, n4, n5, n6])
    # add node to be remove
    _n = slice.add_node('minus')
    slice.add_input_mapping('in', _n, 'a')
    slice.remove_input_mapping('in', _n, 'a')
    # add input mapping
    slice.add_input_mapping('in', node_2, 'a')
    slice.add_input_mapping('in2', node_5, 'a')
    slice.add_input_mapping('in3', node_5, 'b')
    # add and remove input mapping
    slice.add_output_mapping('out', _n, None)
    slice.remove_output_mapping('out', _n, None)
    # check if number of nodes decrease when removing it
    length_initial = len(cr.get_crumb('minus').get_nodes_using())
    slice.remove_node(_n)
    length_end = len(cr.get_crumb('minus').get_nodes_using())
    assert length_end < length_initial
    # adds output mapping
    slice.add_output_mapping('out', node_3, None)
    slice.add_output_mapping('out2', node_4, None)
    # add/remove links
    slice.add_link(node_1, None, node_6, 'a')
    slice.remove_link(node_1, None, node_6, 'a')
    slice.add_link(node_1, None, node_6, 'a')
    slice.add_link(node_2, None, node_6, 'b')
    slice.add_link(node_5, None, node_3, 'a')
    slice.add_link(node_6, None, node_3, 'b')
    # other debug
    # from pprint import pprint
    # pprint(s.nodes[n1]['node'].output)
    # pprint(s.nodes[n6]['node'].input)
    # pprint(s.crumbs)
    # pprint(s.nodes)
    # print(s._check_graph_circular())
    # print(s._check_input_complete(only_in_output=True))
    # ensure parallel will be used
    delete_slicer()
    Settings.USE_MULTISLICER = True
    # run
    ret = slice.run(input={'in': 1, 'in2': 10, 'in3': 5})
    assert ret['out'] == 16
    assert ret['out2'] == 5
    # kill and re-run
    delete_slicer()
    ret = slice.run(input={'in': 1, 'in2': 10, 'in3': 5})
    assert ret['out'] == 16
    assert ret['out2'] == 5
    # print(s.to_json())
    delete_slicer()
    Settings.USE_MULTISLICER = False


if __name__ == '__main__':
    test_graph_parallel()
