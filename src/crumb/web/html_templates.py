"""HTML Templates"""

from tornado.template import Template

# basic
INPUT_NODE_TEMPLATE = Template("""
<div class="title-box"><i class="fa-solid fa-arrow-right-to-bracket green-iconcolor"></i> Input</div>
<div class="box">
    <p>Input name <i id="input-save" class="fa-solid fa-floppy-disk" onclick="editor.setParameter({{node_id}});"></i></p>
    <input type="text" class="node-name-{{node_id}}" value="{{node_output_name}}" onchange="onParameterChange({{node_id}});" onkeypress="this.onchange();" onpaste="this.onchange();" oninput="this.onchange();">
    <p>Variable type</p>
    <input type="text" class="node-type-{{node_id}}" value="int" onchange="onParameterChange({{node_id}});" onkeypress="this.onchange();" onpaste="this.onchange();" oninput="this.onchange();">
</div>""")

OUTPUT_NODE_TEMPLATE = Template("""
<div class="title-box"><i class="fa-solid fa-arrow-right-from-bracket green-iconcolor"></i> Output</div>
<div class="box">
    <p>Output name <i id="output-save" class="fa-solid fa-floppy-disk" onclick="editor.setParameter({{node_id}});"></i></p>
    <input type="text" class="node-name-{{node_id}}" value="{{node_input_name}}" onchange="onParameterChange({{node_id}});" onkeypress="this.onchange();" onpaste="this.onchange();" oninput="this.onchange();">
    <p>Variable type</p>
    <input type="text" class="node-type-{{node_id}}" value="int" onchange="onParameterChange({{node_id}});" onkeypress="this.onchange();" onpaste="this.onchange();" oninput="this.onchange();">
</div>""")

# others
NODE_TEMPLATE = Template("""
<div>
    <div class="title-box"><i class="{{node_icon}}"></i> {{node_name}}</div>
    <div class="box">
    {{node_description}}
    </div>
</div>""")

# section
SECTION_TEMPLATE = Template("""<div class="col-section">
<div class="hide-section {{section_code}}" onclick="hideSection('{{section_code}}')">{{section_name}}</div>
<div class="col-section-values {{section_code}}">
{% for f in functions %}
<div class="drag-drawflow" draggable="true" ondragstart="drag(event)" data-node="{{f['type_identifier']}}">
    <i class="{{f['icon']}}"></i><span> {{f['name']}}</span>
</div>
{% end %}
</div>
</div>""")

# nav_element
NAV_TYPES = {'folder': b'&#128193;',
             'file': b'&#128221;',
             'breadr': b'&#127838;'}


def function_list_as_html(sections):
    ret = ''
    for s in sections:
        section_code = s['code']
        section_name = s['name']
        ret += SECTION_TEMPLATE.generate(section_code=section_code, section_name=section_name, functions=s['functions']).decode('utf-8')
    return ret
