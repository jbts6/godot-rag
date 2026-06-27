# Compositor

**Experimental:** More customization of the rendering pipeline will be added in the future.

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Stores attributes used to customize how a Viewport is rendered.

## Description

The compositor resource stores attributes used to customize how a `Viewport` is rendered.

## Tutorials

- `The Compositor `

## Property Descriptions

`Array`\[`CompositorEffect`\] **compositor_effects** = `[]`

- `void (No return value.)` **set_compositor_effects**(value: `Array`\[`CompositorEffect`\])
- `Array`\[`CompositorEffect`\] **get_compositor_effects**()

The custom `CompositorEffect`s that are applied during rendering of viewports using this compositor.