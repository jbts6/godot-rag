# VisualShaderNodeColorParameter

**Inherits:** `VisualShaderNodeParameter` **<** `VisualShaderNode` **<** `Resource` **<** `RefCounted` **<** `Object`

A `Color` parameter to be used within the visual shader graph.

## Description

Translated to `uniform vec4` in the shader language.

## Property Descriptions

`Color` **default_value** = `Color(1, 1, 1, 1)`

- `void (No return value.)` **set_default_value**(value: `Color`)
- `Color` **get_default_value**()

A default value to be assigned within the shader.

`bool` **default_value_enabled** = `false`

- `void (No return value.)` **set_default_value_enabled**(value: `bool`)
- `bool` **is_default_value_enabled**()

Enables usage of the `default_value`.