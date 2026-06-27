# XRInterfaceExtension

**Inherits:** `XRInterface` **<** `RefCounted` **<** `Object`

Base class for XR interface extensions (plugins).

## Description

External XR interface plugins should inherit from this class.

## Tutorials

- `XR documentation index `

## Method Descriptions

`void (No return value.)` **\_end_frame**() `virtual (This method should typically be overridden by the user to have any effect.)`

Called if interface is active and queues have been submitted.

`bool` **\_get_anchor_detection_is_enabled**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Return `true` if anchor detection is enabled for this interface.

`int` **\_get_camera_feed_id**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the camera feed ID for the `CameraFeed` registered with the `CameraServer` that should be presented as the background on an AR capable device (if applicable).

`Transform3D` **\_get_camera_transform**() `virtual (This method should typically be overridden by the user to have any effect.)`

Returns the `Transform3D` that positions the `XRCamera3D` in the world.

`int` **\_get_capabilities**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the capabilities of this interface.

`RID` **\_get_color_texture**() `virtual (This method should typically be overridden by the user to have any effect.)`

Return color texture into which to render (if applicable).

`RID` **\_get_depth_texture**() `virtual (This method should typically be overridden by the user to have any effect.)`

Return depth texture into which to render (if applicable).

`StringName` **\_get_name**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the name of this interface.

`PackedVector3Array` **\_get_play_area**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns a `PackedVector3Array` that represents the play areas boundaries (if applicable).

`PlayAreaMode` **\_get_play_area_mode**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the play area mode that sets up our play area.

`PackedFloat64Array` **\_get_projection_for_view**(view: `int`, aspect: `float`, z_near: `float`, z_far: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Returns the projection matrix for the given view as a `PackedFloat64Array`.

`Vector2` **\_get_render_target_size**() `virtual (This method should typically be overridden by the user to have any effect.)`

Returns the size of our render target for this interface, this overrides the size of the `Viewport` marked as the xr viewport.

`PackedStringArray` **\_get_suggested_pose_names**(tracker_name: `StringName`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns a `PackedStringArray` with pose names configured by this interface. Note that user configuration can override this list.

`PackedStringArray` **\_get_suggested_tracker_names**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns a `PackedStringArray` with tracker names configured by this interface. Note that user configuration can override this list.

`Dictionary` **\_get_system_info**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns a `Dictionary` with system information related to this interface.

`TrackingStatus` **\_get_tracking_status**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns the current status of our tracking.

`Transform3D` **\_get_transform_for_view**(view: `int`, cam_transform: `Transform3D`) `virtual (This method should typically be overridden by the user to have any effect.)`

Returns a `Transform3D` for a given view.

`RID` **\_get_velocity_texture**() `virtual (This method should typically be overridden by the user to have any effect.)`

Return velocity texture into which to render (if applicable).

`int` **\_get_view_count**() `virtual (This method should typically be overridden by the user to have any effect.)`

Returns the number of views this interface requires, 1 for mono, 2 for stereoscopic.

`RID` **\_get_vrs_texture**() `virtual (This method should typically be overridden by the user to have any effect.)`

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`VRSTextureFormat` **\_get_vrs_texture_format**() `virtual (This method should typically be overridden by the user to have any effect.)`

Returns the format of the texture returned by `_get_vrs_texture()`.

`bool` **\_initialize**() `virtual (This method should typically be overridden by the user to have any effect.)`

Initializes the interface, returns `true` on success.

`bool` **\_is_initialized**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if this interface has been initialized.

`void (No return value.)` **\_post_draw_viewport**(render_target: `RID`, screen_rect: `Rect2`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called after the XR `Viewport` draw logic has completed.

`bool` **\_pre_draw_viewport**(render_target: `RID`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called if this is our primary **XRInterfaceExtension** before we start processing a `Viewport` for every active XR `Viewport`, returns `true` if that viewport should be rendered. An XR interface may return `false` if the user has taken off their headset and we can pause rendering.

`void (No return value.)` **\_pre_render**() `virtual (This method should typically be overridden by the user to have any effect.)`

Called if this **XRInterfaceExtension** is active before rendering starts. Most XR interfaces will sync tracking at this point in time.

`void (No return value.)` **\_process**() `virtual (This method should typically be overridden by the user to have any effect.)`

Called if this **XRInterfaceExtension** is active before our physics and game process is called. Most XR interfaces will update its `XRPositionalTracker`s at this point in time.

`void (No return value.)` **\_set_anchor_detection_is_enabled**(enabled: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Enables anchor detection on this interface if supported.

`bool` **\_set_play_area_mode**(mode: `PlayAreaMode`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Set the play area mode for this interface.

`bool` **\_supports_play_area_mode**(mode: `PlayAreaMode`) `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Returns `true` if this interface supports this play area mode.

`void (No return value.)` **\_trigger_haptic_pulse**(action_name: `String`, tracker_name: `StringName`, frequency: `float`, amplitude: `float`, duration_sec: `float`, delay_sec: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Triggers a haptic pulse to be emitted on the specified tracker.

`void (No return value.)` **\_uninitialize**() `virtual (This method should typically be overridden by the user to have any effect.)`

Uninitialize the interface.

`void (No return value.)` **add_blit**(render_target: `RID`, src_rect: `Rect2`, dst_rect: `Rect2i`, use_layer: `bool`, layer: `int`, apply_lens_distortion: `bool`, eye_center: `Vector2`, k1: `float`, k2: `float`, upscale: `float`, aspect_ratio: `float`)

Blits our render results to screen optionally applying lens distortion. This can only be called while processing `_commit_views`.

`RID` **get_color_texture**()

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`RID` **get_depth_texture**()

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!

`RID` **get_render_target_texture**(render_target: `RID`)

Returns a valid `RID` for a texture to which we should render the current frame if supported by the interface.

`RID` **get_velocity_texture**()

There is currently no description for this method. Please help us by [contributing one](https://contributing.godotengine.org/en/latest/documentation/class_reference.html)!