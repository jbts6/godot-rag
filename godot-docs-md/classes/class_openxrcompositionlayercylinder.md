# OpenXRCompositionLayerCylinder

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `OpenXRCompositionLayer` **<** `Node3D` **<** `Node` **<** `Object`

An OpenXR composition layer that is rendered as an internal slice of a cylinder.

## Description

An OpenXR composition layer that allows rendering a `SubViewport` on an internal slice of a cylinder.

## Property Descriptions

`float` **aspect_ratio** = `1.0`

- `void (No return value.)` **set_aspect_ratio**(value: `float`)
- `float` **get_aspect_ratio**()

The aspect ratio of the slice. Used to set the height relative to the width.

`float` **central_angle** = `1.5707964`

- `void (No return value.)` **set_central_angle**(value: `float`)
- `float` **get_central_angle**()

The central angle of the cylinder. Used to set the width.

`int` **fallback_segments** = `10`

- `void (No return value.)` **set_fallback_segments**(value: `int`)
- `int` **get_fallback_segments**()

The number of segments to use in the fallback mesh.

`float` **radius** = `1.0`

- `void (No return value.)` **set_radius**(value: `float`)
- `float` **get_radius**()

The radius of the cylinder.