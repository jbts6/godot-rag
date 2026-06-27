# OptionButton

**Inherits:** `Button` **<** `BaseButton` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`

A button that brings up a dropdown with selectable options when pressed.

## Description

**OptionButton** is a type of button that brings up a dropdown with selectable items when pressed. The item selected becomes the "current" item and is displayed as the button text.

See also `BaseButton` which contains common properties and methods associated with this node.

**Note:** The IDs used for items are limited to signed 32-bit integers, not the full 64 bits of `int`. These have a range of `-2^31` to `2^31 - 1`, that is, `-2147483648` to `2147483647`.

**Note:** The `Button.text` and `Button.icon` properties are set automatically based on the selected item. They shouldn't be changed manually.

## Theme Properties

## Signals

**item_focused**(index: `int`)

Emitted when the user navigates to an item using the `ProjectSettings.input/ui_up` or `ProjectSettings.input/ui_down` input actions. The index of the item focused is passed as argument.

**item_selected**(index: `int`)

Emitted when the current item has been changed by the user. The index of the item selected is passed as argument.

`allow_reselect` must be enabled to reselect an item.

## Property Descriptions

`bool` **allow_reselect** = `false`

- `void (No return value.)` **set_allow_reselect**(value: `bool`)
- `bool` **get_allow_reselect**()

If `true`, the currently selected item can be selected again.

`bool` **fit_to_longest_item** = `true`

- `void (No return value.)` **set_fit_to_longest_item**(value: `bool`)
- `bool` **is_fit_to_longest_item**()

If `true`, minimum size will be determined by the longest item's text, instead of the currently selected one's.

**Note:** For performance reasons, the minimum size doesn't update immediately when adding, removing or modifying items.

`int` **item_count** = `0`

- `void (No return value.)` **set_item_count**(value: `int`)
- `int` **get_item_count**()

The number of items to select from.

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

`bool` **search_bar_enabled** = `false`

- `void (No return value.)` **set_search_bar_enabled**(value: `bool`)
- `bool` **is_search_bar_enabled**()

If `true`, shows a search bar at the top of the `PopupMenu` for filtering items. See `search_bar_min_item_count` for dynamically controlling its visibility based on the number of items.

`bool` **search_bar_fuzzy_search_enabled** = `true`

- `void (No return value.)` **set_search_bar_fuzzy_search_enabled**(value: `bool`)
- `bool` **is_search_bar_fuzzy_search_enabled**()

If `true`, enables fuzzy searching in the `PopupMenu` search bar. This allows the search results to include items that almost match the search query, as well items that match the individual characters of the search query, but not in sequence.

Use `search_bar_fuzzy_search_max_misses` to set the maximum number of mismatches allowed in the search results.

`int` **search_bar_fuzzy_search_max_misses** = `2`

- `void (No return value.)` **set_search_bar_fuzzy_search_max_misses**(value: `int`)
- `int` **get_search_bar_fuzzy_search_max_misses**()

Sets the maximum number of mismatches allowed in each search result when fuzzy searching is enabled for the `PopupMenu` search bar. Any item with more mismatches will be hidden from the search results.

`int` **search_bar_min_item_count** = `0`

- `void (No return value.)` **set_search_bar_min_item_count**(value: `int`)
- `int` **get_search_bar_min_item_count**()

Sets the minimum number of items required for the `PopupMenu` search bar to be visible. `search_bar_enabled` must be `true` for this to have any effect.

`int` **selected** = `-1`

- `int` **get_selected**()

The index of the currently selected item, or `-1` if no item is selected.

## Method Descriptions

`void (No return value.)` **add_icon_item**(texture: `Texture2D`, label: `String`, id: `int` = -1)

Adds an item, with a `texture` icon, text `label` and (optionally) `id`. If no `id` is passed, the item index will be used as the item's ID. New items are appended at the end.

**Note:** The item will be selected if there are no other items.

`void (No return value.)` **add_item**(label: `String`, id: `int` = -1)

Adds an item, with text `label` and (optionally) `id`. If no `id` is passed, the item index will be used as the item's ID. New items are appended at the end.

**Note:** The item will be selected if there are no other items.

`void (No return value.)` **add_separator**(text: `String` = "")

Adds a separator to the list of items. Separators help to group items, and can optionally be given a `text` header. A separator also gets an index assigned, and is appended at the end of the item list.

`void (No return value.)` **clear**()

Clears all the items in the **OptionButton**.

`AutoTranslateMode` **get_item_auto_translate_mode**(idx: `int`) `const`

Returns the auto translate mode of the item at index `idx`.

`Texture2D` **get_item_icon**(idx: `int`) `const`

Returns the icon of the item at index `idx`.

`int` **get_item_id**(idx: `int`) `const`

Returns the ID of the item at index `idx`.

`int` **get_item_index**(id: `int`) `const`

Returns the index of the item with the given `id`.

`Variant` **get_item_metadata**(idx: `int`) `const`

Retrieves the metadata of an item. Metadata may be any type and can be used to store extra information about an item, such as an external string ID.

`String` **get_item_text**(idx: `int`) `const`

Returns the text of the item at index `idx`.

`String` **get_item_tooltip**(idx: `int`) `const`

Returns the tooltip of the item at index `idx`.

`PopupMenu` **get_popup**() `const`

Returns the `PopupMenu` contained in this button.

**Warning:** This is a required internal node, removing and freeing it may cause a crash. If you wish to hide it or any of its children, use their `Window.visible` property.

`int` **get_selectable_item**(from_last: `bool` = false) `const`

Returns the index of the first item which is not disabled, or marked as a separator. If `from_last` is `true`, the items will be searched in reverse order.

Returns `-1` if no item is found.

`int` **get_selected_id**() `const`

Returns the ID of the selected item, or `-1` if no item is selected.

`Variant` **get_selected_metadata**() `const`

Gets the metadata of the selected item. Metadata for items can be set using `set_item_metadata()`.

`bool` **has_selectable_items**() `const`

Returns `true` if this button contains at least one item which is not disabled, or marked as a separator.

`bool` **is_item_disabled**(idx: `int`) `const`

Returns `true` if the item at index `idx` is disabled.

`bool` **is_item_separator**(idx: `int`) `const`

Returns `true` if the item at index `idx` is marked as a separator.

`void (No return value.)` **remove_item**(idx: `int`)

Removes the item at index `idx`.

`void (No return value.)` **select**(idx: `int`)

Selects an item by index and makes it the current item. This will work even if the item is disabled.

Passing `-1` as the index deselects any currently selected item.

`void (No return value.)` **set_disable_shortcuts**(disabled: `bool`)

If `true`, shortcuts are disabled and cannot be used to trigger the button.

`void (No return value.)` **set_item_auto_translate_mode**(idx: `int`, mode: `AutoTranslateMode`)

Sets the auto translate mode of the item at index `idx`.

Items use `Node.AUTO_TRANSLATE_MODE_INHERIT` by default, which uses the same auto translate mode as the **OptionButton** itself.

`void (No return value.)` **set_item_disabled**(idx: `int`, disabled: `bool`)

Sets whether the item at index `idx` is disabled.

Disabled items are drawn differently in the dropdown and are not selectable by the user. If the current selected item is set as disabled, it will remain selected.

`void (No return value.)` **set_item_icon**(idx: `int`, texture: `Texture2D`)

Sets the icon of the item at index `idx`.

`void (No return value.)` **set_item_id**(idx: `int`, id: `int`)

Sets the ID of the item at index `idx`.

`void (No return value.)` **set_item_metadata**(idx: `int`, metadata: `Variant`)

Sets the metadata of an item. Metadata may be of any type and can be used to store extra information about an item, such as an external string ID.

`void (No return value.)` **set_item_text**(idx: `int`, text: `String`)

Sets the text of the item at index `idx`.

`void (No return value.)` **set_item_tooltip**(idx: `int`, tooltip: `String`)

Sets the tooltip of the item at index `idx`.

`void (No return value.)` **show_popup**()

Adjusts popup position and sizing for the **OptionButton**, then shows the `PopupMenu`. Prefer this over using `get_popup().popup()`.

## Theme Property Descriptions

`int` **arrow_margin** = `4`

The horizontal space between the arrow icon and the right edge of the button.

`int` **modulate_arrow** = `0`

If different than `0`, the arrow icon will be modulated to the font color.

`Texture2D` **arrow**

The arrow icon to be drawn on the right end of the button.