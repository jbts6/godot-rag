# OpenXRCompositionLayerEquirect

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `OpenXRCompositionLayer` **<** `Node3D` **<** `Node` **<** `Object`

An OpenXR composition layer that is rendered as an internal slice of a sphere.

## Description

An OpenXR composition layer that allows rendering a `SubViewport` on an internal slice of a sphere.

## Property Descriptions

`float` **central_horizontal_angle** = `1.5707964`

- `void (No return value.)` **set_central_horizontal_angle**(value: `float`)
- `float` **get_central_horizontal_angle**()

The central horizontal angle of the sphere. Used to set the width.

`int` **fallback_segments** = `10`

- `void (No return value.)` **set_fallback_segments**(value: `int`)
- `int` **get_fallback_segments**()

The number of segments to use in the fallback mesh.

`float` **lower_vertical_angle** = `0.7853982`

- `void (No return value.)` **set_lower_vertical_angle**(value: `float`)
- `float` **get_lower_vertical_angle**()

The lower vertical angle of the sphere. Used (together with `upper_vertical_angle`) to set the height.

`float` **radius** = `1.0`

- `void (No return value.)` **set_radius**(value: `float`)
- `float` **get_radius**()

The radius of the sphere.

`float` **upper_vertical_angle** = `0.7853982`

- `void (No return value.)` **set_upper_vertical_angle**(value: `float`)
- `float` **get_upper_vertical_angle**()

The upper vertical angle of the sphere. Used (together with `lower_vertical_angle`) to set the height.