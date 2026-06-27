# VisualShaderNodeParameterRef

**Inherits:** `VisualShaderNode` **<** `Resource` **<** `RefCounted` **<** `Object`

A reference to an existing `VisualShaderNodeParameter`.

## Description

Creating a reference to a `VisualShaderNodeParameter` allows you to reuse this parameter in different shaders or shader stages easily.

## Property Descriptions

`String` **parameter_name** = `"[None]"`

- `void (No return value.)` **set_parameter_name**(value: `String`)
- `String` **get_parameter_name**()

The name of the parameter which this reference points to.