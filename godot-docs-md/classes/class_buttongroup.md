# ButtonGroup

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

A group of buttons that doesn't allow more than one button to be pressed at a time.

## Description

A group of `BaseButton`-derived buttons. The buttons in a **ButtonGroup** are treated like radio buttons: No more than one button can be pressed at a time. Some types of buttons (such as `CheckBox`) may have a special appearance in this state.

Every member of a **ButtonGroup** should have `BaseButton.toggle_mode` set to `true`.

## Signals

**pressed**(button: `BaseButton`)

Emitted when one of the buttons of the group is pressed.

## Property Descriptions

`bool` **allow_unpress** = `false`

- `void (No return value.)` **set_allow_unpress**(value: `bool`)
- `bool` **is_allow_unpress**()

If `true`, it is possible to unpress all buttons in this **ButtonGroup**.

## Method Descriptions

`Array`\[`BaseButton`\] **get_buttons**()

Returns an `Array` of `Button`s who have this as their **ButtonGroup** (see `BaseButton.button_group`).

`BaseButton` **get_pressed_button**()

Returns the current pressed button.