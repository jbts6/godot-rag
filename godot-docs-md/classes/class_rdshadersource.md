# RDShaderSource

**Inherits:** `RefCounted` **<** `Object`

Shader source code (used by `RenderingDevice`).

## Description

Shader source code in text form.

See also `RDShaderFile`. **RDShaderSource** is only meant to be used with the `RenderingDevice` API. It should not be confused with Godot's own `Shader` resource, which is what Godot's various nodes use for high-level shader programming.

## Property Descriptions

`ShaderLanguage` **language** = `0`

- `void (No return value.)` **set_language**(value: `ShaderLanguage`)
- `ShaderLanguage` **get_language**()

The language the shader is written in.

`String` **source_any_hit** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's any hit stage.

`String` **source_closest_hit** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's closest hit stage.

`String` **source_compute** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's compute stage.

`String` **source_fragment** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's fragment stage.

`String` **source_intersection** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's intersection stage.

`String` **source_miss** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's miss stage.

`String` **source_raygen** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's ray generation stage.

`String` **source_tesselation_control** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's tessellation control stage.

`String` **source_tesselation_evaluation** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's tessellation evaluation stage.

`String` **source_vertex** = `""`

- `void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)
- `String` **get_stage_source**(stage: `ShaderStage`) `const`

Source code for the shader's vertex stage.

## Method Descriptions

`String` **get_stage_source**(stage: `ShaderStage`) `const`

Returns source code for the specified shader `stage`. Equivalent to getting one of `source_compute`, `source_fragment`, `source_tesselation_control`, `source_tesselation_evaluation` or `source_vertex`.

`void (No return value.)` **set_stage_source**(stage: `ShaderStage`, source: `String`)

Sets `source` code for the specified shader `stage`. Equivalent to setting one of `source_compute`, `source_fragment`, `source_tesselation_control`, `source_tesselation_evaluation` or `source_vertex`.

**Note:** If you set the compute shader source code using this method directly, remember to remove the Godot-specific hint `#[compute]`.