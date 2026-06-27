# OpenXRActionSet

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Collection of `OpenXRAction` resources that make up an action set.

## Description

Action sets in OpenXR define a collection of actions that can be activated in unison. This allows games to easily change between different states that require different inputs or need to reinterpret inputs. For instance we could have an action set that is active when a menu is open, an action set that is active when the player is freely walking around and an action set that is active when the player is controlling a vehicle.

Action sets can contain the same action with the same name, if such action sets are active at the same time the action set with the highest priority defines which binding is active.

## Property Descriptions

`Array` **actions** = `[]`

- `void (No return value.)` **set_actions**(value: `Array`)
- `Array` **get_actions**()

Collection of actions for this action set.

`String` **localized_name** = `""`

- `void (No return value.)` **set_localized_name**(value: `String`)
- `String` **get_localized_name**()

The localized name of this action set.

`int` **priority** = `0`

- `void (No return value.)` **set_priority**(value: `int`)
- `int` **get_priority**()

The priority for this action set.

## Method Descriptions

`void (No return value.)` **add_action**(action: `OpenXRAction`)

Add an action to this action set.

`int` **get_action_count**() `const`

Retrieve the number of actions in our action set.

`void (No return value.)` **remove_action**(action: `OpenXRAction`)

Remove an action from this action set.