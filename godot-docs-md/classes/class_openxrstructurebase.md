# OpenXRStructureBase

**Inherits:** `RefCounted` **<** `Object`

**Inherited By:** `OpenXRSpatialContextPersistenceConfig`

Object for storing OpenXR structure data.

## Description

Object for storing OpenXR structure data that is passed when calling into OpenXR APIs.

## Property Descriptions

`OpenXRStructureBase` **next**

- `void (No return value.)` **set_next**(value: `OpenXRStructureBase`)
- `OpenXRStructureBase` **get_next**()

Setting another structure object here chains these structures together to extend the API functionality. Consult the OpenXR documentation for which structures can be used with a given API call.

## Method Descriptions

`int` **\_get_header**(next: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`int` **get_structure_type**()

Returns the structure type (OpenXR `XrStructureType`) used for this structure.