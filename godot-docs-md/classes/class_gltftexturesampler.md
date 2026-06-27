# GLTFTextureSampler

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Represents a glTF texture sampler

## Description

Represents a texture sampler as defined by the base glTF spec. Texture samplers in glTF specify how to sample data from the texture's base image, when rendering the texture on an object.

## Tutorials

- `Runtime file loading and saving `

## Property Descriptions

`int` **mag_filter** = `9729`

- `void (No return value.)` **set_mag_filter**(value: `int`)
- `int` **get_mag_filter**()

Texture's magnification filter, used when texture appears larger on screen than the source image.

`int` **min_filter** = `9987`

- `void (No return value.)` **set_min_filter**(value: `int`)
- `int` **get_min_filter**()

Texture's minification filter, used when the texture appears smaller on screen than the source image.

`int` **wrap_s** = `10497`

- `void (No return value.)` **set_wrap_s**(value: `int`)
- `int` **get_wrap_s**()

Wrapping mode to use for S-axis (horizontal) texture coordinates.

`int` **wrap_t** = `10497`

- `void (No return value.)` **set_wrap_t**(value: `int`)
- `int` **get_wrap_t**()

Wrapping mode to use for T-axis (vertical) texture coordinates.