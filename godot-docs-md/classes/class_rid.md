# RID

A handle for a `Resource`'s unique identifier.

## Description

The RID `Variant` type is used to access a low-level resource by its unique ID. RIDs are opaque, which means they do not grant access to the resource by themselves. They are used by the low-level server classes, such as `DisplayServer`, `RenderingServer`, `TextServer`, etc.

A low-level resource may correspond to a high-level `Resource`, such as `Texture` or `Mesh`.

**Note:** RIDs are only useful during the current session. It won't correspond to a similar resource if sent over a network, or loaded from a file at a later time.

**Note:** In a boolean context, an RID will evaluate to `false` if it has the invalid ID `0`. Otherwise, an RID will always evaluate to `true`. This is equivalent to calling `is_valid()`.

> [!NOTE]
> There are notable differences when using this API with C#. See `doc_c_sharp_differences` for more information.

## Constructor Descriptions

`RID` **RID**()

Constructs an empty **RID** with the invalid ID `0`.

`RID` **RID**(from: `RID`)

Constructs an **RID** as a copy of the given **RID**.

## Method Descriptions

`int` **get_id**() `const`

Returns the ID of the referenced low-level resource.

`bool` **is_valid**() `const`

Returns `true` if the **RID** is not `0`.

## Operator Descriptions

`bool` **operator !=**(right: `RID`)

Returns `true` if the **RID**s are not equal.

`bool` **operator <**(right: `RID`)

Returns `true` if the **RID**'s ID is less than `right`'s ID.

`bool` **operator <=**(right: `RID`)

Returns `true` if the **RID**'s ID is less than or equal to `right`'s ID.

`bool` **operator ==**(right: `RID`)

Returns `true` if both **RID**s are equal, which means they both refer to the same low-level resource.

`bool` **operator \>**(right: `RID`)

Returns `true` if the **RID**'s ID is greater than `right`'s ID.

`bool` **operator \>=**(right: `RID`)

Returns `true` if the **RID**'s ID is greater than or equal to `right`'s ID.