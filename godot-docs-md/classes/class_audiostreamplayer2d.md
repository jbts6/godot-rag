# AudioStreamPlayer2D

**Inherits:** `Node2D` **<** `CanvasItem` **<** `Node` **<** `Object`

Plays positional sound in 2D space.

## Description

Plays audio that is attenuated with distance to the listener.

By default, audio is heard from the screen center. This can be changed by adding an `AudioListener2D` node to the scene and enabling it by calling `AudioListener2D.make_current()` on it.

See also `AudioStreamPlayer` to play a sound non-positionally.

**Note:** Hiding an **AudioStreamPlayer2D** node does not disable its audio output. To temporarily disable an **AudioStreamPlayer2D**'s audio output, set `volume_db` to a very low value like `-100` (which isn't audible to human hearing).

## Tutorials

- `Audio streams `

## Signals

**finished**()

Emitted when the audio stops playing.

## Property Descriptions

`int` **area_mask** = `0`

- `void (No return value.)` **set_area_mask**(value: `int`)
- `int` **get_area_mask**()

Determines which `Area2D` layers affect the sound for reverb and audio bus effects. Areas can be used to redirect `AudioStream`s so that they play in a certain audio bus. An example of how you might use this is making a "water" area so that sounds played in the water are redirected through an audio bus to make them sound like they are being played underwater.

`float` **attenuation** = `1.0`

- `void (No return value.)` **set_attenuation**(value: `float`)
- `float` **get_attenuation**()

The volume is attenuated over distance with this as an exponent.

`bool` **autoplay** = `false`

- `void (No return value.)` **set_autoplay**(value: `bool`)
- `bool` **is_autoplay_enabled**()

If `true`, audio plays when added to scene tree.

`StringName` **bus** = `&"Master"`

- `void (No return value.)` **set_bus**(value: `StringName`)
- `StringName` **get_bus**()

Bus on which this audio is playing.

**Note:** When setting this property, keep in mind that no validation is performed to see if the given name matches an existing bus. This is because audio bus layouts might be loaded after this property is set. If this given name can't be resolved at runtime, it will fall back to `"Master"`.

`float` **max_distance** = `2000.0`

- `void (No return value.)` **set_max_distance**(value: `float`)
- `float` **get_max_distance**()

Maximum distance from which audio is still hearable.

`int` **max_polyphony** = `1`

- `void (No return value.)` **set_max_polyphony**(value: `int`)
- `int` **get_max_polyphony**()

The maximum number of sounds this node can play at the same time. Playing additional sounds after this value is reached will cut off the oldest sounds.

`float` **panning_strength** = `1.0`

- `void (No return value.)` **set_panning_strength**(value: `float`)
- `float` **get_panning_strength**()

Scales the panning strength for this node by multiplying the base `ProjectSettings.audio/general/2d_panning_strength` with this factor. Higher values will pan audio from left to right more dramatically than lower values.

`float` **pitch_scale** = `1.0`

- `void (No return value.)` **set_pitch_scale**(value: `float`)
- `float` **get_pitch_scale**()

The pitch and the tempo of the audio, as a multiplier of the audio sample's sample rate.

`PlaybackType` **playback_type** = `0`

- `void (No return value.)` **set_playback_type**(value: `PlaybackType`)
- `PlaybackType` **get_playback_type**()

**Experimental:** This property may be changed or removed in future versions.

The playback type of the stream player. If set other than to the default value, it will force that playback type.

`bool` **playing** = `false`

- `void (No return value.)` **set_playing**(value: `bool`)
- `bool` **is_playing**()

If `true`, audio is playing or is queued to be played (see `play()`).

`AudioStream` **stream**

- `void (No return value.)` **set_stream**(value: `AudioStream`)
- `AudioStream` **get_stream**()

The `AudioStream` object to be played.

`bool` **stream_paused** = `false`

- `void (No return value.)` **set_stream_paused**(value: `bool`)
- `bool` **get_stream_paused**()

If `true`, the playback is paused. You can resume it by setting `stream_paused` to `false`.

`float` **volume_db** = `0.0`

- `void (No return value.)` **set_volume_db**(value: `float`)
- `float` **get_volume_db**()

Base volume before attenuation, in decibels.

`float` **volume_linear**

- `void (No return value.)` **set_volume_linear**(value: `float`)
- `float` **get_volume_linear**()

Base volume before attenuation, as a linear value.

**Note:** This member modifies `volume_db` for convenience. The returned value is equivalent to the result of `@GlobalScope.db_to_linear()` on `volume_db`. Setting this member is equivalent to setting `volume_db` to the result of `@GlobalScope.linear_to_db()` on a value.

## Method Descriptions

`float` **get_playback_position**()

Returns the position in the `AudioStream`.

`AudioStreamPlayback` **get_stream_playback**()

Returns the `AudioStreamPlayback` object associated with this **AudioStreamPlayer2D**.

`bool` **has_stream_playback**()

Returns whether the `AudioStreamPlayer` can return the `AudioStreamPlayback` object or not.

`void (No return value.)` **play**(from_position: `float` = 0.0)

Queues the audio to play on the next physics frame, from the given position `from_position`, in seconds.

`void (No return value.)` **seek**(to_position: `float`)

Sets the position from which audio will be played, in seconds.

`void (No return value.)` **stop**()

Stops the audio.