"""html setup for nodes in html/js"""


from crumb.web.html_templates import NODE_TEMPLATE, INPUT_NODE_TEMPLATE, OUTPUT_NODE_TEMPLATE


def get_node_definition(identifier, classname, x_pos, y_pos, inputs, outputs, icon="fas fa-code-branch", node_description="\n\n\n\n"):
    """Generate standard node"""
    return {'node_id': identifier,
            'num_in': len(inputs),
            'num_out': len(outputs),
            'input_tooltips': {i+1: {'name': j[0], 'type': j[1].__name__} for i, j in enumerate(inputs.items())},
            'output_tooltips': {i+1: {'name': j[0], 'type': j[1].__name__} for i, j in enumerate(outputs.items())},
            'typenode': False,
            'html': NODE_TEMPLATE.generate(node_name=classname, node_icon=icon, node_description=node_description).decode('utf-8'),
            'classoverride': classname,
            'other_data': {},
            'pos': {'x': x_pos, 'y': y_pos}
            }


def get_input_definition(identifier, x_pos, y_pos, node_output_name):
    """Generate input node"""
    return {'node_id': identifier,
            'num_in': 0,
            'num_out': 1,
            'input_tooltips': {},
            'output_tooltips': {1: {'name': node_output_name, 'type': 'int'}},
            'typenode': False,
            'html': INPUT_NODE_TEMPLATE.generate(node_id=identifier, node_output_name=node_output_name).decode('utf-8'),
            'classoverride': 'input_element',
            'other_data': {},
            'pos': {'x': x_pos, 'y': y_pos}
            }


def get_output_definition(identifier, x_pos, y_pos, node_input_name):
    """Generate output node"""
    return {'node_id': identifier,
            'num_in': 1,
            'num_out': 0,
            'input_tooltips': {1: {'name': node_input_name, 'type': 'int'}},
            'output_tooltips': {},
            'typenode': False,
            'html': OUTPUT_NODE_TEMPLATE.generate(node_id=identifier, node_input_name=node_input_name).decode('utf-8'),
            'classoverride': 'output_element',
            'other_data': {},
            'pos': {'x': x_pos, 'y': y_pos}
            }
