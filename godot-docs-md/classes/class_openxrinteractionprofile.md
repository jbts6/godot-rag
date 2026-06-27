# OpenXRInteractionProfile

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Suggested bindings object for OpenXR.

## Description

This object stores suggested bindings for an interaction profile. Interaction profiles define the metadata for a tracked XR device such as an XR controller.

For more information see the [interaction profiles info in the OpenXR specification](https://www.khronos.org/registry/OpenXR/specs/1.0/html/xrspec.html#semantic-path-interaction-profiles).

## Property Descriptions

`Array` **binding_modifiers** = `[]`

- `void (No return value.)` **set_binding_modifiers**(value: `Array`)
- `Array` **get_binding_modifiers**()

Binding modifiers for this interaction profile.

`Array` **bindings** = `[]`

- `void (No return value.)` **set_bindings**(value: `Array`)
- `Array` **get_bindings**()

Action bindings for this interaction profile.

`String` **interaction_profile_path** = `""`

- `void (No return value.)` **set_interaction_profile_path**(value: `String`)
- `String` **get_interaction_profile_path**()

The interaction profile path identifying the XR device.

## Method Descriptions

`OpenXRIPBinding` **get_binding**(index: `int`) `const`

Retrieve the binding at this index.

`int` **get_binding_count**() `const`

Get the number of bindings in this interaction profile.

`OpenXRIPBindingModifier` **get_binding_modifier**(index: `int`) `const`

Get the `OpenXRBindingModifier` at this index.

`int` **get_binding_modifier_count**() `const`

Get the number of binding modifiers in this interaction profile.