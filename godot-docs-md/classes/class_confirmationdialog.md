# ConfirmationDialog

**Inherits:** `AcceptDialog` **<** `Window` **<** `Viewport` **<** `Node` **<** `Object`

**Inherited By:** `EditorCommandPalette`, `FileDialog`, `ScriptCreateDialog`

A dialog used for confirmation of actions.

## Description

A dialog used for confirmation of actions. This window is similar to `AcceptDialog`, but pressing its Cancel button can have a different outcome from pressing the OK button. The order of the two buttons varies depending on the host OS.

To get cancel action, you can use:

``` gdscript
get_cancel_button().pressed.connect(_on_canceled)
```

``` csharp
GetCancelButton().Pressed += OnCanceled;
```

**Note:** `AcceptDialog` is invisible by default. To make it visible, call one of the `popup_*` methods from `Window` on the node, such as `Window.popup_centered_clamped()`.

## Property Descriptions

`String` **cancel_button_text** = `"Cancel"`

- `void (No return value.)` **set_cancel_button_text**(value: `String`)
- `String` **get_cancel_button_text**()

The text displayed by the cancel button (see `get_cancel_button()`).

## Method Descriptions

`Button` **get_cancel_button**()

Returns the cancel button.

**Warning:** This is a required internal node, removing and freeing it may cause a crash. If you wish to hide it or any of its children, use their `CanvasItem.visible` property.