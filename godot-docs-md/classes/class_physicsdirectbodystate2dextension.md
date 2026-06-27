# PhysicsDirectBodyState2DExtension

**Inherits:** `PhysicsDirectBodyState2D` **<** `Object`

Provides virtual methods that can be overridden to create custom `PhysicsDirectBodyState2D` implementations.

## Description

This class extends `PhysicsDirectBodyState2D` by providing additional virtual methods that can be overridden. When these methods are overridden, they will be called instead of the internal methods of the physics server.

Intended for use with GDExtension to create custom implementations of `PhysicsDirectBodyState2D`.

## Method Descriptions

`void (No return value.)` **\_add_constant_central_force**(force: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.add_constant_central_force()`.

`void (No return value.)` **\_add_constant_force**(force: `Vector2`, position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.add_constant_force()`.

`void (No return value.)` **\_add_constant_torque**(torque: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.add_constant_torque()`.

`void (No return value.)` **\_apply_central_force**(force: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.apply_central_force()`.

`void (No return value.)` **\_apply_central_impulse**(impulse: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.apply_central_impulse()`.

`void (No return value.)` **\_apply_force**(force: `Vector2`, position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.apply_force()`.

`void (No return value.)` **\_apply_impulse**(impulse: `Vector2`, position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.apply_impulse()`.

`void (No return value.)` **\_apply_torque**(torque: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.apply_torque()`.

`void (No return value.)` **\_apply_torque_impulse**(impulse: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.apply_torque_impulse()`.

`float` **\_get_angular_velocity**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.angular_velocity` and its respective getter.

`Vector2` **\_get_center_of_mass**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.center_of_mass` and its respective getter.

`Vector2` **\_get_center_of_mass_local**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.center_of_mass_local` and its respective getter.

`int` **\_get_collision_layer**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`int` **\_get_collision_mask**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`Vector2` **\_get_constant_force**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_constant_force()`.

`float` **\_get_constant_torque**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_constant_torque()`.

`RID` **\_get_contact_collider**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_collider()`.

`int` **\_get_contact_collider_id**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_collider_id()`.

`Object` **\_get_contact_collider_object**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_collider_object()`.

`Vector2` **\_get_contact_collider_position**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_collider_position()`.

`int` **\_get_contact_collider_shape**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_collider_shape()`.

`Vector2` **\_get_contact_collider_velocity_at_position**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_collider_velocity_at_position()`.

`int` **\_get_contact_count**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_count()`.

`Vector2` **\_get_contact_impulse**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_impulse()`.

`Vector2` **\_get_contact_local_normal**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_local_normal()`.

`Vector2` **\_get_contact_local_position**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_local_position()`.

`int` **\_get_contact_local_shape**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_local_shape()`.

`Vector2` **\_get_contact_local_velocity_at_position**(contact_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_contact_local_velocity_at_position()`.

`float` **\_get_inverse_inertia**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.inverse_inertia` and its respective getter.

`float` **\_get_inverse_mass**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.inverse_mass` and its respective getter.

`Vector2` **\_get_linear_velocity**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.linear_velocity` and its respective getter.

`PhysicsDirectSpaceState2D` **\_get_space_state**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.get_space_state()`.

`float` **\_get_step**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.step` and its respective getter.

`float` **\_get_total_angular_damp**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.total_angular_damp` and its respective getter.

`Vector2` **\_get_total_gravity**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.total_gravity` and its respective getter.

`float` **\_get_total_linear_damp**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.total_linear_damp` and its respective getter.

`Transform2D` **\_get_transform**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.transform` and its respective getter.

`Vector2` **\_get_velocity_at_local_position**(local_position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsDirectBodyState2D.get_velocity_at_local_position()`.

`void (No return value.)` **\_integrate_forces**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.integrate_forces()`.

`bool` **\_is_sleeping**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Implement to override the behavior of `PhysicsDirectBodyState2D.sleeping` and its respective getter.

`void (No return value.)` **\_set_angular_velocity**(velocity: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Implement to override the behavior of `PhysicsDirectBodyState2D.angular_velocity` and its respective setter.

`void (No return value.)` **\_set_collision_layer**(layer: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`void (No return value.)` **\_set_collision_mask**(mask: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`void (No return value.)` **\_set_constant_force**(force: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.set_constant_force()`.

`void (No return value.)` **\_set_constant_torque**(torque: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsDirectBodyState2D.set_constant_torque()`.

`void (No return value.)` **\_set_linear_velocity**(velocity: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Implement to override the behavior of `PhysicsDirectBodyState2D.linear_velocity` and its respective setter.

`void (No return value.)` **\_set_sleep_state**(enabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Implement to override the behavior of `PhysicsDirectBodyState2D.sleeping` and its respective setter.

`void (No return value.)` **\_set_transform**(transform: `Transform2D`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Implement to override the behavior of `PhysicsDirectBodyState2D.transform` and its respective setter.