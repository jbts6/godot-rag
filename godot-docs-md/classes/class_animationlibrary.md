# AnimationLibrary

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Container for `Animation` resources.

## Description

An animation library stores a set of animations accessible through `StringName` keys, for use with `AnimationPlayer` nodes.

## Tutorials

- `Animation tutorial index `

## Signals

**animation_added**(anim_name: `StringName`)

Emitted when an `Animation` is added, under the key `anim_name`.

**animation_changed**(anim_name: `StringName`)

Emitted when there's a change in one of the animations, e.g. tracks are added, moved or have changed paths. `anim_name` is the key of the animation that was changed.

See also `Resource.changed`, which this acts as a relay for.

**animation_removed**(anim_name: `StringName`)

Emitted when an `Animation` stored with the key `anim_name` is removed.

**animation_renamed**(old_name: `StringName`, new_name: `StringName`)

Emitted when the key for an `Animation` is changed, from `old_name` to `new_name`.

## Method Descriptions

`Error` **add_animation**(name: `StringName`, animation: `Animation`)

Adds the `animation` to the library, accessible by the key `name`.

`Animation` **get_animation**(name: `StringName`) `const`

Returns the `Animation` with the key `name`. If the animation does not exist, `null` is returned and an error is logged.

`Array`\[`StringName`\] **get_animation_list**() `const`

Returns the keys for the `Animation`s stored in the library.

`int` **get_animation_list_size**() `const`

Returns the key count for the `Animation`s stored in the library.

`bool` **has_animation**(name: `StringName`) `const`

Returns `true` if the library stores an `Animation` with `name` as the key.

`void (No return value.)` **remove_animation**(name: `StringName`)

Removes the `Animation` with the key `name`.

`void (No return value.)` **rename_animation**(name: `StringName`, newname: `StringName`)

Changes the key of the `Animation` associated with the key `name` to `newname`.