# TreeItem

**Inherits:** `Object`

An internal control for a single item inside `Tree`.

## Description

A single item of a `Tree` control. It can contain other **TreeItem**s as children, which allows it to create a hierarchy. It can also contain text and buttons. **TreeItem** is not a `Node`, it is internal to the `Tree`.

To create a **TreeItem**, use `Tree.create_item()` or `create_child()`. To remove a **TreeItem**, use `Object.free()`.

**Note:** The ID values used for buttons are 32-bit, unlike `int` which is always 64-bit. They go from `-2147483648` to `2147483647`.

## Enumerations

enum **TreeCellMode**:

`TreeCellMode` **CELL_MODE_STRING** = `0`

Cell shows a string label, optionally with an icon. When editable, the text can be edited using a `LineEdit`, or a `TextEdit` popup if `set_edit_multiline()` is used.

`TreeCellMode` **CELL_MODE_CHECK** = `1`

Cell shows a checkbox, optionally with text and an icon. The checkbox can be pressed, released, or indeterminate (via `set_indeterminate()`). The checkbox can't be clicked unless the cell is editable.

`TreeCellMode` **CELL_MODE_RANGE** = `2`

Cell shows a numeric range. When editable, it can be edited using a range slider. Use `set_range()` to set the value and `set_range_config()` to configure the range.

This cell can also be used in a text dropdown mode when you assign a text with `set_text()`. Separate options with a comma, e.g. `"Option1,Option2,Option3"`.

`TreeCellMode` **CELL_MODE_ICON** = `3`

Cell shows an icon. It can't be edited nor display text. The icon is always centered within the cell.

`TreeCellMode` **CELL_MODE_CUSTOM** = `4`

Cell shows as a clickable button. It will display an arrow similar to `OptionButton`, but doesn't feature a dropdown (for that you can use `CELL_MODE_RANGE`). Clicking the button emits the `Tree.item_edited` signal. The button is flat by default, you can use `set_custom_as_button()` to display it with a `StyleBox`.

This mode also supports custom drawing using `set_custom_draw_callback()`.

## Property Descriptions

`bool` **collapsed**

- `void (No return value.)` **set_collapsed**(value: `bool`)
- `bool` **is_collapsed**()

If `true`, the TreeItem is collapsed.

`int` **custom_minimum_height**

- `void (No return value.)` **set_custom_minimum_height**(value: `int`)
- `int` **get_custom_minimum_height**()

The custom minimum height.

`bool` **disable_folding**

- `void (No return value.)` **set_disable_folding**(value: `bool`)
- `bool` **is_folding_disabled**()

If `true`, folding is disabled for this TreeItem.

`bool` **visible**

- `void (No return value.)` **set_visible**(value: `bool`)
- `bool` **is_visible**()

If `true`, the **TreeItem** is visible (default).

Note that if a **TreeItem** is set to not be visible, none of its children will be visible either.

## Method Descriptions

`void (No return value.)` **add_button**(column: `int`, button: `Texture2D`, id: `int` = -1, disabled: `bool` = false, tooltip_text: `String` = "", description: `String` = "")

Adds a button with `Texture2D` `button` to the end of the cell at column `column`. The `id` is used to identify the button in the according `Tree.button_clicked` signal and can be different from the buttons index. If not specified, the next available index is used, which may be retrieved by calling `get_button_count()` immediately before this method. Optionally, the button can be `disabled` and have a `tooltip_text`. `description` is used as the button description for assistive apps.

`void (No return value.)` **add_child**(child: `TreeItem`)

Adds a previously unparented **TreeItem** as a direct child of this one. The `child` item must not be a part of any `Tree` or parented to any **TreeItem**. See also `remove_child()`.

`void (No return value.)` **call_recursive**(method: `StringName`, ...) `vararg`

Calls the `method` on the actual TreeItem and its children recursively. Pass parameters as a comma separated list.

`void (No return value.)` **clear_buttons**()

Removes all buttons from all columns of this item.

`void (No return value.)` **clear_custom_bg_color**(column: `int`)

Resets the background color for the given column to default.

`void (No return value.)` **clear_custom_color**(column: `int`)

Resets the color for the given column to default.

`TreeItem` **create_child**(index: `int` = -1)

Creates an item and adds it as a child.

The new item will be inserted as position `index` (the default value `-1` means the last position), or it will be the last child if `index` is higher than the child count.

`void (No return value.)` **deselect**(column: `int`)

Deselects the given column.

`void (No return value.)` **erase_button**(column: `int`, button_index: `int`)

Removes the button at index `button_index` in column `column`.

`AutoTranslateMode` **get_auto_translate_mode**(column: `int`) `const`

Returns the column's auto translate mode.

`AutowrapMode` **get_autowrap_mode**(column: `int`) `const`

Returns the text autowrap mode in the given `column`. By default it is `TextServer.AUTOWRAP_OFF`.

`BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\] **get_autowrap_trim_flags**(column: `int`) `const`

Returns the autowrap trim flags for the given `column`. By default, both `TextServer.BREAK_TRIM_START_EDGE_SPACES` and `TextServer.BREAK_TRIM_END_EDGE_SPACES` are enabled.

`Texture2D` **get_button**(column: `int`, button_index: `int`) `const`

Returns the `Texture2D` of the button at index `button_index` in column `column`.

`int` **get_button_by_id**(column: `int`, id: `int`) `const`

Returns the button index if there is a button with ID `id` in column `column`, otherwise returns -1.

`Color` **get_button_color**(column: `int`, id: `int`) `const`

Returns the color of the button with ID `id` in column `column`. If the specified button does not exist, returns `Color.BLACK`.

`int` **get_button_count**(column: `int`) `const`

Returns the number of buttons in column `column`.

`int` **get_button_id**(column: `int`, button_index: `int`) `const`

Returns the ID for the button at index `button_index` in column `column`.

`String` **get_button_tooltip_text**(column: `int`, button_index: `int`) `const`

Returns the tooltip text for the button at index `button_index` in column `column`.

`TreeCellMode` **get_cell_mode**(column: `int`) `const`

Returns the column's cell mode.

`TreeItem` **get_child**(index: `int`)

Returns a child item by its `index` (see `get_child_count()`). This method is often used for iterating all children of an item.

Negative indices access the children from the last one.

`int` **get_child_count**()

Returns the number of child items.

`Array`\[`TreeItem`\] **get_children**()

Returns an array of references to the item's children.

`Color` **get_custom_bg_color**(column: `int`) `const`

Returns the custom background color of column `column`.

`Color` **get_custom_color**(column: `int`) `const`

Returns the custom color of column `column`.

`Callable` **get_custom_draw_callback**(column: `int`) `const`

Returns the custom callback of column `column`.

`Font` **get_custom_font**(column: `int`) `const`

Returns custom font used to draw text in the column `column`.

`int` **get_custom_font_size**(column: `int`) `const`

Returns custom font size used to draw text in the column `column`.

`StyleBox` **get_custom_stylebox**(column: `int`) `const`

Returns the given column's custom `StyleBox` used to draw the background.

`String` **get_description**(column: `int`) `const`

Returns the given column's description for assistive apps.

`bool` **get_expand_right**(column: `int`) `const`

Returns `true` if `expand_right` is set.

`TreeItem` **get_first_child**() `const`

Returns the TreeItem's first child.

`Texture2D` **get_icon**(column: `int`) `const`

Returns the given column's icon `Texture2D`. Error if no icon is set.

`int` **get_icon_max_width**(column: `int`) `const`

Returns the maximum allowed width of the icon in the given `column`.

`Color` **get_icon_modulate**(column: `int`) `const`

Returns the `Color` modulating the column's icon.

`Texture2D` **get_icon_overlay**(column: `int`) `const`

Returns the given column's icon overlay `Texture2D`.

`Rect2` **get_icon_region**(column: `int`) `const`

Returns the icon `Texture2D` region as `Rect2`.

`int` **get_index**()

Returns the node's order in the tree. For example, if called on the first child item the position is `0`.

`String` **get_language**(column: `int`) `const`

Returns item's text language code.

`Variant` **get_metadata**(column: `int`) `const`

Returns the metadata value that was set for the given column using `set_metadata()`.

`TreeItem` **get_next**() `const`

Returns the next sibling TreeItem in the tree or a `null` object if there is none.

`TreeItem` **get_next_in_tree**(wrap: `bool` = false)

Returns the next TreeItem in the tree (in the context of a depth-first search) or a `null` object if there is none.

If `wrap` is enabled, the method will wrap around to the first element in the tree when called on the last element, otherwise it returns `null`.

`TreeItem` **get_next_visible**(wrap: `bool` = false)

Returns the next visible TreeItem in the tree (in the context of a depth-first search) or a `null` object if there is none.

If `wrap` is enabled, the method will wrap around to the first visible element in the tree when called on the last visible element, otherwise it returns `null`.

`TreeItem` **get_parent**() `const`

Returns the parent TreeItem or a `null` object if there is none.

`TreeItem` **get_prev**()

Returns the previous sibling TreeItem in the tree or a `null` object if there is none.

`TreeItem` **get_prev_in_tree**(wrap: `bool` = false)

Returns the previous TreeItem in the tree (in the context of a depth-first search) or a `null` object if there is none.

If `wrap` is enabled, the method will wrap around to the last element in the tree when called on the first visible element, otherwise it returns `null`.

`TreeItem` **get_prev_visible**(wrap: `bool` = false)

Returns the previous visible sibling TreeItem in the tree (in the context of a depth-first search) or a `null` object if there is none.

If `wrap` is enabled, the method will wrap around to the last visible element in the tree when called on the first visible element, otherwise it returns `null`.

`float` **get_range**(column: `int`) `const`

Returns the value of a `CELL_MODE_RANGE` column.

`Dictionary` **get_range_config**(column: `int`)

Returns a dictionary containing the range parameters for a given column. The keys are "min", "max", "step", and "expr".

`StructuredTextParser` **get_structured_text_bidi_override**(column: `int`) `const`

Returns the BiDi algorithm override set for this cell.

`Array` **get_structured_text_bidi_override_options**(column: `int`) `const`

Returns the additional BiDi options set for this cell.

`String` **get_suffix**(column: `int`) `const`

Gets the suffix string shown after the column value.

`String` **get_text**(column: `int`) `const`

Returns the given column's text.

`HorizontalAlignment` **get_text_alignment**(column: `int`) `const`

Returns the given column's text alignment.

`TextDirection` **get_text_direction**(column: `int`) `const`

Returns item's text base writing direction.

`OverrunBehavior` **get_text_overrun_behavior**(column: `int`) `const`

Returns the clipping behavior when the text exceeds the item's bounding rectangle in the given `column`. By default it is `TextServer.OVERRUN_TRIM_ELLIPSIS`.

`String` **get_tooltip_text**(column: `int`) `const`

Returns the given column's tooltip text.

`Tree` **get_tree**() `const`

Returns the `Tree` that owns this TreeItem.

`bool` **is_accepting_children**() `const`

Returns `true` if this **TreeItem** is allowed to accept children.

`bool` **is_any_collapsed**(only_visible: `bool` = false)

Returns `true` if this **TreeItem**, or any of its descendants, is collapsed.

If `only_visible` is `true` it ignores non-visible **TreeItem**s.

`bool` **is_button_disabled**(column: `int`, button_index: `int`) `const`

Returns `true` if the button at index `button_index` for the given `column` is disabled.

`bool` **is_checked**(column: `int`) `const`

Returns `true` if the given `column` is checked.

`bool` **is_custom_set_as_button**(column: `int`) `const`

Returns `true` if the cell was made into a button with `set_custom_as_button()`.

`bool` **is_edit_multiline**(column: `int`) `const`

Returns `true` if the given `column` is multiline editable.

`bool` **is_editable**(column: `int`)

Returns `true` if the given `column` is editable.

`bool` **is_indeterminate**(column: `int`) `const`

Returns `true` if the given `column` is indeterminate.

`bool` **is_selectable**(column: `int`) `const`

Returns `true` if the given `column` is selectable.

`bool` **is_selected**(column: `int`)

Returns `true` if the given `column` is selected.

`bool` **is_visible_in_tree**() `const`

Returns `true` if `visible` is `true` and all its ancestors are also visible.

`void (No return value.)` **move_after**(item: `TreeItem`)

Moves this TreeItem right after the given `item`.

**Note:** You can't move to the root or move the root.

`void (No return value.)` **move_before**(item: `TreeItem`)

Moves this TreeItem right before the given `item`.

**Note:** You can't move to the root or move the root.

`void (No return value.)` **propagate_check**(column: `int`, emit_signal: `bool` = true)

Propagates this item's checked status to its children and parents for the given `column`. It is possible to process the items affected by this method call by connecting to `Tree.check_propagated_to_item`. The order that the items affected will be processed is as follows: the item invoking this method, children of that item, and finally parents of that item. If `emit_signal` is `false`, then `Tree.check_propagated_to_item` will not be emitted.

`void (No return value.)` **remove_child**(child: `TreeItem`)

Removes the given child **TreeItem** and all its children from the `Tree`. Note that it doesn't free the item from memory, so it can be reused later (see `add_child()`). To completely remove a **TreeItem** use `Object.free()`.

**Note:** If you want to move a child from one `Tree` to another, then instead of removing and adding it manually you can use `move_before()` or `move_after()`.

`void (No return value.)` **select**(column: `int`, set_as_cursor: `bool` = true)

Selects the given `column`. If `set_as_cursor` is `true`, the `Tree`'s cursor will be moved to this item (only matters if `Tree.select_mode` is set to `Tree.SELECT_MULTI`).

`void (No return value.)` **set_accept_children**(allowed: `bool`)

Sets **TreeItem**'s ability to accept children.

`void (No return value.)` **set_auto_translate_mode**(column: `int`, mode: `AutoTranslateMode`)

Sets the given column's auto translate mode to `mode`.

All columns use `Node.AUTO_TRANSLATE_MODE_INHERIT` by default, which uses the same auto translate mode as the `Tree` itself.

`void (No return value.)` **set_autowrap_mode**(column: `int`, autowrap_mode: `AutowrapMode`)

Sets the autowrap mode in the given `column`. If set to something other than `TextServer.AUTOWRAP_OFF`, the text gets wrapped inside the cell's bounding rectangle.

`void (No return value.)` **set_autowrap_trim_flags**(column: `int`, flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\])

Sets the autowrap trim flags for the given `column`. These flags control whether leading and trailing spaces are trimmed on wrapped lines. Set to `0` to disable all trimming.

`void (No return value.)` **set_button**(column: `int`, button_index: `int`, button: `Texture2D`)

Sets the given column's button `Texture2D` at index `button_index` to `button`.

`void (No return value.)` **set_button_color**(column: `int`, button_index: `int`, color: `Color`)

Sets the given column's button color at index `button_index` to `color`.

`void (No return value.)` **set_button_description**(column: `int`, button_index: `int`, description: `String`)

Sets the given column's button description at index `button_index` for assistive apps.

`void (No return value.)` **set_button_disabled**(column: `int`, button_index: `int`, disabled: `bool`)

If `true`, disables the button at index `button_index` in the given `column`.

`void (No return value.)` **set_button_tooltip_text**(column: `int`, button_index: `int`, tooltip: `String`)

Sets the tooltip text for the button at index `button_index` in the given `column`.

`void (No return value.)` **set_cell_mode**(column: `int`, mode: `TreeCellMode`)

Sets the given column's cell mode to `mode`. This determines how the cell is displayed and edited.

`void (No return value.)` **set_checked**(column: `int`, checked: `bool`)

If `checked` is `true`, the given `column` is checked. Clears column's indeterminate status.

`void (No return value.)` **set_collapsed_recursive**(enable: `bool`)

Collapses or uncollapses this **TreeItem** and all the descendants of this item.

`void (No return value.)` **set_custom_as_button**(column: `int`, enable: `bool`)

Makes a cell with `CELL_MODE_CUSTOM` display as a non-flat button with a `StyleBox`.

`void (No return value.)` **set_custom_bg_color**(column: `int`, color: `Color`, just_outline: `bool` = false)

Sets the given column's custom background color and whether to just use it as an outline.

**Note:** If a custom `StyleBox` is set, the background color will be drawn behind it.

`void (No return value.)` **set_custom_color**(column: `int`, color: `Color`)

Sets the given column's custom color.

`void (No return value.)` **set_custom_draw**(column: `int`, object: `Object`, callback: `StringName`)

**Deprecated:** Use `set_custom_draw_callback()` instead.

Sets the given column's custom draw callback to the `callback` method on `object`.

The method named `callback` should accept two arguments: the **TreeItem** that is drawn and its position and size as a `Rect2`.

`void (No return value.)` **set_custom_draw_callback**(column: `int`, callback: `Callable`)

Sets the given column's custom draw callback. Use an empty `Callable` (`Callable()`) to clear the custom callback. The cell has to be in `CELL_MODE_CUSTOM` to use this feature.

The `callback` should accept two arguments: the **TreeItem** that is drawn and its position and size as a `Rect2`.

To draw custom content over the native style, please use `Tree.get_custom_drawing_canvas_item()`.

`void (No return value.)` **set_custom_font**(column: `int`, font: `Font`)

Sets custom font used to draw text in the given `column`.

`void (No return value.)` **set_custom_font_size**(column: `int`, font_size: `int`)

Sets custom font size used to draw text in the given `column`.

`void (No return value.)` **set_custom_stylebox**(column: `int`, stylebox: `StyleBox`)

Sets the given column's custom `StyleBox` used to draw the background.

**Note:** If a custom background color is set, the `StyleBox` will be drawn in front of it.

`void (No return value.)` **set_description**(column: `int`, description: `String`)

Sets the given column's description for assistive apps.

`void (No return value.)` **set_edit_multiline**(column: `int`, multiline: `bool`)

If `multiline` is `true`, the given `column` is multiline editable.

**Note:** This option only affects the type of control (`LineEdit` or `TextEdit`) that appears when editing the column. You can set multiline values with `set_text()` even if the column is not multiline editable.

`void (No return value.)` **set_editable**(column: `int`, enabled: `bool`)

If `enabled` is `true`, the given `column` is editable.

`void (No return value.)` **set_expand_right**(column: `int`, enable: `bool`)

If `enable` is `true`, the given `column` is expanded to the right.

`void (No return value.)` **set_icon**(column: `int`, texture: `Texture2D`)

Sets the given cell's icon `Texture2D`. If the cell is in `CELL_MODE_ICON` mode, the icon is displayed in the center of the cell. Otherwise, the icon is displayed before the cell's text. `CELL_MODE_RANGE` does not display an icon.

`void (No return value.)` **set_icon_max_width**(column: `int`, width: `int`)

Sets the maximum allowed width of the icon in the given `column`. This limit is applied on top of the default size of the icon and on top of `Tree.icon_max_width`. The height is adjusted according to the icon's ratio.

`void (No return value.)` **set_icon_modulate**(column: `int`, modulate: `Color`)

Modulates the given column's icon with `modulate`.

`void (No return value.)` **set_icon_overlay**(column: `int`, texture: `Texture2D`)

Sets the given cell's icon overlay `Texture2D`. The cell has to be in `CELL_MODE_ICON` mode, and icon has to be set. Overlay is drawn on top of icon, in the bottom left corner.

`void (No return value.)` **set_icon_region**(column: `int`, region: `Rect2`)

Sets the given column's icon's texture region.

`void (No return value.)` **set_indeterminate**(column: `int`, indeterminate: `bool`)

If `indeterminate` is `true`, the given `column` is marked indeterminate.

**Note:** If set `true` from `false`, then column is cleared of checked status.

`void (No return value.)` **set_language**(column: `int`, language: `String`)

Sets the language code of the given `column`'s text to `language`. This is used for line-breaking and text shaping algorithms. If `language` is empty, the current locale is used.

`void (No return value.)` **set_metadata**(column: `int`, meta: `Variant`)

Sets the metadata value for the given column, which can be retrieved later using `get_metadata()`. This can be used, for example, to store a reference to the original data.

`void (No return value.)` **set_range**(column: `int`, value: `float`)

Sets the value of a `CELL_MODE_RANGE` column.

`void (No return value.)` **set_range_config**(column: `int`, min: `float`, max: `float`, step: `float`, expr: `bool` = false)

Sets the range of accepted values for a column. The column must be in the `CELL_MODE_RANGE` mode.

If `expr` is `true`, the edit mode slider will use an exponential scale as with `Range.exp_edit`.

`void (No return value.)` **set_selectable**(column: `int`, selectable: `bool`)

If `selectable` is `true`, the given `column` is selectable.

`void (No return value.)` **set_structured_text_bidi_override**(column: `int`, parser: `StructuredTextParser`)

Set BiDi algorithm override for the structured text. Has effect for cells that display text.

`void (No return value.)` **set_structured_text_bidi_override_options**(column: `int`, args: `Array`)

Set additional options for BiDi override. Has effect for cells that display text.

`void (No return value.)` **set_suffix**(column: `int`, text: `String`)

Sets a string to be shown after a column's value (for example, a unit abbreviation).

`void (No return value.)` **set_text**(column: `int`, text: `String`)

Sets the given column's text value.

`void (No return value.)` **set_text_alignment**(column: `int`, text_alignment: `HorizontalAlignment`)

Sets the given column's text alignment to `text_alignment`.

`void (No return value.)` **set_text_direction**(column: `int`, direction: `TextDirection`)

Sets item's text base writing direction.

`void (No return value.)` **set_text_overrun_behavior**(column: `int`, overrun_behavior: `OverrunBehavior`)

Sets the clipping behavior when the text exceeds the item's bounding rectangle in the given `column`.

`void (No return value.)` **set_tooltip_text**(column: `int`, tooltip: `String`)

Sets the given column's tooltip text.

`void (No return value.)` **uncollapse_tree**()

Uncollapses all **TreeItem**s necessary to reveal this **TreeItem**, i.e. all ancestor **TreeItem**s.