# UniformSetCacheRD

**Inherits:** `Object`

Uniform set cache manager for Rendering Device based renderers.

## Description

Uniform set cache manager for `RenderingDevice`-based renderers. Provides a way to create a uniform set and reuse it in subsequent calls for as long as the uniform set exists. Uniform set will automatically be cleaned up when dependent objects are freed.

## Method Descriptions

`RID` **get_cache**(shader: `RID`, set: `int`, uniforms: `Array`\[`RDUniform`\]) `static (This method doesn't need an instance to be called, so it can be called directly using the class name.)`

Creates/returns a cached uniform set based on the provided uniforms for a given shader.