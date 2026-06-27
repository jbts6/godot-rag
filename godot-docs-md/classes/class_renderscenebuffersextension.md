# RenderSceneBuffersExtension

**Inherits:** `RenderSceneBuffers` **<** `RefCounted` **<** `Object`

This class allows for a RenderSceneBuffer implementation to be made in GDExtension.

## Description

This class allows for a RenderSceneBuffer implementation to be made in GDExtension.

## Method Descriptions

`void (No return value.)` **\_configure**(config: `RenderSceneBuffersConfiguration`) `virtual (This method should typically be overridden by the user to have any effect.)`

Implement this in GDExtension to handle the (re)sizing of a viewport.

`void (No return value.)` **\_set_anisotropic_filtering_level**(anisotropic_filtering_level: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Implement this in GDExtension to change the anisotropic filtering level.

`void (No return value.)` **\_set_fsr_sharpness**(fsr_sharpness: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Implement this in GDExtension to record a new FSR sharpness value.

`void (No return value.)` **\_set_texture_mipmap_bias**(texture_mipmap_bias: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Implement this in GDExtension to change the texture mipmap bias.

`void (No return value.)` **\_set_use_debanding**(use_debanding: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Implement this in GDExtension to react to the debanding flag changing.