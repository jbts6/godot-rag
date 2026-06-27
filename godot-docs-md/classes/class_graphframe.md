# GraphFrame

**Inherits:** `GraphElement` **<** `Container` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`

GraphFrame is a special `GraphElement` that can be used to organize other `GraphElement`s inside a `GraphEdit`.

## Description

GraphFrame is a special `GraphElement` to which other `GraphElement`s can be attached. It can be configured to automatically resize to enclose all attached `GraphElement`s. If the frame is moved, all the attached `GraphElement`s inside it will be moved as well.

A GraphFrame is always kept behind the connection layer and other `GraphElement`s inside a `GraphEdit`.

## Theme Properties

## Signals

**autoshrink_changed**()

Emitted when `autoshrink_enabled` or `autoshrink_margin` changes.

## Property Descriptions

`bool` **autoshrink_enabled** = `true`

- `void (No return value.)` **set_autoshrink_enabled**(value: `bool`)
- `bool` **is_autoshrink_enabled**()

If `true`, the frame's rect will be adjusted automatically to enclose all attached `GraphElement`s.

`int` **autoshrink_margin** = `40`

- `void (No return value.)` **set_autoshrink_margin**(value: `int`)
- `int` **get_autoshrink_margin**()

The margin around the attached nodes that is used to calculate the size of the frame when `autoshrink_enabled` is `true`.

`int` **drag_margin** = `16`

- `void (No return value.)` **set_drag_margin**(value: `int`)
- `int` **get_drag_margin**()

The margin inside the frame that can be used to drag the frame.

`Color` **tint_color** = `Color(0.3, 0.3, 0.3, 0.75)`

- `void (No return value.)` **set_tint_color**(value: `Color`)
- `Color` **get_tint_color**()

The color of the frame when `tint_color_enabled` is `true`.

`bool` **tint_color_enabled** = `false`

- `void (No return value.)` **set_tint_color_enabled**(value: `bool`)
- `bool` **is_tint_color_enabled**()

If `true`, the tint color will be used to tint the frame.

`String` **title** = `""`

- `void (No return value.)` **set_title**(value: `String`)
- `String` **get_title**()

Title of the frame.

## Method Descriptions

`HBoxContainer` **get_titlebar_hbox**()

Returns the `HBoxContainer` used for the title bar, only containing a `Label` for displaying the title by default.

This can be used to add custom controls to the title bar such as option or close buttons.

## Theme Property Descriptions

`Color` **resizer_color** = `Color(0.875, 0.875, 0.875, 1)`

The color modulation applied to the resizer icon.

`StyleBox` **panel**

The default `StyleBox` used for the background of the **GraphFrame**.

`StyleBox` **panel_selected**

The `StyleBox` used for the background of the **GraphFrame** when it is selected.

`StyleBox` **titlebar**

The `StyleBox` used for the title bar of the **GraphFrame**.

`StyleBox` **titlebar_selected**

The `StyleBox` used for the title bar of the **GraphFrame** when it is selected.