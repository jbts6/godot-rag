# IKModifier3D

**Inherits:** `SkeletonModifier3D` **<** `Node3D` **<** `Node` **<** `Object`

**Inherited By:** `ChainIK3D`, `TwoBoneIK3D`

A node for inverse kinematics which may modify more than one bone.

## Description

Base class of `SkeletonModifier3D`s that has some joint lists and applies inverse kinematics. This class has some structs, enums, and helper methods which are useful to solve inverse kinematics.

## Tutorials

- [Inverse Kinematics Returns to Godot 4.6 - IKModifier3D](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/#ikmodifier3d-and-7-child-classes)

## Property Descriptions

`bool` **mutable_bone_axes** = `true`

- `void (No return value.)` **set_mutable_bone_axes**(value: `bool`)
- `bool` **are_bone_axes_mutable**()

If `true`, the solver retrieves the bone axis from the bone pose every frame.

If `false`, the solver retrieves the bone axis from the bone rest and caches it, which increases performance slightly, but position changes in the bone pose made before processing this **IKModifier3D** are ignored.

## Method Descriptions

`void (No return value.)` **clear_settings**()

Clears all settings.

`int` **get_setting_count**() `const`

Returns the number of settings.

`void (No return value.)` **reset**()

Resets a state with respect to the current bone pose.

`void (No return value.)` **set_setting_count**(count: `int`)

Sets the number of settings.