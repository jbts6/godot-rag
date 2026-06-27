# AudioListener3D

**Inherits:** `Node3D` **<** `Node` **<** `Object`

Overrides the location sounds are heard from.

## Description

Once added to the scene tree and enabled using `make_current()`, this node will override the location sounds are heard from. This can be used to listen from a location different from the `Camera3D`.

## Enumerations

enum **DopplerTracking**:

`DopplerTracking` **DOPPLER_TRACKING_DISABLED** = `0`

Disables [Doppler effect](https://en.wikipedia.org/wiki/Doppler_effect) simulation (default).

`DopplerTracking` **DOPPLER_TRACKING_IDLE_STEP** = `1`

Simulate [Doppler effect](https://en.wikipedia.org/wiki/Doppler_effect) by tracking positions of objects that are changed in `_process`. Changes in the relative velocity of this listener compared to those objects affect how audio is perceived (changing the audio's `AudioStreamPlayer3D.pitch_scale`).

`DopplerTracking` **DOPPLER_TRACKING_PHYSICS_STEP** = `2`

Simulate [Doppler effect](https://en.wikipedia.org/wiki/Doppler_effect) by tracking positions of objects that are changed in `_physics_process`. Changes in the relative velocity of this listener compared to those objects affect how audio is perceived (changing the audio's `AudioStreamPlayer3D.pitch_scale`).

## Property Descriptions

`DopplerTracking` **doppler_tracking** = `0`

- `void (No return value.)` **set_doppler_tracking**(value: `DopplerTracking`)
- `DopplerTracking` **get_doppler_tracking**()

If not `DOPPLER_TRACKING_DISABLED`, this listener will simulate the [Doppler effect](https://en.wikipedia.org/wiki/Doppler_effect) for objects changed in particular `_process` methods.

**Note:** The Doppler effect will only be heard on `AudioStreamPlayer3D`s if `AudioStreamPlayer3D.doppler_tracking` is not set to `AudioStreamPlayer3D.DOPPLER_TRACKING_DISABLED`.

## Method Descriptions

`void (No return value.)` **clear_current**()

Disables the listener to use the current camera's listener instead.

`Transform3D` **get_listener_transform**() `const`

Returns the listener's global orthonormalized `Transform3D`.

`bool` **is_current**() `const`

Returns `true` if the listener was made current using `make_current()`, `false` otherwise.

**Note:** There may be more than one AudioListener3D marked as "current" in the scene tree, but only the one that was made current last will be used.

`void (No return value.)` **make_current**()

Enables the listener. This will override the current camera's listener.