# TextureLayered

**Inherits:** `Texture` **<** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `CompressedTextureLayered`, `ImageTextureLayered`, `PlaceholderTextureLayered`, `TextureLayeredRD`

Base class for texture types which contain the data of multiple `Image`s. Each image is of the same size and format.

## Description

Base class for `ImageTextureLayered` and `CompressedTextureLayered`. Cannot be used directly, but contains all the functions necessary for accessing the derived resource types. See also `Texture3D`.

Data is set on a per-layer basis. For `Texture2DArray`s, the layer specifies the array layer.

All images need to have the same width, height and number of mipmap levels.

A **TextureLayered** can be loaded with `ResourceLoader.load()`.

Internally, Godot maps these files to their respective counterparts in the target rendering driver (Vulkan, OpenGL3).

## Enumerations

enum **LayeredType**:

`LayeredType` **LAYERED_TYPE_2D_ARRAY** = `0`

Texture is a generic `Texture2DArray`.

`LayeredType` **LAYERED_TYPE_CUBEMAP** = `1`

Texture is a `Cubemap`, with each side in its own layer (6 in total).

`LayeredType` **LAYERED_TYPE_CUBEMAP_ARRAY** = `2`

Texture is a `CubemapArray`, with each cubemap being made of 6 layers.

## Method Descriptions

`Format` **\_get_format**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the **TextureLayered**'s format is queried.

`int` **\_get_height**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the **TextureLayered**'s height is queried.

`Image` **\_get_layer_data**(layer_index: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the data for a layer in the **TextureLayered** is queried.

`int` **\_get_layered_type**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the layers' type in the **TextureLayered** is queried.

`int` **\_get_layers**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the number of layers in the **TextureLayered** is queried.

`int` **\_get_width**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the **TextureLayered**'s width queried.

`bool` **\_has_mipmaps**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the presence of mipmaps in the **TextureLayered** is queried.

`Format` **get_format**() `const`

Returns the current format being used by this texture.

`int` **get_height**() `const`

Returns the height of the texture in pixels. Height is typically represented by the Y axis.

`Image` **get_layer_data**(layer: `int`) `const`

Returns an `Image` resource with the data from specified `layer`.

`LayeredType` **get_layered_type**() `const`

Returns the **TextureLayered**'s type. The type determines how the data is accessed, with cubemaps having special types.

`int` **get_layers**() `const`

Returns the number of referenced `Image`s.

`int` **get_width**() `const`

Returns the width of the texture in pixels. Width is typically represented by the X axis.

`bool` **has_mipmaps**() `const`

Returns `true` if the layers have generated mipmaps.