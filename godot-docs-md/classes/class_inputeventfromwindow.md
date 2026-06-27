# InputEventFromWindow

**Inherits:** `InputEvent` **<** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `InputEventScreenDrag`, `InputEventScreenTouch`, `InputEventWithModifiers`

Abstract base class for `Viewport`-based input events.

## Description

InputEventFromWindow represents events specifically received by windows. This includes mouse events, keyboard events in focused windows or touch screen actions.

## Property Descriptions

`int` **window_id** = `0`

- `void (No return value.)` **set_window_id**(value: `int`)
- `int` **get_window_id**()

The ID of a `Window` that received this event.