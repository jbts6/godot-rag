# EngineProfiler

**Inherits:** `RefCounted` **<** `Object`

Base class for creating custom profilers.

## Description

This class can be used to implement custom profilers that are able to interact with the engine and editor debugger.

See `EngineDebugger` and `EditorDebuggerPlugin` for more information.

## Method Descriptions

`void (No return value.)` **\_add_frame**(data: `Array`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called when data is added to profiler using `EngineDebugger.profiler_add_frame_data()`.

`void (No return value.)` **\_tick**(frame_time: `float`, process_time: `float`, physics_time: `float`, physics_frame_time: `float`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called once every engine iteration when the profiler is active with information about the current frame. All time values are in seconds. Lower values represent faster processing times and are therefore considered better.

`void (No return value.)` **\_toggle**(enable: `bool`, options: `Array`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called when the profiler is enabled/disabled, along with a set of `options`.