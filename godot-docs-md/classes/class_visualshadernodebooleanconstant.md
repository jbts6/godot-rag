# VisualShaderNodeBooleanConstant

**Inherits:** `VisualShaderNodeConstant` **<** `VisualShaderNode` **<** `Resource` **<** `RefCounted` **<** `Object`

A boolean constant to be used within the visual shader graph.

## Description

Has only one output port and no inputs.

Translated to `bool` in the shader language.

## Property Descriptions

`bool` **constant** = `false`

- `void (No return value.)` **set_constant**(value: `bool`)
- `bool` **get_constant**()

A boolean constant which represents a state of this node.