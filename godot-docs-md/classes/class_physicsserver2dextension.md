# PhysicsServer2DExtension

**Inherits:** `PhysicsServer2D` **<** `Object`

Provides virtual methods that can be overridden to create custom `PhysicsServer2D` implementations.

## Description

This class extends `PhysicsServer2D` by providing additional virtual methods that can be overridden. When these methods are overridden, they will be called instead of the internal methods of the physics server.

Intended for use with GDExtension to create custom implementations of `PhysicsServer2D`.

## Method Descriptions

`void (No return value.)` **\_area_add_shape**(area: `RID`, shape: `RID`, transform: `Transform2D`, disabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_add_shape()`.

`void (No return value.)` **\_area_attach_canvas_instance_id**(area: `RID`, id: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_attach_canvas_instance_id()`.

`void (No return value.)` **\_area_attach_object_instance_id**(area: `RID`, id: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_attach_object_instance_id()`.

`void (No return value.)` **\_area_clear_shapes**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_clear_shapes()`.

`RID` **\_area_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_create()`.

`int` **\_area_get_canvas_instance_id**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_canvas_instance_id()`.

`int` **\_area_get_collision_layer**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_collision_layer()`.

`int` **\_area_get_collision_mask**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_collision_mask()`.

`int` **\_area_get_object_instance_id**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_object_instance_id()`.

`Variant` **\_area_get_param**(area: `RID`, param: `AreaParameter`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_param()`.

`RID` **\_area_get_shape**(area: `RID`, shape_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_shape()`.

`int` **\_area_get_shape_count**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_shape_count()`.

`Transform2D` **\_area_get_shape_transform**(area: `RID`, shape_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_shape_transform()`.

`RID` **\_area_get_space**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_space()`.

`Transform2D` **\_area_get_transform**(area: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.area_get_transform()`.

`void (No return value.)` **\_area_remove_shape**(area: `RID`, shape_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_remove_shape()`.

`void (No return value.)` **\_area_set_area_monitor_callback**(area: `RID`, callback: `Callable`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_area_monitor_callback()`.

`void (No return value.)` **\_area_set_collision_layer**(area: `RID`, layer: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_collision_layer()`.

`void (No return value.)` **\_area_set_collision_mask**(area: `RID`, mask: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_collision_mask()`.

`void (No return value.)` **\_area_set_monitor_callback**(area: `RID`, callback: `Callable`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_monitor_callback()`.

`void (No return value.)` **\_area_set_monitorable**(area: `RID`, monitorable: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_monitorable()`.

`void (No return value.)` **\_area_set_param**(area: `RID`, param: `AreaParameter`, value: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_param()`.

`void (No return value.)` **\_area_set_pickable**(area: `RID`, pickable: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

If set to `true`, allows the area with the given `RID` to detect mouse inputs when the mouse cursor is hovering on it.

Overridable version of `PhysicsServer2D`'s internal `area_set_pickable` method. Corresponds to `CollisionObject2D.input_pickable`.

`void (No return value.)` **\_area_set_shape**(area: `RID`, shape_idx: `int`, shape: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_shape()`.

`void (No return value.)` **\_area_set_shape_disabled**(area: `RID`, shape_idx: `int`, disabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_shape_disabled()`.

`void (No return value.)` **\_area_set_shape_transform**(area: `RID`, shape_idx: `int`, transform: `Transform2D`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_shape_transform()`.

`void (No return value.)` **\_area_set_space**(area: `RID`, space: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_space()`.

`void (No return value.)` **\_area_set_transform**(area: `RID`, transform: `Transform2D`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.area_set_transform()`.

`void (No return value.)` **\_body_add_collision_exception**(body: `RID`, excepted_body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_add_collision_exception()`.

`void (No return value.)` **\_body_add_constant_central_force**(body: `RID`, force: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_add_constant_central_force()`.

`void (No return value.)` **\_body_add_constant_force**(body: `RID`, force: `Vector2`, position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_add_constant_force()`.

`void (No return value.)` **\_body_add_constant_torque**(body: `RID`, torque: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_add_constant_torque()`.

`void (No return value.)` **\_body_add_shape**(body: `RID`, shape: `RID`, transform: `Transform2D`, disabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_add_shape()`.

`void (No return value.)` **\_body_apply_central_force**(body: `RID`, force: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_apply_central_force()`.

`void (No return value.)` **\_body_apply_central_impulse**(body: `RID`, impulse: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_apply_central_impulse()`.

`void (No return value.)` **\_body_apply_force**(body: `RID`, force: `Vector2`, position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_apply_force()`.

`void (No return value.)` **\_body_apply_impulse**(body: `RID`, impulse: `Vector2`, position: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_apply_impulse()`.

`void (No return value.)` **\_body_apply_torque**(body: `RID`, torque: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_apply_torque()`.

`void (No return value.)` **\_body_apply_torque_impulse**(body: `RID`, impulse: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_apply_torque_impulse()`.

`void (No return value.)` **\_body_attach_canvas_instance_id**(body: `RID`, id: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_attach_canvas_instance_id()`.

`void (No return value.)` **\_body_attach_object_instance_id**(body: `RID`, id: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_attach_object_instance_id()`.

`void (No return value.)` **\_body_clear_shapes**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_clear_shapes()`.

`bool` **\_body_collide_shape**(body: `RID`, body_shape: `int`, shape: `RID`, shape_xform: `Transform2D`, motion: `Vector2`, r_results: `void*`, result_max: `int`, r_result_count: `int32_t*`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Given a `body`, a `shape`, and their respective parameters, this method should return `true` if a collision between the two would occur, with additional details passed in `r_results`.

Overridable version of `PhysicsServer2D`'s internal `shape_collide` method. Corresponds to `PhysicsDirectSpaceState2D.collide_shape()`.

`RID` **\_body_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_create()`.

`int` **\_body_get_canvas_instance_id**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_canvas_instance_id()`.

`Array`\[`RID`\] **\_body_get_collision_exceptions**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Returns the `RID`s of all bodies added as collision exceptions for the given `body`. See also `_body_add_collision_exception()` and `_body_remove_collision_exception()`.

Overridable version of `PhysicsServer2D`'s internal `body_get_collision_exceptions` method. Corresponds to `PhysicsBody2D.get_collision_exceptions()`.

`int` **\_body_get_collision_layer**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_collision_layer()`.

`int` **\_body_get_collision_mask**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_collision_mask()`.

`float` **\_body_get_collision_priority**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_collision_priority()`.

`Vector2` **\_body_get_constant_force**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_constant_force()`.

`float` **\_body_get_constant_torque**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_constant_torque()`.

`float` **\_body_get_contacts_reported_depth_threshold**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D`'s internal `body_get_contacts_reported_depth_threshold` method.

**Note:** This method is currently unused by Godot's default physics implementation.

`CCDMode` **\_body_get_continuous_collision_detection_mode**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_continuous_collision_detection_mode()`.

`PhysicsDirectBodyState2D` **\_body_get_direct_state**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_get_direct_state()`.

`int` **\_body_get_max_contacts_reported**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_max_contacts_reported()`.

`BodyMode` **\_body_get_mode**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_mode()`.

`int` **\_body_get_object_instance_id**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_object_instance_id()`.

`Variant` **\_body_get_param**(body: `RID`, param: `BodyParameter`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_param()`.

`RID` **\_body_get_shape**(body: `RID`, shape_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_shape()`.

`int` **\_body_get_shape_count**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_shape_count()`.

`Transform2D` **\_body_get_shape_transform**(body: `RID`, shape_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_shape_transform()`.

`RID` **\_body_get_space**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_space()`.

`Variant` **\_body_get_state**(body: `RID`, state: `BodyState`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_get_state()`.

`bool` **\_body_is_omitting_force_integration**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_is_omitting_force_integration()`.

`void (No return value.)` **\_body_remove_collision_exception**(body: `RID`, excepted_body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_remove_collision_exception()`.

`void (No return value.)` **\_body_remove_shape**(body: `RID`, shape_idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_remove_shape()`.

`void (No return value.)` **\_body_reset_mass_properties**(body: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_reset_mass_properties()`.

`void (No return value.)` **\_body_set_axis_velocity**(body: `RID`, axis_velocity: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_axis_velocity()`.

`void (No return value.)` **\_body_set_collision_layer**(body: `RID`, layer: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_collision_layer()`.

`void (No return value.)` **\_body_set_collision_mask**(body: `RID`, mask: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_collision_mask()`.

`void (No return value.)` **\_body_set_collision_priority**(body: `RID`, priority: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_collision_priority()`.

`void (No return value.)` **\_body_set_constant_force**(body: `RID`, force: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_constant_force()`.

`void (No return value.)` **\_body_set_constant_torque**(body: `RID`, torque: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_constant_torque()`.

`void (No return value.)` **\_body_set_contacts_reported_depth_threshold**(body: `RID`, threshold: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D`'s internal `body_set_contacts_reported_depth_threshold` method.

**Note:** This method is currently unused by Godot's default physics implementation.

`void (No return value.)` **\_body_set_continuous_collision_detection_mode**(body: `RID`, mode: `CCDMode`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_continuous_collision_detection_mode()`.

`void (No return value.)` **\_body_set_force_integration_callback**(body: `RID`, callable: `Callable`, userdata: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_force_integration_callback()`.

`void (No return value.)` **\_body_set_max_contacts_reported**(body: `RID`, amount: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_max_contacts_reported()`.

`void (No return value.)` **\_body_set_mode**(body: `RID`, mode: `BodyMode`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_mode()`.

`void (No return value.)` **\_body_set_omit_force_integration**(body: `RID`, enable: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_omit_force_integration()`.

`void (No return value.)` **\_body_set_param**(body: `RID`, param: `BodyParameter`, value: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_param()`.

`void (No return value.)` **\_body_set_pickable**(body: `RID`, pickable: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

If set to `true`, allows the body with the given `RID` to detect mouse inputs when the mouse cursor is hovering on it.

Overridable version of `PhysicsServer2D`'s internal `body_set_pickable` method. Corresponds to `CollisionObject2D.input_pickable`.

`void (No return value.)` **\_body_set_shape**(body: `RID`, shape_idx: `int`, shape: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_shape()`.

`void (No return value.)` **\_body_set_shape_as_one_way_collision**(body: `RID`, shape_idx: `int`, enable: `bool`, margin: `float`, direction: `Vector2`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_shape_as_one_way_collision()`.

`void (No return value.)` **\_body_set_shape_disabled**(body: `RID`, shape_idx: `int`, disabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_shape_disabled()`.

`void (No return value.)` **\_body_set_shape_transform**(body: `RID`, shape_idx: `int`, transform: `Transform2D`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_shape_transform()`.

`void (No return value.)` **\_body_set_space**(body: `RID`, space: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_space()`.

`void (No return value.)` **\_body_set_state**(body: `RID`, state: `BodyState`, value: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.body_set_state()`.

`void (No return value.)` **\_body_set_state_sync_callback**(body: `RID`, callable: `Callable`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Assigns the `body` to call the given `callable` during the synchronization phase of the loop, before `_step()` is called. See also `_sync()`.

Overridable version of `PhysicsServer2D.body_set_state_sync_callback()`.

`bool` **\_body_test_motion**(body: `RID`, from: `Transform2D`, motion: `Vector2`, margin: `float`, collide_separation_ray: `bool`, recovery_as_collision: `bool`, r_result: `PhysicsServer2DExtensionMotionResult*`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.body_test_motion()`. Unlike the exposed implementation, this method does not receive all of the arguments inside a `PhysicsTestMotionParameters2D`.

`RID` **\_capsule_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.capsule_shape_create()`.

`RID` **\_circle_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.circle_shape_create()`.

`RID` **\_concave_polygon_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.concave_polygon_shape_create()`.

`RID` **\_convex_polygon_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.convex_polygon_shape_create()`.

`float` **\_damped_spring_joint_get_param**(joint: `RID`, param: `DampedSpringParam`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.damped_spring_joint_get_param()`.

`void (No return value.)` **\_damped_spring_joint_set_param**(joint: `RID`, param: `DampedSpringParam`, value: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.damped_spring_joint_set_param()`.

`void (No return value.)` **\_end_sync**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called to indicate that the physics server has stopped synchronizing. It is in the loop's iteration/physics phase, and can access physics objects even if running on a separate thread. See also `_sync()`.

Overridable version of `PhysicsServer2D`'s internal `end_sync` method.

`void (No return value.)` **\_finish**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the main loop finalizes to shut down the physics server. See also `MainLoop._finalize()` and `_init()`.

Overridable version of `PhysicsServer2D`'s internal `finish` method.

`void (No return value.)` **\_flush_queries**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called every physics step before `_step()` to process all remaining queries.

Overridable version of `PhysicsServer2D`'s internal `flush_queries` method.

`void (No return value.)` **\_free_rid**(rid: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.free_rid()`.

`int` **\_get_process_info**(process_info: `ProcessInfo`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.get_process_info()`.

`void (No return value.)` **\_init**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the main loop is initialized and creates a new instance of this physics server. See also `MainLoop._initialize()` and `_finish()`.

Overridable version of `PhysicsServer2D`'s internal `init` method.

`bool` **\_is_flushing_queries**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable method that should return `true` when the physics server is processing queries. See also `_flush_queries()`.

Overridable version of `PhysicsServer2D`'s internal `is_flushing_queries` method.

`void (No return value.)` **\_joint_clear**(joint: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_clear()`.

`RID` **\_joint_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_create()`.

`void (No return value.)` **\_joint_disable_collisions_between_bodies**(joint: `RID`, disable: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_disable_collisions_between_bodies()`.

`float` **\_joint_get_param**(joint: `RID`, param: `JointParam`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.joint_get_param()`.

`JointType` **\_joint_get_type**(joint: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.joint_get_type()`.

`bool` **\_joint_is_disabled_collisions_between_bodies**(joint: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.joint_is_disabled_collisions_between_bodies()`.

`void (No return value.)` **\_joint_make_damped_spring**(joint: `RID`, anchor_a: `Vector2`, anchor_b: `Vector2`, body_a: `RID`, body_b: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_make_damped_spring()`.

`void (No return value.)` **\_joint_make_groove**(joint: `RID`, a_groove1: `Vector2`, a_groove2: `Vector2`, b_anchor: `Vector2`, body_a: `RID`, body_b: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_make_groove()`.

`void (No return value.)` **\_joint_make_pin**(joint: `RID`, anchor: `Vector2`, body_a: `RID`, body_b: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_make_pin()`.

`void (No return value.)` **\_joint_set_param**(joint: `RID`, param: `JointParam`, value: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.joint_set_param()`.

`bool` **\_pin_joint_get_flag**(joint: `RID`, flag: `PinJointFlag`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.pin_joint_get_flag()`.

`float` **\_pin_joint_get_param**(joint: `RID`, param: `PinJointParam`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.pin_joint_get_param()`.

`void (No return value.)` **\_pin_joint_set_flag**(joint: `RID`, flag: `PinJointFlag`, enabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.pin_joint_set_flag()`.

`void (No return value.)` **\_pin_joint_set_param**(joint: `RID`, param: `PinJointParam`, value: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.pin_joint_set_param()`.

`RID` **\_rectangle_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.rectangle_shape_create()`.

`RID` **\_segment_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.segment_shape_create()`.

`RID` **\_separation_ray_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.separation_ray_shape_create()`.

`void (No return value.)` **\_set_active**(active: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.set_active()`.

`bool` **\_shape_collide**(shape_A: `RID`, xform_A: `Transform2D`, motion_A: `Vector2`, shape_B: `RID`, xform_B: `Transform2D`, motion_B: `Vector2`, r_results: `void*`, result_max: `int`, r_result_count: `int32_t*`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Given two shapes and their parameters, should return `true` if a collision between the two would occur, with additional details passed in `r_results`.

Overridable version of `PhysicsServer2D`'s internal `shape_collide` method. Corresponds to `PhysicsDirectSpaceState2D.collide_shape()`.

`float` **\_shape_get_custom_solver_bias**(shape: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Should return the custom solver bias of the given `shape`, which defines how much bodies are forced to separate on contact when this shape is involved.

Overridable version of `PhysicsServer2D`'s internal `shape_get_custom_solver_bias` method. Corresponds to `Shape2D.custom_solver_bias`.

`Variant` **\_shape_get_data**(shape: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.shape_get_data()`.

`ShapeType` **\_shape_get_type**(shape: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.shape_get_type()`.

`void (No return value.)` **\_shape_set_custom_solver_bias**(shape: `RID`, bias: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Should set the custom solver bias for the given `shape`. It defines how much bodies are forced to separate on contact.

Overridable version of `PhysicsServer2D`'s internal `shape_get_custom_solver_bias` method. Corresponds to `Shape2D.custom_solver_bias`.

`void (No return value.)` **\_shape_set_data**(shape: `RID`, data: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.shape_set_data()`.

`RID` **\_space_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.space_create()`.

`int` **\_space_get_contact_count**(space: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Should return how many contacts have occurred during the last physics step in the given `space`. See also `_space_get_contacts()` and `_space_set_debug_contacts()`.

Overridable version of `PhysicsServer2D`'s internal `space_get_contact_count` method.

`PackedVector2Array` **\_space_get_contacts**(space: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Should return the positions of all contacts that have occurred during the last physics step in the given `space`. See also `_space_get_contact_count()` and `_space_set_debug_contacts()`.

Overridable version of `PhysicsServer2D`'s internal `space_get_contacts` method.

`PhysicsDirectSpaceState2D` **\_space_get_direct_state**(space: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.space_get_direct_state()`.

`float` **\_space_get_param**(space: `RID`, param: `SpaceParameter`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.space_get_param()`.

`bool` **\_space_is_active**(space: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable version of `PhysicsServer2D.space_is_active()`.

`void (No return value.)` **\_space_set_active**(space: `RID`, active: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.space_set_active()`.

`void (No return value.)` **\_space_set_debug_contacts**(space: `RID`, max_contacts: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Used internally to allow the given `space` to store contact points, up to `max_contacts`. This is automatically set for the main `World2D`'s space when `SceneTree.debug_collisions_hint` is `true`, or by checking "Visible Collision Shapes" in the editor. Only works in debug builds.

Overridable version of `PhysicsServer2D`'s internal `space_set_debug_contacts` method.

`void (No return value.)` **\_space_set_param**(space: `RID`, param: `SpaceParameter`, value: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.space_set_param()`.

`void (No return value.)` **\_step**(step: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called every physics step to process the physics simulation. `step` is the time elapsed since the last physics step, in seconds. It is usually the same as the value returned by `Node.get_physics_process_delta_time()`.

Overridable version of `PhysicsServer2D`'s internal `step` method.

`void (No return value.)` **\_sync**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called to indicate that the physics server is synchronizing and cannot access physics states if running on a separate thread. See also `_end_sync()`.

Overridable version of `PhysicsServer2D`'s internal `sync` method.

`RID` **\_world_boundary_shape_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Overridable version of `PhysicsServer2D.world_boundary_shape_create()`.

`bool` **body_test_motion_is_excluding_body**(body: `RID`) `const`

Returns `true` if the body with the given `RID` is being excluded from `_body_test_motion()`. See also `Object.get_instance_id()`.

`bool` **body_test_motion_is_excluding_object**(object: `int`) `const`

Returns `true` if the object with the given instance ID is being excluded from `_body_test_motion()`. See also `Object.get_instance_id()`.