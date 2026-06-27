# SegmentShape2D

**Inherits:** `Shape2D` **<** `Resource` **<** `RefCounted` **<** `Object`

A 2D line segment shape used for physics collision.

## Description

A 2D line segment shape, intended for use in physics. Usually used to provide a shape for a `CollisionShape2D`.

## Property Descriptions

`Vector2` **a** = `Vector2(0, 0)`

- `void (No return value.)` **set_a**(value: `Vector2`)
- `Vector2` **get_a**()

The segment's first point position.

`Vector2` **b** = `Vector2(0, 10)`

- `void (No return value.)` **set_b**(value: `Vector2`)
- `Vector2` **get_b**()

The segment's second point position.