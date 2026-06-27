# OpenXRInteractionProfileEditorBase

**Inherits:** `HBoxContainer` **<** `BoxContainer` **<** `Container` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`

**Inherited By:** `OpenXRInteractionProfileEditor`

Base class for editing interaction profiles.

## Description

This is a base class for interaction profile editors used by the OpenXR action map editor. It can be used to create bespoke editors for specific interaction profiles.

## Method Descriptions

`void (No return value.)` **setup**(action_map: `OpenXRActionMap`, interaction_profile: `OpenXRInteractionProfile`)

Setup this editor for the provided `action_map` and `interaction_profile`.