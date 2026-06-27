# TextServerExtension

**Inherits:** `TextServer` **<** `RefCounted` **<** `Object`

**Inherited By:** `TextServerAdvanced`, `TextServerDummy`, `TextServerFallback`

Base class for custom `TextServer` implementations (plugins).

## Description

External `TextServer` implementations should inherit from this class.

## Method Descriptions

`void (No return value.)` **\_cleanup**() `virtual (This method should typically be overridden by the user to have any effect.)`

This method is called before text server is unregistered.

`RID` **\_create_font**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Creates a new, empty font cache entry resource.

`RID` **\_create_font_linked_variation**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)`

Optional, implement if font supports extra spacing or baseline offset.

Creates a new variation existing font which is reusing the same glyph cache and font data.

`RID` **\_create_shaped_text**(direction: `Direction`, orientation: `Orientation`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Creates a new buffer for complex text layout, with the given `direction` and `orientation`.

`void (No return value.)` **\_draw_hex_code_box**(canvas: `RID`, size: `int`, pos: `Vector2`, index: `int`, color: `Color`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Draws box displaying character hexadecimal code.

`void (No return value.)` **\_font_clear_glyphs**(font_rid: `RID`, size: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Removes all rendered glyph information from the cache entry.

`void (No return value.)` **\_font_clear_kerning_map**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Removes all kerning overrides.

`void (No return value.)` **\_font_clear_size_cache**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Removes all font sizes from the cache entry.

`void (No return value.)` **\_font_clear_system_fallback_cache**() `virtual (This method should typically be overridden by the user to have any effect.)`

Frees all automatically loaded system fonts.

`void (No return value.)` **\_font_clear_textures**(font_rid: `RID`, size: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Removes all textures from font cache entry.

`void (No return value.)` **\_font_draw_glyph**(font_rid: `RID`, canvas: `RID`, size: `int`, pos: `Vector2`, index: `int`, color: `Color`, oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Draws single glyph into a canvas item at the position, using `font_rid` at the size `size`. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **\_font_draw_glyph_outline**(font_rid: `RID`, canvas: `RID`, size: `int`, outline_size: `int`, pos: `Vector2`, index: `int`, color: `Color`, oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Draws single glyph outline of size `outline_size` into a canvas item at the position, using `font_rid` at the size `size`. If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`FontAntialiasing` **\_font_get_antialiasing**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font anti-aliasing mode.

`float` **\_font_get_ascent**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the font ascent (number of pixels above the baseline).

`float` **\_font_get_baseline_offset**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns extra baseline offset (as a fraction of font height).

`int` **\_font_get_char_from_glyph_index**(font_rid: `RID`, size: `int`, glyph_index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns character code associated with `glyph_index`, or `0` if `glyph_index` is invalid.

`float` **\_font_get_descent**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the font descent (number of pixels below the baseline).

`bool` **\_font_get_disable_embedded_bitmaps**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns whether the font's embedded bitmap loading is disabled.

`float` **\_font_get_embolden**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font embolden strength.

`int` **\_font_get_face_count**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns number of faces in the TrueType / OpenType collection.

`int` **\_font_get_face_index**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns an active face index in the TrueType / OpenType collection.

`int` **\_font_get_fixed_size**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns bitmap font fixed size.

`FixedSizeScaleMode` **\_font_get_fixed_size_scale_mode**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns bitmap font scaling mode.

`bool` **\_font_get_generate_mipmaps**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if font texture mipmap generation is enabled.

`float` **\_font_get_global_oversampling**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the font oversampling factor, shared by all fonts in the TextServer.

`Vector2` **\_font_get_glyph_advance**(font_rid: `RID`, size: `int`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns glyph advance (offset of the next glyph).

`Dictionary` **\_font_get_glyph_contours**(font_rid: `RID`, size: `int`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns outline contours of the glyph.

`int` **\_font_get_glyph_index**(font_rid: `RID`, size: `int`, char: `int`, variation_selector: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the glyph index of a `char`, optionally modified by the `variation_selector`.

`PackedInt32Array` **\_font_get_glyph_list**(font_rid: `RID`, size: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns list of rendered glyphs in the cache entry.

`Vector2` **\_font_get_glyph_offset**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns glyph offset from the baseline.

`Vector2` **\_font_get_glyph_size**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns size of the glyph.

`int` **\_font_get_glyph_texture_idx**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns index of the cache texture containing the glyph.

`RID` **\_font_get_glyph_texture_rid**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns resource ID of the cache texture containing the glyph.

`Vector2` **\_font_get_glyph_texture_size**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns size of the cache texture containing the glyph.

`Rect2` **\_font_get_glyph_uv_rect**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns rectangle in the cache texture containing the glyph.

`Hinting` **\_font_get_hinting**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the font hinting mode. Used by dynamic fonts only.

`bool` **\_font_get_keep_rounding_remainders**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns glyph position rounding behavior. If set to `true`, when aligning glyphs to the pixel boundaries rounding remainders are accumulated to ensure more uniform glyph distribution. This setting has no effect if subpixel positioning is enabled.

`Vector2` **\_font_get_kerning**(font_rid: `RID`, size: `int`, glyph_pair: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns kerning for the pair of glyphs.

`Array`\[`Vector2i`\] **\_font_get_kerning_list**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns list of the kerning overrides.

`bool` **\_font_get_language_support_override**(font_rid: `RID`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Returns `true` if support override is enabled for the `language`.

`PackedStringArray` **\_font_get_language_support_overrides**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)`

Returns list of language support overrides.

`int` **\_font_get_msdf_pixel_range**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the width of the range around the shape between the minimum and maximum representable signed distance.

`int` **\_font_get_msdf_size**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns source font size used to generate MSDF textures.

`String` **\_font_get_name**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font family name.

`Dictionary` **\_font_get_opentype_feature_overrides**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font OpenType feature set override.

`Dictionary` **\_font_get_ot_name_strings**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `Dictionary` with OpenType font name strings (localized font names, version, description, license information, sample text, etc.).

`float` **\_font_get_oversampling**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns oversampling factor override. If set to a positive value, overrides the oversampling factor of the viewport this font is used in. See `Viewport.oversampling`. This value doesn't override the `oversampling` parameter of `draw_*` methods. Used by dynamic fonts only.

`PackedColorArray` **\_font_get_palette_colors**(font_rid: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the array in the predefined color palette at `index`. Palette contains all colors used to render font glyphs. Each palette has the same number of colors. Colors can be overridden using `_font_set_palette_custom_colors()`.

`int` **\_font_get_palette_count**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the number of predefined color palettes. Palette contains all colors used to render font glyphs. Each palette has the same number of colors.

`PackedColorArray` **\_font_get_palette_custom_colors**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns array of custom colors to override predefined palette.

`String` **\_font_get_palette_name**(font_rid: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the name of the predefined color palette at `index`. Palette contains all colors used to render font glyphs. Each palette has the same number of colors.

`float` **\_font_get_scale**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns scaling factor of the color bitmap font.

`bool` **\_font_get_script_support_override**(font_rid: `RID`, script: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Returns `true` if support override is enabled for the `script`.

`PackedStringArray` **\_font_get_script_support_overrides**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)`

Returns list of script support overrides.

`Array`\[`Dictionary`\] **\_font_get_size_cache_info**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font cache information, each entry contains the following fields: `Vector2i size_px` - font size in pixels, `float viewport_oversampling` - viewport oversampling factor, `int glyphs` - number of rendered glyphs, `int textures` - number of used textures, `int textures_size` - size of texture data in bytes.

`Array`\[`Vector2i`\] **\_font_get_size_cache_list**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns list of the font sizes in the cache. Each size is `Vector2i` with font size and outline size.

`int` **\_font_get_spacing**(font_rid: `RID`, spacing: `SpacingType`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the spacing for `spacing` in pixels (not relative to the font size).

`int` **\_font_get_stretch**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font stretch amount, compared to a normal width. A percentage value between `50%` and `200%`.

`BitField (This value is an integer composed as a bitmask of the following flags.)`\[`FontStyle`\] **\_font_get_style**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font style flags.

`String` **\_font_get_style_name**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font style name.

`SubpixelPositioning` **\_font_get_subpixel_positioning**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns font subpixel glyph positioning mode.

`String` **\_font_get_supported_chars**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns a string containing all the characters available in the font.

`PackedInt32Array` **\_font_get_supported_glyphs**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns an array containing all glyph indices in the font.

`int` **\_font_get_texture_count**(font_rid: `RID`, size: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns number of textures used by font cache entry.

`Image` **\_font_get_texture_image**(font_rid: `RID`, size: `Vector2i`, texture_index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns font cache texture image data.

`PackedInt32Array` **\_font_get_texture_offsets**(font_rid: `RID`, size: `Vector2i`, texture_index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns array containing glyph packing data.

`Transform2D` **\_font_get_transform**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns 2D transform applied to the font outlines.

`float` **\_font_get_underline_position**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns pixel offset of the underline below the baseline.

`float` **\_font_get_underline_thickness**(font_rid: `RID`, size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns thickness of the underline in pixels.

`int` **\_font_get_used_palette**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns used palette index.

`Dictionary` **\_font_get_variation_coordinates**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns variation coordinates for the specified font cache entry.

`int` **\_font_get_weight**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns weight (boldness) of the font. A value in the `100...999` range, normal font weight is `400`, bold font weight is `700`.

`bool` **\_font_has_char**(font_rid: `RID`, char: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns `true` if a Unicode `char` is available in the font.

`bool` **\_font_is_allow_system_fallback**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if system fonts can be automatically used as fallbacks.

`bool` **\_font_is_force_autohinter**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if auto-hinting is supported and preferred over font built-in hinting.

`bool` **\_font_is_language_supported**(font_rid: `RID`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if the font supports the given language (as a [ISO 639](https://en.wikipedia.org/wiki/ISO_639-1) code).

`bool` **\_font_is_modulate_color_glyphs**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if color modulation is applied when drawing the font's colored glyphs.

`bool` **\_font_is_multichannel_signed_distance_field**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if glyphs of all sizes are rendered using single multichannel signed distance field generated from the dynamic font vector data.

`bool` **\_font_is_script_supported**(font_rid: `RID`, script: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if the font supports the given script (as a [ISO 15924](https://en.wikipedia.org/wiki/ISO_15924) code).

`void (No return value.)` **\_font_remove_glyph**(font_rid: `RID`, size: `Vector2i`, glyph: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Removes specified rendered glyph information from the cache entry.

`void (No return value.)` **\_font_remove_kerning**(font_rid: `RID`, size: `int`, glyph_pair: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)`

Removes kerning override for the pair of glyphs.

`void (No return value.)` **\_font_remove_language_support_override**(font_rid: `RID`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Remove language support override.

`void (No return value.)` **\_font_remove_script_support_override**(font_rid: `RID`, script: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Removes script support override.

`void (No return value.)` **\_font_remove_size_cache**(font_rid: `RID`, size: `Vector2i`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Removes specified font size from the cache entry.

`void (No return value.)` **\_font_remove_texture**(font_rid: `RID`, size: `Vector2i`, texture_index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Removes specified texture from the cache entry.

`void (No return value.)` **\_font_render_glyph**(font_rid: `RID`, size: `Vector2i`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Renders specified glyph to the font cache texture.

`void (No return value.)` **\_font_render_range**(font_rid: `RID`, size: `Vector2i`, start: `int`, end: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Renders the range of characters to the font cache texture.

`void (No return value.)` **\_font_set_allow_system_fallback**(font_rid: `RID`, allow_system_fallback: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true`, system fonts can be automatically used as fallbacks.

`void (No return value.)` **\_font_set_antialiasing**(font_rid: `RID`, antialiasing: `FontAntialiasing`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font anti-aliasing mode.

`void (No return value.)` **\_font_set_ascent**(font_rid: `RID`, size: `int`, ascent: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets the font ascent (number of pixels above the baseline).

`void (No return value.)` **\_font_set_baseline_offset**(font_rid: `RID`, baseline_offset: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets extra baseline offset (as a fraction of font height).

`void (No return value.)` **\_font_set_data**(font_rid: `RID`, data: `PackedByteArray`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font source data, e.g contents of the dynamic font source file.

`void (No return value.)` **\_font_set_data_ptr**(font_rid: `RID`, data_ptr: `const uint8_t*`, data_size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets pointer to the font source data, e.g contents of the dynamic font source file.

`void (No return value.)` **\_font_set_descent**(font_rid: `RID`, size: `int`, descent: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets the font descent (number of pixels below the baseline).

`void (No return value.)` **\_font_set_disable_embedded_bitmaps**(font_rid: `RID`, disable_embedded_bitmaps: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true`, embedded font bitmap loading is disabled.

`void (No return value.)` **\_font_set_embolden**(font_rid: `RID`, strength: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font embolden strength. If `strength` is not equal to zero, emboldens the font outlines. Negative values reduce the outline thickness.

`void (No return value.)` **\_font_set_face_index**(font_rid: `RID`, face_index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets an active face index in the TrueType / OpenType collection.

`void (No return value.)` **\_font_set_fixed_size**(font_rid: `RID`, fixed_size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets bitmap font fixed size. If set to value greater than zero, same cache entry will be used for all font sizes.

`void (No return value.)` **\_font_set_fixed_size_scale_mode**(font_rid: `RID`, fixed_size_scale_mode: `FixedSizeScaleMode`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets bitmap font scaling mode. This property is used only if `fixed_size` is greater than zero.

`void (No return value.)` **\_font_set_force_autohinter**(font_rid: `RID`, force_autohinter: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true` auto-hinting is preferred over font built-in hinting.

`void (No return value.)` **\_font_set_generate_mipmaps**(font_rid: `RID`, generate_mipmaps: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true` font texture mipmap generation is enabled.

`void (No return value.)` **\_font_set_global_oversampling**(oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets oversampling factor, shared by all font in the TextServer.

`void (No return value.)` **\_font_set_glyph_advance**(font_rid: `RID`, size: `int`, glyph: `int`, advance: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets glyph advance (offset of the next glyph).

`void (No return value.)` **\_font_set_glyph_offset**(font_rid: `RID`, size: `Vector2i`, glyph: `int`, offset: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets glyph offset from the baseline.

`void (No return value.)` **\_font_set_glyph_size**(font_rid: `RID`, size: `Vector2i`, glyph: `int`, gl_size: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets size of the glyph.

`void (No return value.)` **\_font_set_glyph_texture_idx**(font_rid: `RID`, size: `Vector2i`, glyph: `int`, texture_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets index of the cache texture containing the glyph.

`void (No return value.)` **\_font_set_glyph_uv_rect**(font_rid: `RID`, size: `Vector2i`, glyph: `int`, uv_rect: `Rect2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets rectangle in the cache texture containing the glyph.

`void (No return value.)` **\_font_set_hinting**(font_rid: `RID`, hinting: `Hinting`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font hinting mode. Used by dynamic fonts only.

`void (No return value.)` **\_font_set_keep_rounding_remainders**(font_rid: `RID`, keep_rounding_remainders: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets glyph position rounding behavior. If set to `true`, when aligning glyphs to the pixel boundaries rounding remainders are accumulated to ensure more uniform glyph distribution. This setting has no effect if subpixel positioning is enabled.

`void (No return value.)` **\_font_set_kerning**(font_rid: `RID`, size: `int`, glyph_pair: `Vector2i`, kerning: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets kerning for the pair of glyphs.

`void (No return value.)` **\_font_set_language_support_override**(font_rid: `RID`, language: `String`, supported: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Adds override for `_font_is_language_supported()`.

`void (No return value.)` **\_font_set_modulate_color_glyphs**(font_rid: `RID`, modulate: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true`, color modulation is applied when drawing colored glyphs, otherwise it's applied to the monochrome glyphs only.

`void (No return value.)` **\_font_set_msdf_pixel_range**(font_rid: `RID`, msdf_pixel_range: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets the width of the range around the shape between the minimum and maximum representable signed distance.

`void (No return value.)` **\_font_set_msdf_size**(font_rid: `RID`, msdf_size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets source font size used to generate MSDF textures.

`void (No return value.)` **\_font_set_multichannel_signed_distance_field**(font_rid: `RID`, msdf: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true`, glyphs of all sizes are rendered using single multichannel signed distance field generated from the dynamic font vector data. MSDF rendering allows displaying the font at any scaling factor without blurriness, and without incurring a CPU cost when the font size changes (since the font no longer needs to be rasterized on the CPU). As a downside, font hinting is not available with MSDF. The lack of font hinting may result in less crisp and less readable fonts at small sizes.

`void (No return value.)` **\_font_set_name**(font_rid: `RID`, name: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets the font family name.

`void (No return value.)` **\_font_set_opentype_feature_overrides**(font_rid: `RID`, overrides: `Dictionary`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font OpenType feature set override.

`void (No return value.)` **\_font_set_oversampling**(font_rid: `RID`, oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to a positive value, overrides the oversampling factor of the viewport this font is used in. See `Viewport.oversampling`. This value doesn't override the `oversampling` parameter of `draw_*` methods. Used by dynamic fonts only.

`void (No return value.)` **\_font_set_palette_custom_colors**(font_rid: `RID`, colors: `PackedColorArray`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets array of custom colors to override predefined palette. Set to empty array to reset overrides. Use `Color(0, 0, 0, 0)`, to keep predefined palette color at specific position.

`void (No return value.)` **\_font_set_scale**(font_rid: `RID`, size: `int`, scale: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets scaling factor of the color bitmap font.

`void (No return value.)` **\_font_set_script_support_override**(font_rid: `RID`, script: `String`, supported: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Adds override for `_font_is_script_supported()`.

`void (No return value.)` **\_font_set_spacing**(font_rid: `RID`, spacing: `SpacingType`, value: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets the spacing for `spacing` to `value` in pixels (not relative to the font size).

`void (No return value.)` **\_font_set_stretch**(font_rid: `RID`, stretch: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font stretch amount, compared to a normal width. A percentage value between `50%` and `200%`.

`void (No return value.)` **\_font_set_style**(font_rid: `RID`, style: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`FontStyle`\]) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets the font style flags.

`void (No return value.)` **\_font_set_style_name**(font_rid: `RID`, name_style: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets the font style name.

`void (No return value.)` **\_font_set_subpixel_positioning**(font_rid: `RID`, subpixel_positioning: `SubpixelPositioning`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets font subpixel glyph positioning mode.

`void (No return value.)` **\_font_set_texture_image**(font_rid: `RID`, size: `Vector2i`, texture_index: `int`, image: `Image`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets font cache texture image data.

`void (No return value.)` **\_font_set_texture_offsets**(font_rid: `RID`, size: `Vector2i`, texture_index: `int`, offset: `PackedInt32Array`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets array containing glyph packing data.

`void (No return value.)` **\_font_set_transform**(font_rid: `RID`, transform: `Transform2D`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets 2D transform, applied to the font outlines, can be used for slanting, flipping, and rotating glyphs.

`void (No return value.)` **\_font_set_underline_position**(font_rid: `RID`, size: `int`, underline_position: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets pixel offset of the underline below the baseline.

`void (No return value.)` **\_font_set_underline_thickness**(font_rid: `RID`, size: `int`, underline_thickness: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets thickness of the underline in pixels.

`void (No return value.)` **\_font_set_used_palette**(font_rid: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets used palette index.

`void (No return value.)` **\_font_set_variation_coordinates**(font_rid: `RID`, variation_coordinates: `Dictionary`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets variation coordinates for the specified font cache entry.

`void (No return value.)` **\_font_set_weight**(font_rid: `RID`, weight: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets weight (boldness) of the font. A value in the `100...999` range, normal font weight is `400`, bold font weight is `700`.

`Dictionary` **\_font_supported_feature_list**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the dictionary of the supported OpenType features.

`Dictionary` **\_font_supported_variation_list**(font_rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the dictionary of the supported OpenType variation coordinates.

`String` **\_format_number**(number: `String`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

**Deprecated:** Use `TranslationServer.format_number()` instead.

Converts a number from Western Arabic (0..9) to the numeral system used in the given `language`.

If `language` is an empty string, the active locale will be used.

`void (No return value.)` **\_free_rid**(rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Frees an object created by this `TextServer`.

`int` **\_get_features**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns text server features, see `Feature`.

`Vector2` **\_get_hex_code_box_size**(size: `int`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns size of the replacement character (box with character hexadecimal code that is drawn in place of invalid characters).

`String` **\_get_name**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the name of the server interface.

`PackedByteArray` **\_get_support_data**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns default TextServer database (e.g. ICU break iterators and dictionaries).

`String` **\_get_support_data_filename**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns default TextServer database (e.g. ICU break iterators and dictionaries) filename.

`String` **\_get_support_data_info**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns TextServer database (e.g. ICU break iterators and dictionaries) description.

`bool` **\_has**(rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Returns `true` if `rid` is valid resource owned by this text server.

`bool` **\_has_feature**(feature: `Feature`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns `true` if the server supports a feature.

`int` **\_is_confusable**(string: `String`, dict: `PackedStringArray`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns index of the first string in `dict` which is visually confusable with the `string`, or `-1` if none is found.

`bool` **\_is_locale_right_to_left**(locale: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if locale is right-to-left.

`bool` **\_is_locale_using_support_data**(locale: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if the locale requires text server support data for line/word breaking.

`bool` **\_is_valid_identifier**(string: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if `string` is a valid identifier.

`bool` **\_is_valid_letter**(unicode: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`bool` **\_load_support_data**(filename: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Loads optional TextServer database (e.g. ICU break iterators and dictionaries).

`int` **\_name_to_tag**(name: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Converts the given readable name of a feature, variation, script, or language to an OpenType tag.

`String` **\_parse_number**(number: `String`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

**Deprecated:** Use `TranslationServer.parse_number()` instead.

Converts `number` from the numeral system used in the given `language` to Western Arabic (0..9).

If `language` is an empty string, the active locale will be used.

`Array`\[`Vector3i`\] **\_parse_structured_text**(parser_type: `StructuredTextParser`, args: `Array`, text: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Default implementation of the BiDi algorithm override function.

`String` **\_percent_sign**(language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

**Deprecated:** Use `TranslationServer.get_percent_sign()` instead.

Returns percent sign used in the given `language`.

`void (No return value.)` **\_reference_oversampling_level**(oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Increases the reference count of the specified oversampling level. This method is called by `Viewport`, and should not be used directly.

`bool` **\_save_support_data**(filename: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Saves optional TextServer database (e.g. ICU break iterators and dictionaries) to the file.

`int` **\_shaped_get_run_count**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the number of uniform text runs in the buffer.

`Direction` **\_shaped_get_run_direction**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the direction of the `index` text run (in visual order).

`RID` **\_shaped_get_run_font_rid**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the font RID of the `index` text run (in visual order).

`int` **\_shaped_get_run_font_size**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the font size of the `index` text run (in visual order).

`Vector2i` **\_shaped_get_run_glyph_range**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the glyph range of the `index` text run (in visual order).

`String` **\_shaped_get_run_language**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the language of the `index` text run (in visual order).

`Variant` **\_shaped_get_run_object**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the embedded object of the `index` text run (in visual order).

`Vector2i` **\_shaped_get_run_range**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the source text range of the `index` text run (in visual order).

`String` **\_shaped_get_run_text**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the source text of the `index` text run (in visual order).

`int` **\_shaped_get_span_count**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns number of text spans added using `_shaped_text_add_string()` or `_shaped_text_add_object()`.

`Variant` **\_shaped_get_span_embedded_object**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns text embedded object key.

`Variant` **\_shaped_get_span_meta**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns text span metadata.

`Variant` **\_shaped_get_span_object**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the text span embedded object key.

`String` **\_shaped_get_span_text**(shaped: `RID`, index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the text span source text.

`String` **\_shaped_get_text**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the text buffer source text, including object replacement characters.

`void (No return value.)` **\_shaped_set_span_update_font**(shaped: `RID`, index: `int`, fonts: `Array`\[`RID`\], size: `int`, opentype_features: `Dictionary`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Changes text span font, font size, and OpenType features, without changing the text.

`bool` **\_shaped_text_add_object**(shaped: `RID`, key: `Variant`, size: `Vector2`, inline_align: `InlineAlignment`, length: `int`, baseline: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Adds inline object to the text buffer, `key` must be unique. In the text, object is represented as `length` object replacement characters.

`bool` **\_shaped_text_add_string**(shaped: `RID`, text: `String`, fonts: `Array`\[`RID`\], size: `int`, opentype_features: `Dictionary`, language: `String`, meta: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Adds text span and font to draw it to the text buffer.

`void (No return value.)` **\_shaped_text_clear**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Clears text buffer (removes text and inline objects).

`int` **\_shaped_text_closest_character_pos**(shaped: `RID`, pos: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns composite character position closest to the `pos`.

`void (No return value.)` **\_shaped_text_draw**(shaped: `RID`, canvas: `RID`, pos: `Vector2`, clip_l: `float`, clip_r: `float`, color: `Color`, oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Draw shaped text into a canvas item at a given position, with `color`. `pos` specifies the leftmost point of the baseline (for horizontal layout) or topmost point of the baseline (for vertical layout). If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`void (No return value.)` **\_shaped_text_draw_outline**(shaped: `RID`, canvas: `RID`, pos: `Vector2`, clip_l: `float`, clip_r: `float`, outline_size: `int`, color: `Color`, oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Draw the outline of the shaped text into a canvas item at a given position, with `color`. `pos` specifies the leftmost point of the baseline (for horizontal layout) or topmost point of the baseline (for vertical layout). If `oversampling` is greater than zero, it is used as font oversampling factor, otherwise viewport oversampling settings are used.

`RID` **\_shaped_text_duplicate**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Duplicates shaped text buffer.

`float` **\_shaped_text_fit_to_width**(shaped: `RID`, width: `float`, justification_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`JustificationFlag`\]) `virtual (This method should typically be overridden by the user to have any effect.)`

Adjusts text width to fit to specified width, returns new text width.

`float` **\_shaped_text_get_ascent**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the text ascent (number of pixels above the baseline for horizontal layout or to the left of baseline for vertical).

`void (No return value.)` **\_shaped_text_get_carets**(shaped: `RID`, position: `int`, r_caret: `CaretInfo*`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns shapes of the carets corresponding to the character offset `position` in the text. Returned caret shape is 1 pixel wide rectangle.

`PackedInt32Array` **\_shaped_text_get_character_breaks**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns array of the composite character boundaries.

`int` **\_shaped_text_get_custom_ellipsis**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns ellipsis character used for text clipping.

`String` **\_shaped_text_get_custom_punctuation**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns custom punctuation character list, used for word breaking. If set to empty string, server defaults are used.

`float` **\_shaped_text_get_descent**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the text descent (number of pixels below the baseline for horizontal layout or to the right of baseline for vertical).

`Direction` **\_shaped_text_get_direction**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns direction of the text.

`int` **\_shaped_text_get_dominant_direction_in_range**(shaped: `RID`, start: `int`, end: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns dominant direction of in the range of text.

`int` **\_shaped_text_get_ellipsis_glyph_count**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns number of glyphs in the ellipsis.

`const Glyph*` **\_shaped_text_get_ellipsis_glyphs**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns array of the glyphs in the ellipsis.

`int` **\_shaped_text_get_ellipsis_pos**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns position of the ellipsis.

`int` **\_shaped_text_get_glyph_count**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns number of glyphs in the buffer.

`const Glyph*` **\_shaped_text_get_glyphs**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns an array of glyphs in the visual order.

`Vector2` **\_shaped_text_get_grapheme_bounds**(shaped: `RID`, pos: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns composite character's bounds as offsets from the start of the line.

`Direction` **\_shaped_text_get_inferred_direction**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns direction of the text, inferred by the BiDi algorithm.

`PackedInt32Array` **\_shaped_text_get_line_breaks**(shaped: `RID`, width: `float`, start: `int`, break_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\]) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Breaks text to the lines and returns character ranges for each line.

`PackedInt32Array` **\_shaped_text_get_line_breaks_adv**(shaped: `RID`, width: `PackedFloat32Array`, start: `int`, once: `bool`, break_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LineBreakFlag`\]) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Breaks text to the lines and columns. Returns character ranges for each segment.

`int` **\_shaped_text_get_object_glyph**(shaped: `RID`, key: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the glyph index of the inline object.

`Vector2i` **\_shaped_text_get_object_range**(shaped: `RID`, key: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the character range of the inline object.

`Rect2` **\_shaped_text_get_object_rect**(shaped: `RID`, key: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns bounding rectangle of the inline object.

`Array` **\_shaped_text_get_objects**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns array of inline objects.

`Orientation` **\_shaped_text_get_orientation**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns text orientation.

`RID` **\_shaped_text_get_parent**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the parent buffer from which the substring originates.

`bool` **\_shaped_text_get_preserve_control**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if text buffer is configured to display control characters.

`bool` **\_shaped_text_get_preserve_invalid**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if text buffer is configured to display hexadecimal codes in place of invalid characters.

`Vector2i` **\_shaped_text_get_range**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns substring buffer character range in the parent buffer.

`PackedVector2Array` **\_shaped_text_get_selection**(shaped: `RID`, start: `int`, end: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns selection rectangles for the specified character range.

`Vector2` **\_shaped_text_get_size**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns size of the text.

`int` **\_shaped_text_get_spacing**(shaped: `RID`, spacing: `SpacingType`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns extra spacing added between glyphs or lines in pixels.

`int` **\_shaped_text_get_trim_pos**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the position of the overrun trim.

`float` **\_shaped_text_get_underline_position**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns pixel offset of the underline below the baseline.

`float` **\_shaped_text_get_underline_thickness**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns thickness of the underline.

`float` **\_shaped_text_get_width**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns width (for horizontal layout) or height (for vertical) of the text.

`PackedInt32Array` **\_shaped_text_get_word_breaks**(shaped: `RID`, grapheme_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`GraphemeFlag`\], skip_grapheme_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`GraphemeFlag`\]) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Breaks text into words and returns array of character ranges. Use `grapheme_flags` to set what characters are used for breaking.

`bool` **\_shaped_text_has_object**(shaped: `RID`, key: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns `true` if an object with `key` is embedded in this shaped text buffer.

`int` **\_shaped_text_hit_test_grapheme**(shaped: `RID`, coord: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns grapheme index at the specified pixel offset at the baseline, or `-1` if none is found.

`int` **\_shaped_text_hit_test_position**(shaped: `RID`, coord: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns caret character offset at the specified pixel offset at the baseline. This function always returns a valid position.

`bool` **\_shaped_text_is_ready**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns `true` if buffer is successfully shaped.

`int` **\_shaped_text_next_character_pos**(shaped: `RID`, pos: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns composite character end position closest to the `pos`.

`int` **\_shaped_text_next_grapheme_pos**(shaped: `RID`, pos: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns grapheme end position closest to the `pos`.

`void (No return value.)` **\_shaped_text_overrun_trim_to_width**(shaped: `RID`, width: `float`, trim_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`TextOverrunFlag`\]) `virtual (This method should typically be overridden by the user to have any effect.)`

Trims text if it exceeds the given width.

`int` **\_shaped_text_prev_character_pos**(shaped: `RID`, pos: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns composite character start position closest to the `pos`.

`int` **\_shaped_text_prev_grapheme_pos**(shaped: `RID`, pos: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns grapheme start position closest to the `pos`.

`bool` **\_shaped_text_resize_object**(shaped: `RID`, key: `Variant`, size: `Vector2`, inline_align: `InlineAlignment`, baseline: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Sets new size and alignment of embedded object.

`void (No return value.)` **\_shaped_text_set_bidi_override**(shaped: `RID`, override: `Array`) `virtual (This method should typically be overridden by the user to have any effect.)`

Overrides BiDi for the structured text.

`void (No return value.)` **\_shaped_text_set_custom_ellipsis**(shaped: `RID`, char: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets ellipsis character used for text clipping.

`void (No return value.)` **\_shaped_text_set_custom_punctuation**(shaped: `RID`, punct: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets custom punctuation character list, used for word breaking. If set to empty string, server defaults are used.

`void (No return value.)` **\_shaped_text_set_direction**(shaped: `RID`, direction: `Direction`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets desired text direction. If set to `TextServer.DIRECTION_AUTO`, direction will be detected based on the buffer contents and current locale.

`void (No return value.)` **\_shaped_text_set_orientation**(shaped: `RID`, orientation: `Orientation`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets desired text orientation.

`void (No return value.)` **\_shaped_text_set_preserve_control**(shaped: `RID`, enabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true` text buffer will display control characters.

`void (No return value.)` **\_shaped_text_set_preserve_invalid**(shaped: `RID`, enabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

If set to `true` text buffer will display invalid characters as hexadecimal codes, otherwise nothing is displayed.

`void (No return value.)` **\_shaped_text_set_spacing**(shaped: `RID`, spacing: `SpacingType`, value: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets extra spacing added between glyphs or lines in pixels.

`bool` **\_shaped_text_shape**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Shapes buffer if it's not shaped. Returns `true` if the string is shaped successfully.

`const Glyph*` **\_shaped_text_sort_logical**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Returns text glyphs in the logical order.

`RID` **\_shaped_text_substr**(shaped: `RID`, start: `int`, length: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns text buffer for the substring of the text in the `shaped` text buffer (including inline objects).

`float` **\_shaped_text_tab_align**(shaped: `RID`, tab_stops: `PackedFloat32Array`) `virtual (This method should typically be overridden by the user to have any effect.)`

Aligns shaped text to the given tab-stops.

`bool` **\_shaped_text_update_breaks**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)`

Updates break points in the shaped text. This method is called by default implementation of text breaking functions.

`bool` **\_shaped_text_update_justification_ops**(shaped: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)`

Updates justification points in the shaped text. This method is called by default implementation of text justification functions.

`bool` **\_spoof_check**(string: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if `string` is likely to be an attempt at confusing the reader.

`PackedInt32Array` **\_string_get_character_breaks**(string: `String`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns array of the composite character boundaries.

`PackedInt32Array` **\_string_get_word_breaks**(string: `String`, language: `String`, chars_per_line: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns an array of the word break boundaries. Elements in the returned array are the offsets of the start and end of words. Therefore the length of the array is always even.

`String` **\_string_to_lower**(string: `String`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the string converted to `lowercase`.

`String` **\_string_to_title**(string: `String`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the string converted to `Title Case`.

`String` **\_string_to_upper**(string: `String`, language: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the string converted to `UPPERCASE`.

`String` **\_strip_diacritics**(string: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Strips diacritics from the string.

`String` **\_tag_to_name**(tag: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Converts the given OpenType tag to the readable name of a feature, variation, script, or language.

`void (No return value.)` **\_unreference_oversampling_level**(oversampling: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Decreases the reference count of the specified oversampling level, and frees the font cache for oversampling level when the reference count reaches zero. This method is called by `Viewport`, and should not be used directly.