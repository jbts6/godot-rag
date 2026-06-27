# SkeletonModificationStack2D

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

A resource that holds a stack of `SkeletonModification2D`s.

## Description

This resource is used by the Skeleton and holds a stack of `SkeletonModification2D`s.

This controls the order of the modifications and how they are applied. Modification order is especially important for full-body IK setups, as you need to execute the modifications in the correct order to get the desired results. For example, you want to execute a modification on the spine *before* the arms on a humanoid skeleton.

This resource also controls how strongly all of the modifications are applied to the `Skeleton2D`.

## Property Descriptions

`bool` **enabled** = `false`

- `void (No return value.)` **set_enabled**(value: `bool`)
- `bool` **get_enabled**()

If `true`, the modification's in the stack will be called. This is handled automatically through the `Skeleton2D` node.

`int` **modification_count** = `0`

- `void (No return value.)` **set_modification_count**(value: `int`)
- `int` **get_modification_count**()

The number of modifications in the stack.

`float` **strength** = `1.0`

- `void (No return value.)` **set_strength**(value: `float`)
- `float` **get_strength**()

The interpolation strength of the modifications in stack. A value of `0` will make it where the modifications are not applied, a strength of `0.5` will be half applied, and a strength of `1` will allow the modifications to be fully applied and override the `Skeleton2D` `Bone2D` poses.

## Method Descriptions

`void (No return value.)` **add_modification**(modification: `SkeletonModification2D`)

Adds the passed-in `SkeletonModification2D` to the stack.

`void (No return value.)` **delete_modification**(mod_idx: `int`)

Deletes the `SkeletonModification2D` at the index position `mod_idx`, if it exists.

`void (No return value.)` **enable_all_modifications**(enabled: `bool`)

Enables all `SkeletonModification2D`s in the stack.

`void (No return value.)` **execute**(delta: `float`, execution_mode: `int`)

Executes all of the `SkeletonModification2D`s in the stack that use the same execution mode as the passed-in `execution_mode`, starting from index `0` to `modification_count`.

**Note:** The order of the modifications can matter depending on the modifications. For example, modifications on a spine should operate before modifications on the arms in order to get proper results.

`bool` **get_is_setup**() `const`

Returns a boolean that indicates whether the modification stack is setup and can execute.

`SkeletonModification2D` **get_modification**(mod_idx: `int`) `const`

Returns the `SkeletonModification2D` at the passed-in index, `mod_idx`.

`Skeleton2D` **get_skeleton**() `const`

Returns the `Skeleton2D` node that the SkeletonModificationStack2D is bound to.

`void (No return value.)` **set_modification**(mod_idx: `int`, modification: `SkeletonModification2D`)

Sets the modification at `mod_idx` to the passed-in modification, `modification`.

`void (No return value.)` **setup**()

Sets up the modification stack so it can execute. This function should be called by `Skeleton2D` and shouldn't be manually called unless you know what you are doing.