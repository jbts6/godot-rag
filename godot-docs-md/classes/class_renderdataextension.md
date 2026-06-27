# RenderDataExtension

**Inherits:** `RenderData` **<** `Object`

This class allows for a RenderData implementation to be made in GDExtension.

## Description

This class allows for a RenderData implementation to be made in GDExtension.

## Method Descriptions

`RID` **\_get_camera_attributes**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Implement this in GDExtension to return the `RID` for the implementation's camera attributes object.

`RID` **\_get_environment**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Implement this in GDExtension to return the `RID` of the implementation's environment object.

`RenderSceneBuffers` **\_get_render_scene_buffers**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Implement this in GDExtension to return the implementation's `RenderSceneBuffers` object.

`RenderSceneData` **\_get_render_scene_data**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Implement this in GDExtension to return the implementation's `RenderSceneDataExtension` object.