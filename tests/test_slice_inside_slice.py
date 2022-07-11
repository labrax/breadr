"""Test the creation of a Slice with a Slice inside"""
import os
import json
import tempfile
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
    delete_slicer()


def test_slice_inside_slice_similar_names():
    """Test the handling of external and internal variable names"""
    try:
        import tests.sample_crumbs  # pylint: disable=import-outside-toplevel
        assert tests.sample_crumbs.get5() == 5
    except ImportError:
        import sample_crumbs  # pylint: disable=import-outside-toplevel
        assert sample_crumbs.get5() == 5
    # inner slice
    slice_inner = Slice('inner')
    slice_inner.add_bakery_item('add', cr.get_crumb('sum2'))
    slice_inner.add_input('in1', int)
    slice_inner.add_input('in2', int)
    slice_inner.add_output('out', int)
    n_inner = slice_inner.add_node('add')
    slice_inner.add_input_mapping('in1', n_inner, 'input_a')
    slice_inner.add_input_mapping('in2', n_inner, 'input_b')
    slice_inner.add_output_mapping('out', n_inner, None)
    # mid slice
    slice_mid = Slice('mid')
    slice_mid.add_bakery_item('get5', cr.get_crumb('get5'))
    slice_mid.add_bakery_item('slice_inner', slice_inner)
    slice_mid.add_input('input', int)
    slice_mid.add_input('input2', int)
    slice_mid.add_output('out_inner', int)
    n_mid = slice_mid.add_node('get5')
    n_slice_inner = slice_mid.add_node('slice_inner')
    slice_mid.add_output_mapping('out_inner', n_slice_inner, 'out')
    slice_mid.add_link(n_mid, None, n_slice_inner, 'in1')
    slice_mid.add_link(n_mid, None, n_slice_inner, 'in2')
    # outer slice
    slice_outer = Slice('out')
    slice_outer.add_bakery_item('slice_mid', slice_mid)
    slice_outer.add_input('in1', int)
    slice_outer.add_input('in2', int)
    slice_outer.add_output('out', int)
    n_slice_mid = slice_outer.add_node('slice_mid')
    slice_outer.add_input_mapping('in1', n_slice_mid, 'input')
    slice_outer.add_input_mapping('in2', n_slice_mid, 'input2')
    slice_outer.add_output_mapping('out', n_slice_mid, 'out_inner')

    ret_inner = slice_inner.run(input={'in1': 1, 'in2': 1})
    assert ret_inner['out'] == 2
    ret_mid = slice_mid.run(input={'input1': 1, 'input2': 1})
    assert ret_mid['out_inner'] == 10
    ret_outer = slice_outer.run(input={'in1': 1, 'in2': 1})
    assert ret_outer['out'] == 10

    # reload from copy
    slice_outer_copy = Slice('out_copy')
    slice_outer_copy.from_json(slice_outer.to_json())
    assert slice_outer_copy.run(input={'in1': 1, 'in2': 1})['out'] == 10

    # settings for files
    mid_temp_file = tempfile.NamedTemporaryFile(delete=False)
    mid_temp_file.close()
    outer_temp_file = tempfile.NamedTemporaryFile(delete=False)
    outer_temp_file.close()

    # mid json changes when saving to file
    assert json.dumps(slice_mid.to_dict(False)) == json.dumps(slice_mid.to_dict(True))
    slice_mid.save_to_file(mid_temp_file.name, overwrite=True)
    assert json.dumps(slice_mid.to_dict(False)) != json.dumps(slice_mid.to_dict(True))
    interest = json.loads(slice_outer.to_json(False))['bakery_items']['slice_mid']['bakery_item']
    assert 'filepath' in interest
    assert 'input' not in interest

    # now try to reload this Slice with a part in another file:
    slice_outer_file = Slice('out_copy_file')
    slice_outer_file.from_json(slice_outer.to_json())
    assert slice_outer_file.run(input={'in1': 1, 'in2': 1})['out'] == 10

    # now try to save this last one
    slice_outer_file.save_to_file(path=outer_temp_file.name, overwrite=True)
    slice_outer_file.load_from_file(outer_temp_file.name)
    assert slice_outer_file.run(input={'in1': 1, 'in2': 1})['out'] == 10

    # delete the files
    os.unlink(mid_temp_file.name)
    os.unlink(outer_temp_file.name)


if __name__ == '__main__':
    test_slice_slice()
    test_slice_inside_slice_similar_names()
