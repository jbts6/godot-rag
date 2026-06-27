# RDAttachmentFormat

**Inherits:** `RefCounted` **<** `Object`

Attachment format (used by `RenderingDevice`).

## Description

This object is used by `RenderingDevice`.

## Property Descriptions

`DataFormat` **format** = `36`

- `void (No return value.)` **set_format**(value: `DataFormat`)
- `DataFormat` **get_format**()

The attachment's data format.

`TextureSamples` **samples** = `0`

- `void (No return value.)` **set_samples**(value: `TextureSamples`)
- `TextureSamples` **get_samples**()

The number of samples used when sampling the attachment.

`int` **usage_flags** = `0`

- `void (No return value.)` **set_usage_flags**(value: `int`)
- `int` **get_usage_flags**()

The attachment's usage flags, which determine what can be done with it.