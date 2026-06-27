# OpenXRAnalogThresholdModifier

**Inherits:** `OpenXRActionBindingModifier` **<** `OpenXRBindingModifier` **<** `Resource` **<** `RefCounted` **<** `Object`

The analog threshold binding modifier can modify a float input to a boolean input with specified thresholds.

## Description

The analog threshold binding modifier can modify a float input to a boolean input with specified thresholds.

See [XR_VALVE_analog_threshold](https://registry.khronos.org/OpenXR/specs/1.1/html/xrspec.html#XR_VALVE_analog_threshold) for in-depth details.

## Property Descriptions

`OpenXRHapticBase` **off_haptic**

- `void (No return value.)` **set_off_haptic**(value: `OpenXRHapticBase`)
- `OpenXRHapticBase` **get_off_haptic**()

Haptic pulse to emit when the user releases the input.

`float` **off_threshold** = `0.4`

- `void (No return value.)` **set_off_threshold**(value: `float`)
- `float` **get_off_threshold**()

When our input value falls below this, our output becomes `false`.

`OpenXRHapticBase` **on_haptic**

- `void (No return value.)` **set_on_haptic**(value: `OpenXRHapticBase`)
- `OpenXRHapticBase` **get_on_haptic**()

Haptic pulse to emit when the user presses the input.

`float` **on_threshold** = `0.6`

- `void (No return value.)` **set_on_threshold**(value: `float`)
- `float` **get_on_threshold**()

When our input value is equal or larger than this value, our output becomes `true`. It stays `true` until it falls under the `off_threshold` value.