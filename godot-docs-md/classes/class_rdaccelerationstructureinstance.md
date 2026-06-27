# RDAccelerationStructureInstance

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `RefCounted` **<** `Object`

Acceleration structure instance (used by `RenderingDevice`).

## Description

**RDAccelerationStructureInstance** describes an instance of a Bottom-Level Acceleration Structure (BLAS) used in the `RenderingDevice.tlas_build()` method.

## Property Descriptions

`RID` **blas** = `RID()`

- `void (No return value.)` **set_blas**(value: `RID`)
- `RID` **get_blas**()

The BLAS referenced by this instance. If `null`, the instance is treated as a placeholder but still contributes to `gl_InstanceIndex` in GLSL.

`BitField (This value is an integer composed as a bitmask of the following flags.)`\[`AccelerationStructureInstanceFlagBits`\] **flags** = `0`

- `void (No return value.)` **set_flags**(value: `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`AccelerationStructureInstanceFlagBits`\])
- `BitField (This value is an integer composed as a bitmask of the following flags.)`\[`AccelerationStructureInstanceFlagBits`\] **get_flags**()

Flags for the instance.

`int` **hit_sbt_range** = `0`

- `void (No return value.)` **set_hit_sbt_range**(value: `int`)
- `int` **get_hit_sbt_range**()

Hit shader binding table range used for this instance, allocated using the `RenderingDevice.hit_sbt_range_alloc()` method.

`int` **id** = `0`

- `void (No return value.)` **set_id**(value: `int`)
- `int` **get_id**()

Custom instance ID that can be accessed in GLSL using `gl_InstanceCustomIndexEXT`.

`int` **mask** = `255`

- `void (No return value.)` **set_mask**(value: `int`)
- `int` **get_mask**()

Visibility mask used to control which rays can intersect this instance.

`Transform3D` **transform** = `Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)`

- `void (No return value.)` **set_transform**(value: `Transform3D`)
- `Transform3D` **get_transform**()

Transform applied to the referenced BLAS for this instance.