# VisualShaderNodeGroupBase

**Inherits:** `VisualShaderNodeResizableBase` **<** `VisualShaderNode` **<** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `VisualShaderNodeExpression`

Base class for a family of nodes with variable number of input and output ports within the visual shader graph.

## Description

Currently, has no direct usage, use the derived classes instead.

## Method Descriptions

`void (No return value.)` **add_input_port**(id: `int`, type: `int`, name: `String`)

Adds an input port with the specified `type` (see `PortType`) and `name`.

`void (No return value.)` **add_output_port**(id: `int`, type: `int`, name: `String`)

Adds an output port with the specified `type` (see `PortType`) and `name`.

`void (No return value.)` **clear_input_ports**()

Removes all previously specified input ports.

`void (No return value.)` **clear_output_ports**()

Removes all previously specified output ports.

`int` **get_free_input_port_id**() `const`

Returns a free input port ID which can be used in `add_input_port()`.

`int` **get_free_output_port_id**() `const`

Returns a free output port ID which can be used in `add_output_port()`.

`int` **get_input_port_count**() `const`

Returns the number of input ports in use. Alternative for `get_free_input_port_id()`.

`String` **get_inputs**() `const`

Returns a `String` description of the input ports as a colon-separated list using the format `id,type,name;` (see `add_input_port()`).

`int` **get_output_port_count**() `const`

Returns the number of output ports in use. Alternative for `get_free_output_port_id()`.

`String` **get_outputs**() `const`

Returns a `String` description of the output ports as a colon-separated list using the format `id,type,name;` (see `add_output_port()`).

`bool` **has_input_port**(id: `int`) `const`

Returns `true` if the specified input port exists.

`bool` **has_output_port**(id: `int`) `const`

Returns `true` if the specified output port exists.

`bool` **is_valid_port_name**(name: `String`) `const`

Returns `true` if the specified port name does not override an existed port name and is valid within the shader.

`void (No return value.)` **remove_input_port**(id: `int`)

Removes the specified input port.

`void (No return value.)` **remove_output_port**(id: `int`)

Removes the specified output port.

`void (No return value.)` **set_input_port_name**(id: `int`, name: `String`)

Renames the specified input port.

`void (No return value.)` **set_input_port_type**(id: `int`, type: `int`)

Sets the specified input port's type (see `PortType`).

`void (No return value.)` **set_inputs**(inputs: `String`)

Defines all input ports using a `String` formatted as a colon-separated list: `id,type,name;` (see `add_input_port()`).

`void (No return value.)` **set_output_port_name**(id: `int`, name: `String`)

Renames the specified output port.

`void (No return value.)` **set_output_port_type**(id: `int`, type: `int`)

Sets the specified output port's type (see `PortType`).

`void (No return value.)` **set_outputs**(outputs: `String`)

Defines all output ports using a `String` formatted as a colon-separated list: `id,type,name;` (see `add_output_port()`).