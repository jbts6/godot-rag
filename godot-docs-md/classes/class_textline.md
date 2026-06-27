# TextLine

**Inherits:** `RefCounted` **<** `Object`

Holds a line of text.

## Description

Abstraction over `TextServer` for handling a single line of text.

## Property Descriptions

`HorizontalAlignment` **alignment** = `0`

- `void (No return value.)` **set_horizontal_alignment**(value: `HorizontalAlignment`)
- `HorizontalAlignment` **get_horizontal_alignment**()

Sets text alignment within the line as if the line was horizontal.

`Direction` **direction** = `0`

- `void (No return value.)` **set_direction**(value: `Direction`)
- `Direction` **get_direction**()

Text writing direction.

`String` **ellipsis_char** = `"…"`

- `void (No return value.)` **set_ellipsis_char**(value: `String`)
- `String` **get_ellipsis_char**()

Ellipsis character used for text clipping.

`BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\] **flags** = `3`

- `void (No return value.)` **set_flags**(value: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\])
- `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\] **get_flags**()

Line alignment rules. For more info see `TextServer`.

`Orientation` **orientation** = `0`

- `void (No return value.)` **set_orientation**(value: `Orientation`)
- `Orientation` **get_orientation**()

Text orientation.

`bool` **preserve_control** = `false`

- `void (No return value.)` **set_preserve_control**(value: `bool`)
- `bool` **get_preserve_control**()

If set to `true` text will display control characters.

`bool` **preserve_invalid** = `true`

- `void (No return value.)` **set_preserve_invalid**(value: `bool`)
- `bool` **get_preserve_invalid**()

If set to `true` text will display invalid characters.

`OverrunBehavior` **text_overrun_behavior** = `3`

- `void (No return value.)` **set_text_overrun_behavior**(value: `OverrunBehavior`)
- `OverrunBehavior` **get_text_overrun_behavior**()

The clipping behavior when the text exceeds the text line's set width.

`float` **width** = `-1.0`

- `void (No return value.)` **set_width**(value: `float`)
- `float` **get_width**()

Text line width.

## Method Descriptions

`bool` **add_object**(key: `Variant`, size: `Vector2`, inline_align: `InlineAlignment` = 5, length: `int` = 1, baseline: `float` = 0.0)

Adds inline object to the text buffer, `key` must be unique. In the text, object is represented as `length` object replacement characters.

`bool` **add_string**(text: `String`, font: `Font`, font_size: `int`, language: `String` = "", meta: `Variant` = null)

Adds text span and font to draw it.

`void (No return value.)` **clear**()

Clears text line (removes text and inline objects).

`void (No return value.)` **draw**(canvas: `RID`, pos: `Vector2`, color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw text into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **draw_outline**(canvas: `RID`, pos: `Vector2`, outline_size: `int` = 1, color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw text into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`TextLine` **duplicate**() `const`

Duplicates this **TextLine**.

`Direction` **get_inferred_direction**() `const`

Returns the text writing direction inferred by the BiDi algorithm.

`float` **get_line_ascent**() `const`

Returns the text ascent (number of pixels above the baseline for horizontal layout or to the left of baseline for vertical).

`float` **get_line_descent**() `const`

Returns the text descent (number of pixels below the baseline for horizontal layout or to the right of baseline for vertical).

`float` **get_line_underline_position**() `const`

Returns pixel offset of the underline below the baseline.

`float` **get_line_underline_thickness**() `const`

Returns thickness of the underline.

`float` **get_line_width**() `const`

Returns width (for horizontal layout) or height (for vertical) of the text.

`Rect2` **get_object_rect**(key: `Variant`) `const`

Returns bounding rectangle of the inline object.

`Array` **get_objects**() `const`

Returns array of inline objects.

`RID` **get_rid**() `const`

Returns TextServer buffer RID.

`Vector2` **get_size**() `const`

Returns size of the bounding box of the text.

`bool` **has_object**(key: `Variant`) `const`

Returns `true` if an object with `key` is embedded in this line.

`int` **hit_test**(coords: `float`) `const`

Returns caret character offset at the specified pixel offset at the baseline. This function always returns a valid position.

`bool` **resize_object**(key: `Variant`, size: `Vector2`, inline_align: `InlineAlignment` = 5, baseline: `float` = 0.0)

Sets new size and alignment of embedded object.

`void (No return value.)` **set_bidi_override**(override: `Array`)

Overrides BiDi for the structured text.

Override ranges should cover full source text without overlaps. BiDi algorithm will be used on each range separately.

`void (No return value.)` **tab_align**(tab_stops: `PackedFloat32Array`)

Aligns text to the given tab-stops.