# OpenXRBindingModifier

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `OpenXRActionBindingModifier`, `OpenXRIPBindingModifier`

Binding modifier base class.

## Description

Binding modifier base class. Subclasses implement various modifiers that alter how an OpenXR runtime processes inputs.

## Method Descriptions

`String` **\_get_description**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Return the description of this class that is used for the title bar of the binding modifier editor.

`PackedByteArray` **\_get_ip_modification**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Returns the data that is sent to OpenXR when submitting the suggested interacting bindings this modifier is a part of.

**Note:** This must be data compatible with an `XrBindingModificationBaseHeaderKHR` structure.