# AudioStreamPlayback

**Inherits:** `RefCounted` **<** `Object`

**Inherited By:** `AudioStreamPlaybackInteractive`, `AudioStreamPlaybackPlaylist`, `AudioStreamPlaybackPolyphonic`, `AudioStreamPlaybackResampled`, `AudioStreamPlaybackSynchronized`

Meta class for playing back audio.

## Description

Can play, loop, pause a scroll through audio. See `AudioStream` and `AudioStreamOggVorbis` for usage.

## Tutorials

- [Audio Generator Demo](https://godotengine.org/asset-library/asset/2759)

## Method Descriptions

`int` **\_get_loop_count**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Overridable method. Should return how many times this audio stream has looped. Most built-in playbacks always return `0`.

`Variant` **\_get_parameter**(name: `StringName`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Return the current value of a playback parameter by name (see `AudioStream._get_parameter_list()`).

`float` **\_get_playback_position**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable method. Should return the current progress along the audio stream, in seconds.

`bool` **\_is_playing**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Overridable method. Should return `true` if this playback is active and playing its audio stream.

`int` **\_mix**(buffer: `AudioFrame*`, rate_scale: `float`, frames: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Override this method to customize how the audio stream is mixed. This method is called even if the playback is not active.

**Note:** It is not useful to override this method in GDScript or C#. Only GDExtension can take advantage of it.

`void (No return value.)` **\_seek**(position: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Override this method to customize what happens when seeking this audio stream at the given `position`, such as by calling `AudioStreamPlayer.seek()`.

`void (No return value.)` **\_set_parameter**(name: `StringName`, value: `Variant`) `virtual (This method should typically be overridden by the user to have any effect.)`

Set the current value of a playback parameter by name (see `AudioStream._get_parameter_list()`).

`void (No return value.)` **\_start**(from_pos: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Override this method to customize what happens when the playback starts at the given position, such as by calling `AudioStreamPlayer.play()`.

`void (No return value.)` **\_stop**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Override this method to customize what happens when the playback is stopped, such as by calling `AudioStreamPlayer.stop()`.

`void (No return value.)` **\_tag_used_streams**() `virtual (This method should typically be overridden by the user to have any effect.)`

Overridable method. Called whenever the audio stream is mixed if the playback is active and `AudioServer.set_enable_tagging_used_audio_streams()` has been set to `true`. Editor plugins may use this method to "tag" the current position along the audio stream and display it in a preview.

`int` **get_loop_count**() `const`

Returns the number of times the stream has looped.

`float` **get_playback_position**() `const`

Returns the current position in the stream, in seconds.

`AudioSamplePlayback` **get_sample_playback**() `const`

**Experimental:** This method may be changed or removed in future versions.

Returns the `AudioSamplePlayback` associated with this **AudioStreamPlayback** for playing back the audio sample of this stream.

`bool` **is_playing**() `const`

Returns `true` if the stream is playing.

`PackedVector2Array` **mix_audio**(rate_scale: `float`, frames: `int`)

Mixes up to `frames` of audio from the stream from the current position, at a rate of `rate_scale`, advancing the stream.

Returns a `PackedVector2Array` where each element holds the left and right channel volume levels of each frame.

**Note:** Can return fewer frames than requested, make sure to use the size of the return value.

`void (No return value.)` **seek**(time: `float` = 0.0)

Seeks the stream at the given `time`, in seconds.

`void (No return value.)` **set_sample_playback**(playback_sample: `AudioSamplePlayback`)

**Experimental:** This method may be changed or removed in future versions.

Associates `AudioSamplePlayback` to this **AudioStreamPlayback** for playing back the audio sample of this stream.

`void (No return value.)` **start**(from_pos: `float` = 0.0)

Starts the stream from the given `from_pos`, in seconds.

`void (No return value.)` **stop**()

Stops the stream.