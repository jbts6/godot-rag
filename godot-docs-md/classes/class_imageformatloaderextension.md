# ImageFormatLoaderExtension

**Inherits:** `ImageFormatLoader` **<** `RefCounted` **<** `Object`

Base class for creating `ImageFormatLoader` extensions (adding support for extra image formats).

## Description

The engine supports multiple image formats out of the box (PNG, SVG, JPEG, WebP to name a few), but you can choose to implement support for additional image formats by extending this class.

Be sure to respect the documented return types and values. You should create an instance of it, and call `add_format_loader()` to register that loader during the initialization phase.

## Method Descriptions

`PackedStringArray` **\_get_recognized_extensions**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the list of file extensions for this image format. Files with the given extensions will be treated as image file and loaded using this class.

`Error` **\_load_image**(image: `Image`, fileaccess: `FileAccess`, flags: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`LoaderFlags`\], scale: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Loads the content of `fileaccess` into the provided `image`.

`void (No return value.)` **add_format_loader**()

Add this format loader to the engine, allowing it to recognize the file extensions returned by `_get_recognized_extensions()`.

`void (No return value.)` **remove_format_loader**()

Remove this format loader from the engine.