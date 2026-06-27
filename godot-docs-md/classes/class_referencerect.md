# ReferenceRect

**Inherits:** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`

A rectangular box for designing UIs.

## Description

A rectangular box that displays only a colored border around its rectangle (see `Control.get_rect()`). It can be used to visualize the extents of a `Control` node, for testing purposes.

## Property Descriptions

`Color` **border_color** = `Color(1, 0, 0, 1)`

- `void (No return value.)` **set_border_color**(value: `Color`)
- `Color` **get_border_color**()

Sets the border color of the **ReferenceRect**.

`float` **border_width** = `1.0`

- `void (No return value.)` **set_border_width**(value: `float`)
- `float` **get_border_width**()

Sets the border width of the **ReferenceRect**. The border grows both inwards and outwards with respect to the rectangle box.

`bool` **editor_only** = `true`

- `void (No return value.)` **set_editor_only**(value: `bool`)
- `bool` **get_editor_only**()

If `true`, the **ReferenceRect** will only be visible while in editor. Otherwise, **ReferenceRect** will be visible in the running project.