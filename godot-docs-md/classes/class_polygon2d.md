# Polygon2D

**Inherits:** `Node2D` **<** `CanvasItem` **<** `Node` **<** `Object`

A 2D polygon.

## Description

A Polygon2D is defined by a set of points. Each point is connected to the next, with the final point being connected to the first, resulting in a closed polygon. Polygon2Ds can be filled with color (solid or gradient) or filled with a given texture.

## Property Descriptions

`bool` **antialiased** = `false`

- `void (No return value.)` **set_antialiased**(value: `bool`)
- `bool` **get_antialiased**()

If `true`, polygon edges will be anti-aliased.

`Color` **color** = `Color(1, 1, 1, 1)`

- `void (No return value.)` **set_color**(value: `Color`)
- `Color` **get_color**()

The polygon's fill color. If `texture` is set, it will be multiplied by this color. It will also be the default color for vertices not set in `vertex_colors`.

`int` **internal_vertex_count** = `0`

- `void (No return value.)` **set_internal_vertex_count**(value: `int`)
- `int` **get_internal_vertex_count**()

Number of internal vertices, used for UV mapping.

`float` **invert_border** = `100.0`

- `void (No return value.)` **set_invert_border**(value: `float`)
- `float` **get_invert_border**()

Added padding applied to the bounding box when `invert_enabled` is set to `true`. Setting this value too small may result in a "Bad Polygon" error.

`bool` **invert_enabled** = `false`

- `void (No return value.)` **set_invert_enabled**(value: `bool`)
- `bool` **get_invert_enabled**()

If `true`, the polygon will be inverted, containing the area outside the defined points and extending to the `invert_border`.

`Vector2` **offset** = `Vector2(0, 0)`

- `void (No return value.)` **set_offset**(value: `Vector2`)
- `Vector2` **get_offset**()

The offset applied to each vertex.

`PackedVector2Array` **polygon** = `PackedVector2Array()`

- `void (No return value.)` **set_polygon**(value: `PackedVector2Array`)
- `PackedVector2Array` **get_polygon**()

The polygon's list of vertices. The final point will be connected to the first.

**Note:** The returned array is *copied* and any changes to it will not update the original property value. See `PackedVector2Array` for more details.

`Array` **polygons** = `[]`

- `void (No return value.)` **set_polygons**(value: `Array`)
- `Array` **get_polygons**()

The list of polygons, in case more than one is being represented. Every individual polygon is stored as a `PackedInt32Array` where each `int` is an index to a point in `polygon`. If empty, this property will be ignored, and the resulting single polygon will be composed of all points in `polygon`, using the order they are stored in.

`NodePath` **skeleton** = `NodePath("")`

- `void (No return value.)` **set_skeleton**(value: `NodePath`)
- `NodePath` **get_skeleton**()

Path to a `Skeleton2D` node used for skeleton-based deformations of this polygon. If empty or invalid, skeletal deformations will not be used.

`Texture2D` **texture**

- `void (No return value.)` **set_texture**(value: `Texture2D`)
- `Texture2D` **get_texture**()

The polygon's fill texture. Use `uv` to set texture coordinates.

`Vector2` **texture_offset** = `Vector2(0, 0)`

- `void (No return value.)` **set_texture_offset**(value: `Vector2`)
- `Vector2` **get_texture_offset**()

Amount to offset the polygon's `texture`. If set to `Vector2(0, 0)`, the texture's origin (its top-left corner) will be placed at the polygon's position.

`float` **texture_rotation** = `0.0`

- `void (No return value.)` **set_texture_rotation**(value: `float`)
- `float` **get_texture_rotation**()

The texture's rotation in radians.

`Vector2` **texture_scale** = `Vector2(1, 1)`

- `void (No return value.)` **set_texture_scale**(value: `Vector2`)
- `Vector2` **get_texture_scale**()

Amount to multiply the `uv` coordinates when using `texture`. Larger values make the texture smaller, and vice versa.

`PackedVector2Array` **uv** = `PackedVector2Array()`

- `void (No return value.)` **set_uv**(value: `PackedVector2Array`)
- `PackedVector2Array` **get_uv**()

Texture coordinates for each vertex of the polygon. There should be one UV value per polygon vertex. If there are fewer, undefined vertices will use `Vector2(0, 0)`.

**Note:** The returned array is *copied* and any changes to it will not update the original property value. See `PackedVector2Array` for more details.

`PackedColorArray` **vertex_colors** = `PackedColorArray()`

- `void (No return value.)` **set_vertex_colors**(value: `PackedColorArray`)
- `PackedColorArray` **get_vertex_colors**()

Color for each vertex. Colors are interpolated between vertices, resulting in smooth gradients. There should be one per polygon vertex. If there are fewer, undefined vertices will use `color`.

**Note:** The returned array is *copied* and any changes to it will not update the original property value. See `PackedColorArray` for more details.

## Method Descriptions

`void (No return value.)` **add_bone**(path: `NodePath`, weights: `PackedFloat32Array`)

Adds a bone with the specified `path` and `weights`.

`void (No return value.)` **clear_bones**()

Removes all bones from this **Polygon2D**.

`void (No return value.)` **erase_bone**(index: `int`)

Removes the specified bone from this **Polygon2D**.

`int` **get_bone_count**() `const`

Returns the number of bones in this **Polygon2D**.

`NodePath` **get_bone_path**(index: `int`) `const`

Returns the path to the node associated with the specified bone.

`PackedFloat32Array` **get_bone_weights**(index: `int`) `const`

Returns the weight values of the specified bone.

`void (No return value.)` **set_bone_path**(index: `int`, path: `NodePath`)

Sets the path to the node associated with the specified bone.

`void (No return value.)` **set_bone_weights**(index: `int`, weights: `PackedFloat32Array`)

Sets the weight values for the specified bone.