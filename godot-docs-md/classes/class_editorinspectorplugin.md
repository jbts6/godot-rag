# EditorInspectorPlugin

**Inherits:** `RefCounted` **<** `Object`

Plugin for adding custom property editors on the inspector.

## Description

**EditorInspectorPlugin** allows adding custom property editors to `EditorInspector`.

When an object is edited, the `_can_handle()` function is called and must return `true` if the object type is supported.

If supported, the function `_parse_begin()` will be called, allowing to place custom controls at the beginning of the class.

Subsequently, the `_parse_category()` and `_parse_property()` are called for every category and property. They offer the ability to add custom controls to the inspector too.

Finally, `_parse_end()` will be called.

On each of these calls, the "add" functions can be called.

To use **EditorInspectorPlugin**, register it using the `EditorPlugin.add_inspector_plugin()` method first.

## Tutorials

- `Inspector plugins `

## Method Descriptions

`bool` **\_can_handle**(object: `Object`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if this object can be handled by this plugin.

`void (No return value.)` **\_parse_begin**(object: `Object`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called to allow adding controls at the beginning of the property list for `object`.

`void (No return value.)` **\_parse_category**(object: `Object`, category: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called to allow adding controls at the beginning of a category in the property list for `object`.

`void (No return value.)` **\_parse_end**(object: `Object`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called to allow adding controls at the end of the property list for `object`.

`void (No return value.)` **\_parse_group**(object: `Object`, group: `String`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called to allow adding controls at the beginning of a group or a sub-group in the property list for `object`.

`bool` **\_parse_property**(object: `Object`, type: `Variant.Type`, name: `String`, hint_type: `PropertyHint`, hint_string: `String`, usage_flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`PropertyUsageFlags`\], wide: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called to allow adding property-specific editors to the property list for `object`. The added editor control must extend `EditorProperty`. Returning `true` removes the built-in editor for this property, otherwise allows to insert a custom editor before the built-in one.

`void (No return value.)` **add_custom_control**(control: `Control`)

Adds a custom control, which is not necessarily a property editor.

`void (No return value.)` **add_property_editor**(property: `String`, editor: `Control`, add_to_end: `bool` = false, label: `String` = "")

Adds a property editor for an individual property. The `editor` control must extend `EditorProperty`.

There can be multiple property editors for a property. If `add_to_end` is `true`, this newly added editor will be displayed after all the other editors of the property whose `add_to_end` is `false`. For example, the editor uses this parameter to add an "Edit Region" button for `Sprite2D.region_rect` below the regular `Rect2` editor.

`label` can be used to choose a custom label for the property editor in the inspector. If left empty, the label is computed from the name of the property instead.

`void (No return value.)` **add_property_editor_for_multiple_properties**(label: `String`, properties: `PackedStringArray`, editor: `Control`)

Adds an editor that allows modifying multiple properties. The `editor` control must extend `EditorProperty`.