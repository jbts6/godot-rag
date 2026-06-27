# PrismMesh

**Inherits:** `PrimitiveMesh` **<** `Mesh` **<** `Resource` **<** `RefCounted` **<** `Object`

Class representing a prism-shaped `PrimitiveMesh`.

## Description

Class representing a prism-shaped `PrimitiveMesh`.

## Property Descriptions

`float` **left_to_right** = `0.5`

- `void (No return value.)` **set_left_to_right**(value: `float`)
- `float` **get_left_to_right**()

Displacement of the upper edge along the X axis. 0.0 positions edge straight above the bottom-left edge.

`Vector3` **size** = `Vector3(1, 1, 1)`

- `void (No return value.)` **set_size**(value: `Vector3`)
- `Vector3` **get_size**()

Size of the prism.

`int` **subdivide_depth** = `0`

- `void (No return value.)` **set_subdivide_depth**(value: `int`)
- `int` **get_subdivide_depth**()

Number of added edge loops along the Z axis.

`int` **subdivide_height** = `0`

- `void (No return value.)` **set_subdivide_height**(value: `int`)
- `int` **get_subdivide_height**()

Number of added edge loops along the Y axis.

`int` **subdivide_width** = `0`

- `void (No return value.)` **set_subdivide_width**(value: `int`)
- `int` **get_subdivide_width**()

Number of added edge loops along the X axis.