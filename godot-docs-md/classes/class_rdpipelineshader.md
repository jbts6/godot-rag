# RDPipelineShader

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `RefCounted` **<** `Object`

Pipeline shader (used by `RenderingDevice`).

## Description

Wraps a shader resource and allows specialization constants to be applied at pipeline creation time.

Used by `RenderingDevice.raytracing_pipeline_create()` for ray generation, miss, and hit shaders. The pipeline selects the required shader stage automatically.

## Property Descriptions

`RID` **shader** = `RID()`

- `void (No return value.)` **set_shader**(value: `RID`)
- `RID` **get_shader**()

Shader resource. The required stage is selected by the pipeline.

`Array`\[`RDPipelineSpecializationConstant`\] **specialization_constants** = `[]`

- `void (No return value.)` **set_specialization_constants**(value: `Array`\[`RDPipelineSpecializationConstant`\])
- `Array`\[`RDPipelineSpecializationConstant`\] **get_specialization_constants**()

Specialization constants applied to the selected shader stage at pipeline creation time.