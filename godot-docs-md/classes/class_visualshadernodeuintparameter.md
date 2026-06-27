# VisualShaderNodeUIntParameter

**Inherits:** `VisualShaderNodeParameter` **<** `VisualShaderNode` **<** `Resource` **<** `RefCounted` **<** `Object`

A visual shader node for shader parameter (uniform) of type unsigned `int`.

## Description

A `VisualShaderNodeParameter` of type unsigned `int`. Offers additional customization for range of accepted values.

## Property Descriptions

`int` **default_value** = `0`

- `void (No return value.)` **set_default_value**(value: `int`)
- `int` **get_default_value**()

Default value of this parameter, which will be used if not set externally. `default_value_enabled` must be enabled; defaults to `0` otherwise.

`bool` **default_value_enabled** = `false`

- `void (No return value.)` **set_default_value_enabled**(value: `bool`)
- `bool` **is_default_value_enabled**()

If `true`, the node will have a custom default value.