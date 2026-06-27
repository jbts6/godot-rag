# VisualShaderNodeFrame

**Inherits:** `VisualShaderNodeResizableBase` **<** `VisualShaderNode` **<** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `VisualShaderNodeComment`

A frame other visual shader nodes can be attached to for better organization.

## Description

A rectangular frame that can be used to group visual shader nodes together to improve organization.

Nodes attached to the frame will move with it when it is dragged and it can automatically resize to enclose all attached nodes.

Its title, description and color can be customized.

## Property Descriptions

`PackedInt32Array` **attached_nodes** = `PackedInt32Array()`

- `void (No return value.)` **set_attached_nodes**(value: `PackedInt32Array`)
- `PackedInt32Array` **get_attached_nodes**()

The list of nodes attached to the frame.

**Note:** The returned array is *copied* and any changes to it will not update the original property value. See `PackedInt32Array` for more details.

`bool` **autoshrink** = `true`

- `void (No return value.)` **set_autoshrink_enabled**(value: `bool`)
- `bool` **is_autoshrink_enabled**()

If `true`, the frame will automatically resize to enclose all attached nodes.

`Color` **tint_color** = `Color(0.3, 0.3, 0.3, 0.75)`

- `void (No return value.)` **set_tint_color**(value: `Color`)
- `Color` **get_tint_color**()

The color of the frame when `tint_color_enabled` is `true`.

`bool` **tint_color_enabled** = `false`

- `void (No return value.)` **set_tint_color_enabled**(value: `bool`)
- `bool` **is_tint_color_enabled**()

If `true`, the frame will be tinted with the color specified in `tint_color`.

`String` **title** = `"Title"`

- `void (No return value.)` **set_title**(value: `String`)
- `String` **get_title**()

The title of the node.

## Method Descriptions

`void (No return value.)` **add_attached_node**(node: `int`)

Adds a node to the list of nodes attached to the frame. Should not be called directly, use the `VisualShader.attach_node_to_frame()` method instead.

`void (No return value.)` **remove_attached_node**(node: `int`)

Removes a node from the list of nodes attached to the frame. Should not be called directly, use the `VisualShader.detach_node_from_frame()` method instead.