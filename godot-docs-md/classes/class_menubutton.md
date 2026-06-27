# MenuButton

**Inherits:** `Button` **<** `BaseButton` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`

A button that brings up a `PopupMenu` when clicked.

## Description

A button that brings up a `PopupMenu` when clicked. To create new items inside this `PopupMenu`, use `get_popup().add_item("My Item Name")`. You can also create them directly from Godot editor's inspector.

See also `BaseButton` which contains common properties and methods associated with this node.

## Signals

**about_to_popup**()

Emitted when the `PopupMenu` of this MenuButton is about to show.

## Property Descriptions

`int` **item_count** = `0`

- `void (No return value.)` **set_item_count**(value: `int`)
- `int` **get_item_count**()

The number of items currently in the list.

`int` **popup/item\_{index}/checkable** = `0`

The checkable item type of the item at `index`.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`bool` **popup/item\_{index}/checked** = `false`

If `true`, the item at `index` is checked.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`bool` **popup/item\_{index}/disabled** = `false`

If `true`, the item at `index` is disabled.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`Texture2D` **popup/item\_{index}/icon**

The icon of the item at `index`.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`int` **popup/item\_{index}/id** = `0`

The ID of the item at `index`.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`bool` **popup/item\_{index}/separator** = `false`

If `true`, the item at `index` is a separator.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`String` **popup/item\_{index}/text** = `""`

The text of the item at `index`.

**Note:** `index` is a value in the `0 .. item_count - 1` range.

`bool` **switch_on_hover** = `false`

- `void (No return value.)` **set_switch_on_hover**(value: `bool`)
- `bool` **is_switch_on_hover**()

If `true`, when the cursor hovers above another **MenuButton** within the same parent which also has `switch_on_hover` enabled, it will close the current **MenuButton** and open the other one.

## Method Descriptions

`PopupMenu` **get_popup**() `const`

Returns the `PopupMenu` contained in this button.

**Warning:** This is a required internal node, removing and freeing it may cause a crash. If you wish to hide it or any of its children, use their `Window.visible` property.

`void (No return value.)` **set_disable_shortcuts**(disabled: `bool`)

If `true`, shortcuts are disabled and cannot be used to trigger the button.

`void (No return value.)` **show_popup**()

Adjusts popup position and sizing for the **MenuButton**, then shows the `PopupMenu`. Prefer this over using `get_popup().popup()`.