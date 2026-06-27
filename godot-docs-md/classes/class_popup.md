# Popup

**Inherits:** `Window` **<** `Viewport` **<** `Node` **<** `Object`

**Inherited By:** `PopupMenu`, `PopupPanel`

Base class for contextual windows and panels with fixed position.

## Description

**Popup** is a base class for contextual windows and panels with fixed position. It's a modal by default (see `Window.popup_window`) and provides methods for implementing custom popup behavior.

**Note:** **Popup** is invisible by default. To make it visible, call one of the `popup_*` methods from `Window` on the node, such as `Window.popup_centered_clamped()`.

## Signals

**popup_hide**()

Emitted when the popup is hidden.