# VideoStream

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `VideoStreamTheora`

Base resource for video streams.

## Description

Base resource type for all video streams. Classes that derive from **VideoStream** can all be used as resource types to play back videos in `VideoStreamPlayer`.

## Tutorials

- `Playing videos `
- `Runtime file loading and saving `

## Property Descriptions

`String` **file** = `""`

- `void (No return value.)` **set_file**(value: `String`)
- `String` **get_file**()

The video file path or URI that this **VideoStream** resource handles.

For `VideoStreamTheora`, this filename should be an Ogg Theora video file with the `.ogv` extension.

## Method Descriptions

`VideoStreamPlayback` **\_instantiate_playback**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the video starts playing, to initialize and return a subclass of `VideoStreamPlayback`.