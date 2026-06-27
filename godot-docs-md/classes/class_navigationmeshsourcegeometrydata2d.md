# NavigationMeshSourceGeometryData2D

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Container for parsed source geometry data used in navigation mesh baking.

## Description

Container for parsed source geometry data used in navigation mesh baking.

## Method Descriptions

`void (No return value.)` **add_obstruction_outline**(shape_outline: `PackedVector2Array`)

Adds the outline points of a shape as obstructed area.

`void (No return value.)` **add_projected_obstruction**(vertices: `PackedVector2Array`, carve: `bool`)

Adds a projected obstruction shape to the source geometry. If `carve` is `true` the carved shape will not be affected by additional offsets (e.g. agent radius) of the navigation mesh baking process.

`void (No return value.)` **add_traversable_outline**(shape_outline: `PackedVector2Array`)

Adds the outline points of a shape as traversable area.

`void (No return value.)` **append_obstruction_outlines**(obstruction_outlines: `Array`\[`PackedVector2Array`\])

Appends another array of `obstruction_outlines` at the end of the existing obstruction outlines array.

`void (No return value.)` **append_traversable_outlines**(traversable_outlines: `Array`\[`PackedVector2Array`\])

Appends another array of `traversable_outlines` at the end of the existing traversable outlines array.

`void (No return value.)` **clear**()

Clears the internal data.

`void (No return value.)` **clear_projected_obstructions**()

Clears all projected obstructions.

`Rect2` **get_bounds**()

Returns an axis-aligned bounding box that covers all the stored geometry data. The bounds are calculated when calling this function with the result cached until further geometry changes are made.

`Array`\[`PackedVector2Array`\] **get_obstruction_outlines**() `const`

Returns all the obstructed area outlines arrays.

`Array` **get_projected_obstructions**() `const`

Returns the projected obstructions as an `Array` of dictionaries. Each `Dictionary` contains the following entries:

- `vertices` - A `PackedFloat32Array` that defines the outline points of the projected shape.
- `carve` - A `bool` that defines how the projected shape affects the navigation mesh baking. If `true` the projected shape will not be affected by addition offsets, e.g. agent radius.

`Array`\[`PackedVector2Array`\] **get_traversable_outlines**() `const`

Returns all the traversable area outlines arrays.

`bool` **has_data**()

Returns `true` when parsed source geometry data exists.

`void (No return value.)` **merge**(other_geometry: `NavigationMeshSourceGeometryData2D`)

Adds the geometry data of another **NavigationMeshSourceGeometryData2D** to the navigation mesh baking data.

`void (No return value.)` **set_obstruction_outlines**(obstruction_outlines: `Array`\[`PackedVector2Array`\])

Sets all the obstructed area outlines arrays.

`void (No return value.)` **set_projected_obstructions**(projected_obstructions: `Array`)

Sets the projected obstructions with an Array of Dictionaries with the following key value pairs:

``` gdscript
"vertices" : PackedFloat32Array
"carve" : bool
```

`void (No return value.)` **set_traversable_outlines**(traversable_outlines: `Array`\[`PackedVector2Array`\])

Sets all the traversable area outlines arrays.