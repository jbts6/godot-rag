# PhysicsRayQueryParameters3D

**Inherits:** `RefCounted` **<** `Object`

Provides parameters for `PhysicsDirectSpaceState3D.intersect_ray()`.

## Description

By changing various properties of this object, such as the ray position, you can configure the parameters for `PhysicsDirectSpaceState3D.intersect_ray()`.

## Property Descriptions

`bool` **collide_with_areas** = `false`

- `void (No return value.)` **set_collide_with_areas**(value: `bool`)
- `bool` **is_collide_with_areas_enabled**()

If `true`, the query will take `Area3D`s into account.

`bool` **collide_with_bodies** = `true`

- `void (No return value.)` **set_collide_with_bodies**(value: `bool`)
- `bool` **is_collide_with_bodies_enabled**()

If `true`, the query will take `PhysicsBody3D`s into account.

`int` **collision_mask** = `4294967295`

- `void (No return value.)` **set_collision_mask**(value: `int`)
- `int` **get_collision_mask**()

The physics layers the query will detect (as a bitmask). By default, all collision layers are detected. See [Collision layers and masks](../tutorials/physics/physics_introduction.html#collision-layers-and-masks) in the documentation for more information.

`Array`\[`RID`\] **exclude** = `[]`

- `void (No return value.)` **set_exclude**(value: `Array`\[`RID`\])
- `Array`\[`RID`\] **get_exclude**()

The list of object `RID`s that will be excluded from collisions. Use `CollisionObject3D.get_rid()` to get the `RID` associated with a `CollisionObject3D`-derived node.

**Note:** The returned array is copied and any changes to it will not update the original property value. To update the value you need to modify the returned array, and then assign it to the property again.

`Vector3` **from** = `Vector3(0, 0, 0)`

- `void (No return value.)` **set_from**(value: `Vector3`)
- `Vector3` **get_from**()

The starting point of the ray being queried for, in global coordinates.

`bool` **hit_back_faces** = `true`

- `void (No return value.)` **set_hit_back_faces**(value: `bool`)
- `bool` **is_hit_back_faces_enabled**()

If `true`, the query will hit back faces with concave polygon shapes with back face enabled or heightmap shapes.

`bool` **hit_from_inside** = `false`

- `void (No return value.)` **set_hit_from_inside**(value: `bool`)
- `bool` **is_hit_from_inside_enabled**()

If `true`, the query will detect a hit when starting inside shapes. In this case the collision normal will be `Vector3(0, 0, 0)`. Does not affect concave polygon shapes or heightmap shapes.

`Vector3` **to** = `Vector3(0, 0, 0)`

- `void (No return value.)` **set_to**(value: `Vector3`)
- `Vector3` **get_to**()

The ending point of the ray being queried for, in global coordinates.

## Method Descriptions

`PhysicsRayQueryParameters3D` **create**(from: `Vector3`, to: `Vector3`, collision_mask: `int` = 4294967295, exclude: `Array`\[`RID`\] = \[\]) `static (This method doesn't need an instance to be called, so it can be called directly using the class name.)`

Returns a new, pre-configured **PhysicsRayQueryParameters3D** object. Use it to quickly create query parameters using the most common options.

    var query = PhysicsRayQueryParameters3D.create(position, position + Vector3(0, -10, 0))
    var collision = get_world_3d().direct_space_state.intersect_ray(query)