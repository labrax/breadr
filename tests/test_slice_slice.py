"""Test the creation of a Slice with a Slice inside"""
from crumb import settings
from crumb.bakery_items.slice import Slice
from crumb.repository import CrumbRepository
from crumb.slicers.slicers import delete_slicer

cr = CrumbRepository()


def test_slice_slice() -> None:
    """
    Tests running a Slice in parallel
    """
    try:
        import tests.sample_crumbs  # pylint: disable=import-outside-toplevel
        assert tests.sample_crumbs.get5() == 5
    except ImportError:
        import sample_crumbs  # pylint: disable=import-outside-toplevel
        assert sample_crumbs.get5() == 5
    slice_3_sum = Slice(name='sum_3_n')
    slice_3_sum.add_bakery_item('sum2', cr.get_crumb('sum2'))
    slice_3_sum.add_input('num1', int)
    slice_3_sum.add_input('num2', int)
    slice_3_sum.add_input('num3', int)
    slice_3_sum.add_output('the_sum', int)
    node_1 = slice_3_sum.add_node('sum2')
    node_2 = slice_3_sum.add_node('sum2')
    slice_3_sum.add_input_mapping('num1', node_1, 'input_a')
    slice_3_sum.add_input_mapping('num2', node_1, 'input_b')
    slice_3_sum.add_link(node_1, None, node_2, 'input_a')
    slice_3_sum.add_input_mapping('num3', node_2, 'input_b')
    slice_3_sum.add_output_mapping('the_sum', node_2, None)
    ret = slice_3_sum.run(input={'num1': 1, 'num2': 1, 'num3': 1})
    assert ret['the_sum'] == 3
    # print('-------------------------------------------')
    # now for 4 inputs
    slice_4_sum = Slice(name='sum_4_n')
    slice_4_sum.add_bakery_item('sum2', cr.get_crumb('sum2'))
    slice_4_sum.add_bakery_item('sum3', slice_3_sum)
    slice_4_sum.add_input('in1', int)
    slice_4_sum.add_input('in2', int)
    slice_4_sum.add_input('in3', int)
    slice_4_sum.add_input('in4', int)
    slice_4_sum.add_output('out_3', int)
    slice_4_sum.add_output('out_4', int)
    node_3 = slice_4_sum.add_node('sum3')
    node_4 = slice_4_sum.add_node('sum2')
    slice_4_sum.add_input_mapping('in1', node_3, 'num1')
    slice_4_sum.add_input_mapping('in2', node_3, 'num2')
    slice_4_sum.add_input_mapping('in3', node_3, 'num3')
    slice_4_sum.add_input_mapping('in4', node_4, 'input_b')
    slice_4_sum.add_output_mapping('out_3', node_3, 'the_sum')
    slice_4_sum.add_output_mapping('out_4', node_4, None)
    slice_4_sum.add_link(node_3, 'the_sum', node_4, 'input_a')
    ret = slice_4_sum.run(input={'in1': 1, 'in2': 1, 'in3': 1, 'in4': 1})
    assert ret['out_3'] == 3
    assert ret['out_4'] == 4
    delete_slicer()
    # print('-------------------------------------------')
    settings.USE_MULTISLICER = True
    ret = slice_4_sum.run(input={'in1': 1, 'in2': 1, 'in3': 1, 'in4': 1})
    assert ret['out_3'] == 3
    assert ret['out_4'] == 4


if __name__ == '__main__':
    test_slice_slice()
