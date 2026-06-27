# ResourceFormatSaver

**Inherits:** `RefCounted` **<** `Object`

Saves a specific resource type to a file.

## Description

The engine can save resources when you do it from the editor, or when you use the `ResourceSaver` singleton. This is accomplished thanks to multiple **ResourceFormatSaver**s, each handling its own format and called automatically by the engine.

By default, Godot saves resources as `.tres` (text-based), `.res` (binary) or another built-in format, but you can choose to create your own format by extending this class. Be sure to respect the documented return types and values. You should give it a global class name with `class_name` for it to be registered. Like built-in ResourceFormatSavers, it will be called automatically when saving resources of its recognized type(s). You may also implement a `ResourceFormatLoader`.

## Method Descriptions

`PackedStringArray` **\_get_recognized_extensions**(resource: `Resource`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the list of extensions available for saving the resource object, provided it is recognized (see `_recognize()`).

`bool` **\_recognize**(resource: `Resource`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns whether the given resource object can be saved by this saver.

`bool` **\_recognize_path**(resource: `Resource`, path: `String`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if this saver handles a given save path and `false` otherwise.

If this method is not implemented, the default behavior returns whether the path's extension is within the ones provided by `_get_recognized_extensions()`.

`Error` **\_save**(resource: `Resource`, path: `String`, flags: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Saves the given resource object to a file at the target `path`. `flags` is a bitmask composed with `SaverFlags` constants.

Returns `@GlobalScope.OK` on success, or an `Error` constant in case of failure.

`Error` **\_set_uid**(path: `String`, uid: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Sets a new UID for the resource at the given `path`. Returns `@GlobalScope.OK` on success, or an `Error` constant in case of failure.