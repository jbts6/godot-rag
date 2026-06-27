# VideoStreamPlayback

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Internal class used by `VideoStream` to manage playback state when played from a `VideoStreamPlayer`.

## Description

This class is intended to be overridden by video decoder extensions with custom implementations of `VideoStream`.

## Method Descriptions

`int` **\_get_channels**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the number of audio channels.

`float` **\_get_length**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the video duration in seconds, if known, or 0 if unknown.

`int` **\_get_mix_rate**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the audio sample rate used for mixing.

`float` **\_get_playback_position**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Return the current playback timestamp. Called in response to the `VideoStreamPlayer.stream_position` getter.

`Texture2D` **\_get_texture**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Allocates a `Texture2D` in which decoded video frames will be drawn.

`bool` **\_is_paused**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the paused status, as set by `_set_paused()`.

`bool` **\_is_playing**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the playback state, as determined by calls to `_play()` and `_stop()`.

`void (No return value.)` **\_play**() `virtual (This method should typically be overridden by the user to have any effect.)`

Called in response to `VideoStreamPlayer.autoplay` or `VideoStreamPlayer.play()`. Note that manual playback may also invoke `_stop()` multiple times before this method is called. `_is_playing()` should return `true` once playing.

`void (No return value.)` **\_seek**(time: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Seeks to `time` seconds. Called in response to the `VideoStreamPlayer.stream_position` setter.

`void (No return value.)` **\_set_audio_track**(idx: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Select the audio track `idx`. Called when playback starts, and in response to the `VideoStreamPlayer.audio_track` setter.

`void (No return value.)` **\_set_paused**(paused: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Set the paused status of video playback. `_is_paused()` must return `paused`. Called in response to the `VideoStreamPlayer.paused` setter.

`void (No return value.)` **\_stop**() `virtual (This method should typically be overridden by the user to have any effect.)`

Stops playback. May be called multiple times before `_play()`, or in response to `VideoStreamPlayer.stop()`. `_is_playing()` should return `false` once stopped.

`void (No return value.)` **\_update**(delta: `float`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Ticks video playback for `delta` seconds. Called every frame as long as both `_is_paused()` and `_is_playing()` return `true`.

`int` **mix_audio**(num_frames: `int`, buffer: `PackedFloat32Array` = PackedFloat32Array(), offset: `int` = 0)

Render `num_frames` audio frames (of `_get_channels()` floats each) from `buffer`, starting from index `offset` in the array. Returns the number of audio frames rendered, or -1 on error.