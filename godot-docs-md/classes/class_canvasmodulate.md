# CanvasModulate

**Inherits:** `Node2D` **<** `CanvasItem` **<** `Node` **<** `Object`

A node that applies a color tint to a canvas.

## Description

**CanvasModulate** applies a color tint to all nodes on a canvas. Only one can be used to tint a canvas, but `CanvasLayer`s can be used to render things independently.

## Tutorials

- `2D lights and shadows `

## Property Descriptions

`Color` **color** = `Color(1, 1, 1, 1)`

- `void (No return value.)` **set_color**(value: `Color`)
- `Color` **get_color**()

The tint color to apply.