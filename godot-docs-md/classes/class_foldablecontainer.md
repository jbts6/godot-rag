# FoldableContainer

**Inherits:** `Container` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`

A container that can be expanded/collapsed.

## Description

A container that can be expanded/collapsed, with a title that can be filled with controls, such as buttons. This is also called an accordion.

The title can be positioned at the top or bottom of the container. The container can be expanded or collapsed by clicking the title or by pressing `ui_accept` when focused. Child control nodes are hidden when the container is collapsed. Ignores non-control children.

A FoldableContainer can be grouped with other FoldableContainers so that only one of them can be opened at a time; see `foldable_group` and `FoldableGroup`.

## Theme Properties

## Signals

**folding_changed**(is_folded: `bool`)

Emitted when the container is folded/expanded.

## Enumerations

enum **TitlePosition**:

`TitlePosition` **POSITION_TOP** = `0`

Makes the title appear at the top of the container.

`TitlePosition` **POSITION_BOTTOM** = `1`

Makes the title appear at the bottom of the container. Also makes all StyleBoxes flipped vertically.

## Property Descriptions

`FoldableGroup` **foldable_group**

- `void (No return value.)` **set_foldable_group**(value: `FoldableGroup`)
- `FoldableGroup` **get_foldable_group**()

The `FoldableGroup` associated with the container. When multiple **FoldableContainer** nodes share the same group, only one of them is allowed to be unfolded.

`bool` **folded** = `false`

- `void (No return value.)` **set_folded**(value: `bool`)
- `bool` **is_folded**()

If `true`, the container will become folded and will hide all its children.

`String` **language** = `""`

- `void (No return value.)` **set_language**(value: `String`)
- `String` **get_language**()

Language code used for text shaping algorithms. If left empty, the current locale is used instead.

`String` **title** = `""`

- `void (No return value.)` **set_title**(value: `String`)
- `String` **get_title**()

The container's title text.

`HorizontalAlignment` **title_alignment** = `0`

- `void (No return value.)` **set_title_alignment**(value: `HorizontalAlignment`)
- `HorizontalAlignment` **get_title_alignment**()

Title's horizontal text alignment.

`TitlePosition` **title_position** = `0`

- `void (No return value.)` **set_title_position**(value: `TitlePosition`)
- `TitlePosition` **get_title_position**()

Title's position.

`TextDirection` **title_text_direction** = `0`

- `void (No return value.)` **set_title_text_direction**(value: `TextDirection`)
- `TextDirection` **get_title_text_direction**()

Title text writing direction.

`OverrunBehavior` **title_text_overrun_behavior** = `0`

- `void (No return value.)` **set_title_text_overrun_behavior**(value: `OverrunBehavior`)
- `OverrunBehavior` **get_title_text_overrun_behavior**()

Defines the behavior of the title when the text is longer than the available space.

## Method Descriptions

`void (No return value.)` **add_title_bar_control**(control: `Control`)

Adds a `Control` that will be placed next to the container's title, obscuring the clickable area. Prime usage is adding `Button` nodes, but it can be any `Control`.

The control will be added as a child of this container and removed from previous parent if necessary. The controls will be placed aligned to the right, with the first added control being the leftmost one.

`void (No return value.)` **expand**()

Expands the container and emits `folding_changed`.

`void (No return value.)` **fold**()

Folds the container and emits `folding_changed`.

`void (No return value.)` **remove_title_bar_control**(control: `Control`)

Removes a `Control` added with `add_title_bar_control()`. The node is not freed automatically, you need to use `Node.queue_free()`.

## Theme Property Descriptions

`Color` **collapsed_font_color** = `Color(1, 1, 1, 1)`

The title's font color when collapsed.

`Color` **font_color** = `Color(0.875, 0.875, 0.875, 1)`

The title's font color when expanded.

`Color` **font_outline_color** = `Color(1, 1, 1, 1)`

The title's font outline color.

`Color` **hover_font_color** = `Color(0.95, 0.95, 0.95, 1)`

The title's font hover color.

`int` **h_separation** = `2`

The horizontal separation between the title's icon and text, and between title bar controls.

`int` **outline_size** = `0`

The title's font outline size.

`Font` **font**

The title's font.

`int` **font_size**

The title's font size.

`Texture2D` **expanded_arrow**

The title's icon used when expanded.

`Texture2D` **expanded_arrow_mirrored**

The title's icon used when expanded (for bottom title).

`Texture2D` **folded_arrow**

The title's icon used when folded (for left-to-right layouts).

`Texture2D` **folded_arrow_mirrored**

The title's icon used when collapsed (for right-to-left layouts).

`StyleBox` **focus**

Background used when **FoldableContainer** has GUI focus. The `focus` `StyleBox` is displayed *over* the base `StyleBox`, so a partially transparent `StyleBox` should be used to ensure the base `StyleBox` remains visible. A `StyleBox` that represents an outline or an underline works well for this purpose. To disable the focus visual effect, assign a `StyleBoxEmpty` resource. Note that disabling the focus visual effect will harm keyboard/controller navigation usability, so this is not recommended for accessibility reasons.

`StyleBox` **panel**

Default background for the **FoldableContainer**.

`StyleBox` **title_collapsed_hover_panel**

Background used when the mouse cursor enters the title's area when collapsed.

`StyleBox` **title_collapsed_panel**

Default background for the **FoldableContainer**'s title when collapsed.

`StyleBox` **title_hover_panel**

Background used when the mouse cursor enters the title's area when expanded.

`StyleBox` **title_panel**

Default background for the **FoldableContainer**'s title when expanded.