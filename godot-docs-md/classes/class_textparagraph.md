# TextParagraph

**Inherits:** `RefCounted` **<** `Object`

Holds a paragraph of text.

## Description

Abstraction over `TextServer` for handling a single paragraph of text.

## Property Descriptions

`HorizontalAlignment` **alignment** = `0`

- `void (No return value.)` **set_alignment**(value: `HorizontalAlignment`)
- `HorizontalAlignment` **get_alignment**()

Paragraph horizontal alignment.

`BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\] **break_flags** = `3`

- `void (No return value.)` **set_break_flags**(value: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\])
- `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\] **get_break_flags**()

Line breaking rules. For more info see `TextServer`.

`String` **custom_punctuation** = `""`

- `void (No return value.)` **set_custom_punctuation**(value: `String`)
- `String` **get_custom_punctuation**()

Custom punctuation character list, used for word breaking. If set to empty string, server defaults are used.

`Direction` **direction** = `0`

- `void (No return value.)` **set_direction**(value: `Direction`)
- `Direction` **get_direction**()

Text writing direction.

`String` **ellipsis_char** = `"…"`

- `void (No return value.)` **set_ellipsis_char**(value: `String`)
- `String` **get_ellipsis_char**()

Ellipsis character used for text clipping.

`BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\] **justification_flags** = `163`

- `void (No return value.)` **set_justification_flags**(value: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\])
- `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\] **get_justification_flags**()

Line fill alignment rules.

`float` **line_spacing** = `0.0`

- `void (No return value.)` **set_line_spacing**(value: `float`)
- `float` **get_line_spacing**()

Additional vertical spacing between lines (in pixels), spacing is added to line descent. This value can be negative.

`int` **max_lines_visible** = `-1`

- `void (No return value.)` **set_max_lines_visible**(value: `int`)
- `int` **get_max_lines_visible**()

Limits the lines of text shown.

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

`OverrunBehavior` **text_overrun_behavior** = `0`

- `void (No return value.)` **set_text_overrun_behavior**(value: `OverrunBehavior`)
- `OverrunBehavior` **get_text_overrun_behavior**()

The clipping behavior when the text exceeds the paragraph's set width.

`float` **width** = `-1.0`

- `void (No return value.)` **set_width**(value: `float`)
- `float` **get_width**()

Paragraph width.

## Method Descriptions

`bool` **add_object**(key: `Variant`, size: `Vector2`, inline_align: `InlineAlignment` = 5, length: `int` = 1, baseline: `float` = 0.0)

Adds inline object to the text buffer, `key` must be unique. In the text, object is represented as `length` object replacement characters.

`bool` **add_string**(text: `String`, font: `Font`, font_size: `int`, language: `String` = "", meta: `Variant` = null)

Adds text span and font to draw it.

`void (No return value.)` **clear**()

Clears text paragraph (removes text and inline objects).

`void (No return value.)` **clear_dropcap**()

Removes dropcap.

`void (No return value.)` **draw**(canvas: `RID`, pos: `Vector2`, color: `Color` = Color(1, 1, 1, 1), dc_color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw all lines of the text and drop cap into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **draw_dropcap**(canvas: `RID`, pos: `Vector2`, color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw drop cap into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **draw_dropcap_outline**(canvas: `RID`, pos: `Vector2`, outline_size: `int` = 1, color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw drop cap outline into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **draw_line**(canvas: `RID`, pos: `Vector2`, line: `int`, color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw single line of text into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **draw_line_outline**(canvas: `RID`, pos: `Vector2`, line: `int`, outline_size: `int` = 1, color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw outline of the single line of text into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **draw_outline**(canvas: `RID`, pos: `Vector2`, outline_size: `int` = 1, color: `Color` = Color(1, 1, 1, 1), dc_color: `Color` = Color(1, 1, 1, 1), oversampling: `float` = 0.0) `const`

Draw outlines of all lines of the text and drop cap into a canvas item at a given position, with `color`. `pos` specifies the top left corner of the bounding box. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`TextParagraph` **duplicate**() `const`

Duplicates this **TextParagraph**.

`int` **get_dropcap_lines**() `const`

Returns number of lines used by dropcap.

`RID` **get_dropcap_rid**() `const`

Returns drop cap text buffer RID.

`Vector2` **get_dropcap_size**() `const`

Returns drop cap bounding box size.

`Direction` **get_inferred_direction**() `const`

Returns the text writing direction inferred by the BiDi algorithm.

`float` **get_line_ascent**(line: `int`) `const`

Returns the text line ascent (number of pixels above the baseline for horizontal layout or to the left of baseline for vertical).

`int` **get_line_count**() `const`

Returns number of lines in the paragraph.

`float` **get_line_descent**(line: `int`) `const`

Returns the text line descent (number of pixels below the baseline for horizontal layout or to the right of baseline for vertical).

`Rect2` **get_line_object_rect**(line: `int`, key: `Variant`) `const`

Returns bounding rectangle of the inline object.

`Array` **get_line_objects**(line: `int`) `const`

Returns array of inline objects in the line.

`Vector2i` **get_line_range**(line: `int`) `const`

Returns character range of the line.

`RID` **get_line_rid**(line: `int`) `const`

Returns TextServer line buffer RID.

`Vector2` **get_line_size**(line: `int`) `const`

Returns size of the bounding box of the line of text. Returned size is rounded up.

`float` **get_line_underline_position**(line: `int`) `const`

Returns pixel offset of the underline below the baseline.

`float` **get_line_underline_thickness**(line: `int`) `const`

Returns thickness of the underline.

`float` **get_line_width**(line: `int`) `const`

Returns width (for horizontal layout) or height (for vertical) of the line of text.

`Vector2` **get_non_wrapped_size**() `const`

Returns the size of the bounding box of the paragraph, without line breaks.

`Vector2i` **get_range**() `const`

Returns the character range of the paragraph.

`RID` **get_rid**() `const`

Returns TextServer full string buffer RID.

`Vector2` **get_size**() `const`

Returns the size of the bounding box of the paragraph.

`bool` **has_object**(key: `Variant`) `const`

Returns `true` if an object with `key` is embedded in this shaped text buffer.

`int` **hit_test**(coords: `Vector2`) `const`

Returns caret character offset at the specified coordinates. This function always returns a valid position.

`bool` **resize_object**(key: `Variant`, size: `Vector2`, inline_align: `InlineAlignment` = 5, baseline: `float` = 0.0)

Sets new size and alignment of embedded object.

`void (No return value.)` **set_bidi_override**(override: `Array`)

Overrides BiDi for the structured text.

Override ranges should cover full source text without overlaps. BiDi algorithm will be used on each range separately.

`bool` **set_dropcap**(text: `String`, font: `Font`, font_size: `int`, dropcap_margins: `Rect2` = Rect2(0, 0, 0, 0), language: `String` = "")

Sets drop cap, overrides previously set drop cap. Drop cap (dropped capital) is a decorative element at the beginning of a paragraph that is larger than the rest of the text.

`void (No return value.)` **tab_align**(tab_stops: `PackedFloat32Array`)

Aligns paragraph to the given tab-stops.