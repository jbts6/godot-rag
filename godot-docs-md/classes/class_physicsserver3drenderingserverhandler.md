# PhysicsServer3DRenderingServerHandler

**Inherits:** `Object`

A class used to provide `PhysicsServer3DExtension._soft_body_update_rendering_server()` with a rendering handler for soft bodies.

## Method Descriptions

`void (No return value.)` **\_set_aabb**(aabb: `AABB`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called by the `PhysicsServer3D` to set the bounding box for the `SoftBody3D`.

`void (No return value.)` **\_set_normal**(vertex_id: `int`, normal: `Vector3`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called by the `PhysicsServer3D` to set the normal for the `SoftBody3D` vertex at the index specified by `vertex_id`.

**Note:** The `normal` parameter used to be of type `const void*` prior to Godot 4.2.

`void (No return value.)` **\_set_vertex**(vertex_id: `int`, vertex: `Vector3`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called by the `PhysicsServer3D` to set the position for the `SoftBody3D` vertex at the index specified by `vertex_id`.

**Note:** The `vertex` parameter used to be of type `const void*` prior to Godot 4.2.

`void (No return value.)` **set_aabb**(aabb: `AABB`)

Sets the bounding box for the `SoftBody3D`.

`void (No return value.)` **set_normal**(vertex_id: `int`, normal: `Vector3`)

Sets the normal for the `SoftBody3D` vertex at the index specified by `vertex_id`.

`void (No return value.)` **set_vertex**(vertex_id: `int`, vertex: `Vector3`)

Sets the position for the `SoftBody3D` vertex at the index specified by `vertex_id`.