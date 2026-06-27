# PhysicsRayQueryParameters2D

**Inherits:** `RefCounted` **<** `Object`

Provides parameters for `PhysicsDirectSpaceState2D.intersect_ray()`.

## Description

By changing various properties of this object, such as the ray position, you can configure the parameters for `PhysicsDirectSpaceState2D.intersect_ray()`.

## Property Descriptions

`bool` **collide_with_areas** = `false`

- `void (No return value.)` **set_collide_with_areas**(value: `bool`)
- `bool` **is_collide_with_areas_enabled**()

If `true`, the query will take `Area2D`s into account.

`bool` **collide_with_bodies** = `true`

- `void (No return value.)` **set_collide_with_bodies**(value: `bool`)
- `bool` **is_collide_with_bodies_enabled**()

If `true`, the query will take `PhysicsBody2D`s into account.

`int` **collision_mask** = `4294967295`

- `void (No return value.)` **set_collision_mask**(value: `int`)
- `int` **get_collision_mask**()

The physics layers the query will detect (as a bitmask). By default, all collision layers are detected. See [Collision layers and masks](../tutorials/physics/physics_introduction.html#collision-layers-and-masks) in the documentation for more information.

`Array`\[`RID`\] **exclude** = `[]`

- `void (No return value.)` **set_exclude**(value: `Array`\[`RID`\])
- `Array`\[`RID`\] **get_exclude**()

The list of object `RID`s that will be excluded from collisions. Use `CollisionObject2D.get_rid()` to get the `RID` associated with a `CollisionObject2D`-derived node.

**Note:** The returned array is copied and any changes to it will not update the original property value. To update the value you need to modify the returned array, and then assign it to the property again.

`Vector2` **from** = `Vector2(0, 0)`

- `void (No return value.)` **set_from**(value: `Vector2`)
- `Vector2` **get_from**()

The starting point of the ray being queried for, in global coordinates.

`bool` **hit_from_inside** = `false`

- `void (No return value.)` **set_hit_from_inside**(value: `bool`)
- `bool` **is_hit_from_inside_enabled**()

If `true`, the query will detect a hit when starting inside shapes. In this case the collision normal will be `Vector2(0, 0)`. Does not affect concave polygon shapes.

`Vector2` **to** = `Vector2(0, 0)`

- `void (No return value.)` **set_to**(value: `Vector2`)
- `Vector2` **get_to**()

The ending point of the ray being queried for, in global coordinates.

## Method Descriptions

`PhysicsRayQueryParameters2D` **create**(from: `Vector2`, to: `Vector2`, collision_mask: `int` = 4294967295, exclude: `Array`\[`RID`\] = \[\]) `static (This method doesn't need an instance to be called, so it can be called directly using the class name.)`

Returns a new, pre-configured **PhysicsRayQueryParameters2D** object. Use it to quickly create query parameters using the most common options.

    var query = PhysicsRayQueryParameters2D.create(global_position, global_position + Vector2(0, 100))
    var collision = get_world_2d().direct_space_state.intersect_ray(query)