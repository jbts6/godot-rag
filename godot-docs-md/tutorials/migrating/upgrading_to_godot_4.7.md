# Upgrading from Godot 4.6 to Godot 4.7

For most games and apps made with 4.6 it should be relatively safe to migrate to 4.7. This page intends to cover everything you need to pay attention to when migrating your project.

## Breaking changes

If you are migrating from 4.6 to 4.7, the breaking changes listed here might affect you. Changes are grouped by areas/systems.

This article indicates whether each breaking change affects GDScript and whether the C# breaking change is *binary compatible* or *source compatible*:

- **Binary compatible** - Existing binaries will load and execute successfully without recompilation, and the runtime behavior won't change.
- **Source compatible** - Source code will compile successfully without changes when upgrading Godot.

### Core

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **Object** |  |  |  |  |
| Method `is_class` changes `class` parameter type from `String` to `StringName` | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -118582\`\_ |
| **ZIPPacker** |  |  |  |  |
| Method `start_file` adds new `permissions` and `modified_time` optional parameters | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -115946\`\_ |
| **OptimizedTranslation** |  |  |  |  |
| Method `generate` changes return type from `void` to `bool` | `✔️ (This API does not break compatibility.)` \| | ❌\| \| | ✔️\| \`G | H-119563\`\_ |

### 2D

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **CPUParticles2D** |  |  |  |  |
| Method `request_particles_process` adds new `process_time_residual` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -109142\`\_ |
| **GPUParticles2D** |  |  |  |  |
| Method `request_particles_process` adds new `process_time_residual` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -109142\`\_ |

### 3D

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **CPUParticles3D** |  |  |  |  |
| Method `request_particles_process` adds new `process_time_residual` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -109142\`\_ |
| **GPUParticles3D** |  |  |  |  |
| Method `request_particles_process` adds new `process_time_residual` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -109142\`\_ |

### GUI nodes

<table>

<tr>
<th>Change</th>
<th>GDScript Compatible</th>
<th>C# Binary Compatible</th>
<th>C# Source Compatible</th>
<th>Introduced</th>
</tr>

<tr>
<td><strong>Control</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Property <code>accessibility_live</code> changes type from <code>DisplayServer.AccessibilityLiveMode</code> to <code>AccessibilityServer.AccessibilityLiveMode</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>❌| |</td>
<td>❌| `</td>
<td>GH-116839`_</td>
</tr>
<tr>
<td><strong>RichTextLabel</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Enum field <code>ImageUpdateMask.UPDATE_WIDTH_IN_PERCENT</code> renamed to <code>ImageUpdateMask.UPDATE_WIDTH_UNIT</code></td>
<td><code class="interpreted-text" role="abbr">❌ (This API breaks compatibility.)</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>❌| `</td>
<td>GH-112617`_</td>
</tr>
<tr>
<td>Method <code>add_image</code> changes <code>width</code> parameter type from <code>int</code> to <code>float</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>add_image</code> changes <code>height</code> parameter type from <code>int</code> to <code>float</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>add_image</code> renames <code>width_in_percent</code> parameter to <code>width_unit</code> and changes type from <code>bool</code> to <code>RichTextLabel.ImageUnit</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |❌</td>
<td>                 `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>add_image</code> renames <code>height_in_percent</code> parameter to <code>height_unit</code> and changes type from <code>bool</code> to <code>RichTextLabel.ImageUnit</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |❌</td>
<td>                 `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>update_image</code> changes <code>width</code> parameter type from <code>int</code> to <code>float</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>update_image</code> changes <code>height</code> parameter type from <code>int</code> to <code>float</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>update_image</code> renames <code>width_in_percent</code> parameter to <code>width_unit</code> and changes type from <code>bool</code> to <code>RichTextLabel.ImageUnit</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |❌</td>
<td>                 `GH</td>
<td>-112617`_</td>
</tr>
<tr>
<td>Method <code>update_image</code> renames <code>height_in_percent</code> parameter to <code>height_unit</code> and changes type from <code>bool</code> to <code>RichTextLabel.ImageUnit</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |❌</td>
<td>                 `GH</td>
<td>-112617`_</td>
</tr>

</table>

### Text

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **Font** |  |  |  |  |
| Method `find_variation` adds new `palette_index` and `custom_colors` optional parameters | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -117149\`\_ |
| **TreeItem** |  |  |  |  |
| Method `select` adds new `set_as_cursor` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -119367\`\_ |

### Rendering

<table>

<tr>
<th>Change</th>
<th>GDScript Compatible</th>
<th>C# Binary Compatible</th>
<th>C# Source Compatible</th>
<th>Introduced</th>
</tr>

<tr>
<td><strong>Image</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Method <code>save_exr</code> adds new <code>color_image</code> and <code>max_linear_value</code> optional parameters</td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-117800`_</td>
</tr>
<tr>
<td>Method <code>save_exr_to_buffer</code> adds new <code>color_image</code> and <code>max_linear_value</code> optional parameters</td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-117800`_</td>
</tr>
<tr>
<td><strong>ImageTexture</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Method <code>get_format</code> moved to base class <code>Texture2D</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |✔</td>
<td>️| `GH</td>
<td>-109004`_</td>
</tr>
<tr>
<td><strong>PortableCompressedTexture2D</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Method <code>get_format</code> moved to base class <code>Texture2D</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |✔</td>
<td>️| `GH</td>
<td>-109004`_</td>
</tr>
<tr>
<td><strong>RenderingServer</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Method <code>particles_request_process_time</code> renames <code>time</code> parameter to <code>process_time</code> and adds new <code>process_time_residual</code> optional parameter</td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |❌</td>
<td>                 `GH</td>
<td>-109142`_</td>
</tr>
<tr>
<td>Method <code>viewport_set_size</code> adds new <code>view_count</code> optional parameter</td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️ with compat| |✔</td>
<td>️| `GH</td>
<td>-115799`_</td>
</tr>

</table>

### Animation

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **Animation** |  |  |  |  |
| Property `length` changes type metadata from `float` to `double` | `✔️ (This API does not break compatibility.)` \| | ❌\| \| | ❌\| \` | GH-116394\`\_ |
| **AnimationNodeBlendSpace1D** |  |  |  |  |
| Method `add_blend_point` adds new `name` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -110369\`\_ |
| **AnimationNodeBlendSpace2D** |  |  |  |  |
| Method `add_blend_point` adds new `name` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -110369\`\_ |

### Physics

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **PhysicsServer2D** |  |  |  |  |
| Method `body_set_shape_as_one_way_collision` adds new `direction` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -104736\`\_ |
| **PhysicsServer2DExtension** |  |  |  |  |
| Method `_body_set_shape_as_one_way_collision` adds new `direction` parameter | `❌ (This API breaks compatibility.)` | `❌ (This API breaks compatibility.)` | `❌ (This API breaks compatibility.)` | [GH-104736](https://github.com/godotengine/godot/pull/104736) |

### Audio

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **AudioEffectSpectrumAnalyzer** |  |  |  |  |
| Property `tap_back_pos` removed | `❌ (This API breaks compatibility.)` | `❌ (This API breaks compatibility.)` | `❌ (This API breaks compatibility.)` | [GH-114355](https://github.com/godotengine/godot/pull/114355) |

### XR

| Change | GDScript Compatible | C# Binary Compatible | C# Source Compatible | Introduced |

| **OpenXRExtensionWrapper** |  |  |  |  |
| Method `_on_register_metadata` adds new `interaction_profile_metadata` parameter | `❌ (This API breaks compatibility.)` | `❌ (This API breaks compatibility.)` | `❌ (This API breaks compatibility.)` | [GH-117399](https://github.com/godotengine/godot/pull/117399) |
| **OpenXRSpatialAnchorCapability** |  |  |  |  |
| Method `create_new_anchor` adds new `next` optional parameter | `✔️ (This API does not break compatibility.)` \| | ✔️ with compat\| \|✔ | ️\| \`GH | -118128\`\_ |

### Editor

<table>

<tr>
<th>Change</th>
<th>GDScript Compatible</th>
<th>C# Binary Compatible</th>
<th>C# Source Compatible</th>
<th>Introduced</th>
</tr>

<tr>
<td><strong>EditorSceneFormatImporter</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Constant <code>IMPORT_ANIMATION</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td>Constant <code>IMPORT_DISCARD_MESHES_AND_MATERIALS</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td>Constant <code>IMPORT_FAIL_ON_MISSING_DEPENDENCIES</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td>Constant <code>IMPORT_FORCE_DISABLE_MESH_COMPRESSION</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td>Constant <code>IMPORT_GENERATE_TANGENT_ARRAYS</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td>Constant <code>IMPORT_SCENE</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td>Constant <code>IMPORT_USE_NAMED_SKIN_BINDS</code> moved to enum <code>ImportFlags</code></td>
<td><code class="interpreted-text" role="abbr">✔️ (This API does not break compatibility.)</code> |</td>
<td>✔️| |❌</td>
<td>                 `GH</td>
<td>-115788`_</td>
</tr>
<tr>
<td><strong>EditorVCSInterface</strong></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Method <code>_commit</code> adds new <code>amend</code> parameter</td>
<td><code class="interpreted-text" role="abbr">❌ (This API breaks compatibility.)</code></td>
<td><code class="interpreted-text" role="abbr">❌ (This API breaks compatibility.)</code></td>
<td><code class="interpreted-text" role="abbr">❌ (This API breaks compatibility.)</code></td>
<td><a href="https://github.com/godotengine/godot/pull/117968">GH-117968</a></td>
</tr>

</table>

## Behavior changes

### Rendering

> [!NOTE]
> The `LinearToSRGB` visual shader no longer clamps to the range `[0.0, 1.0]` when using the Mobile or Forward+ renderer ([GH-113956](https://github.com/godotengine/godot/pull/113956)).

> [!NOTE]
> `CanvasItem` now avoids adding the antialiasing feather when drawing lines ([GH-105122](https://github.com/godotengine/godot/pull/105122)). The feather made lines appear thicker than intended, projects that relied on this behavior will have to be updated to draw a thicker line width.

### Physics

> [!NOTE]
> The default `area_mask` for `AudioStreamPlayer` was changed from `1` to `0` (disabled) ([GH-107679](https://github.com/godotengine/godot/pull/107679)). If you use the `audio_bus_override` feature on `Area2D` or `Area3D`, **and** you use the `AudioStreamPlayer` default `area_mask` (just layer `1` ticked), you will need to reset the mask to layer `1` — otherwise, the bus overrides will stop working. If the mask was set to anything except layer `1`, it will continue to work as expected.

> [!NOTE]
> When using Jolt Physics as the 3D physics engine, `WorldBoundaryShape3D` will now use the same convention as Godot when applying `WorldBoundaryShape3D.plane.d`, resulting in the sign of the plane distance being interpreted in the opposite way compared to Godot 4.6 ([GH-118948](https://github.com/godotengine/godot/pull/118948)). You will need to flip the sign yourself to get the same behavior as in Godot 4.6.

> [!NOTE]
> When using Jolt Physics as the 3D physics engine, `SoftBody3D` will no longer default its mass to `0`, which resulted in an automatically calculated weight of 1 kg per point, resulting in a very high total mass for the body. Now instead it will default to 1 kg for the entire `SoftBody3D`, same as Godot Physics ([GH-116041](https://github.com/godotengine/godot/pull/116041)).

> [!NOTE]
> When using Jolt Physics as the 3D physics engine, `SoftBody3D` will now apply `SoftBody3D.linear_stiffness` in a way that better matches Godot Physics, and in a way that's more appropriate in general ([GH-116041](https://github.com/godotengine/godot/pull/116041)). This will affect every `SoftBody3D` instance in one way or another, meaning you will need to re-tweak properties like `SoftBody3D.linear_stiffness` and `SoftBody3D.damping_coefficient` to achieve your desired behavior.

> [!NOTE]
> When using Jolt Physics as the 3D physics engine, `Area3D` will now report overlaps with `SoftBody3D` from its various signals and methods ([GH-114198](https://github.com/godotengine/godot/pull/114198)). To work around this breaking change, configure your collision layers/masks such that any undesirable interactions between `Area3D` and `SoftBody3D` are ignored.

### Input

> [!NOTE]
> The device IDs for mouse and keyboard were changed from `0` to `InputEvent.DEVICE_ID_MOUSE` and `InputEvent.DEVICE_ID_KEYBOARD` because some joypads may use `0` as their ID ([GH-116274](https://github.com/godotengine/godot/pull/116274)). Check the input event by type or compare the device ID `InputEvent.device` to the constants `InputEvent.DEVICE_ID_MOUSE` and `InputEvent.DEVICE_ID_KEYBOARD` instead.

### GDScript

> [!NOTE]
> Setting the element of packed arrays no longer calls the setter for the entire packed array property ([GH-113228](https://github.com/godotengine/godot/pull/113228)).

> [!NOTE]
> Methods that inherit from a method with a typed return now inherit the return type as well, requiring an explicit return statement in the override ([GH-115763](https://github.com/godotengine/godot/pull/115763)). Add `return null` to the end of the method to fix the error.

## Changed defaults

The following default values have been changed. If your project uses any of these properties with their default value, you can achieve a similar behavior to the previous version by manually setting the values to match the old defaults.

> [!NOTE]
> The default stretch mode and stretch aspect for **newly created** projects is now `canvas_items` and `expand` respectively (previously `disabled` and `keep`). This can be changed in the Project Settings under `display/window/stretch/mode` and `display/window/stretch/aspect`.

### Animation

| Property/Parameter   | Old Default | New Default |

| **LookAtModifier3D** |             |             |
| Property `relative`  | true        | false       |

### Core

| Property/Parameter | Old Default | New Default |

| **ProjectSettings** |  |  |
| Property `rendering/reflections/sky_reflections/roughness_layers` | 7 | 8 |

### GUI nodes

| Property/Parameter | Old Default | New Default |

| **RichTextLabel** |  |  |
| Method `add_image` parameter `width_in_percent` | false | 0 |
| Method `add_image` parameter `height_in_percent` | false | 0 |
| Method `update_image` parameter `width_in_percent` | false | 0 |
| Method `update_image` parameter `height_in_percent` | false | 0 |

### Import

| Property/Parameter              | Old Default | New Default |

| **ResourceImporterDynamicFont** |             |             |
| Property `hinting`              | 1           | 3           |