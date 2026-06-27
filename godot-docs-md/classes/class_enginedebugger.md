# EngineDebugger

**Inherits:** `Object`

Exposes the internal debugger.

## Description

**EngineDebugger** handles the communication between the editor and the running game. It is active in the running game. Messages can be sent/received through it. It also manages the profilers.

## Method Descriptions

`void (No return value.)` **clear_breakpoints**()

Clears all breakpoints.

`void (No return value.)` **debug**(can_continue: `bool` = true, is_error_breakpoint: `bool` = false)

Starts a debug break in script execution, optionally specifying whether the program can continue based on `can_continue` and whether the break was due to a breakpoint.

`int` **get_depth**() `const`

**Experimental:** This method may be changed or removed in future versions.

Returns the current debug depth.

`int` **get_lines_left**() `const`

**Experimental:** This method may be changed or removed in future versions.

Returns the number of lines that remain.

`bool` **has_capture**(name: `StringName`)

Returns `true` if a capture with the given name is present otherwise `false`.

`bool` **has_profiler**(name: `StringName`)

Returns `true` if a profiler with the given name is present otherwise `false`.

`void (No return value.)` **insert_breakpoint**(line: `int`, source: `StringName`)

Inserts a new breakpoint with the given `source` and `line`.

`bool` **is_active**()

Returns `true` if the debugger is active otherwise `false`.

`bool` **is_breakpoint**(line: `int`, source: `StringName`) `const`

Returns `true` if the given `source` and `line` represent an existing breakpoint.

`bool` **is_profiling**(name: `StringName`)

Returns `true` if a profiler with the given name is present and active otherwise `false`.

`bool` **is_skipping_breakpoints**() `const`

Returns `true` if the debugger is skipping breakpoints otherwise `false`.

`void (No return value.)` **line_poll**()

Forces a processing loop of debugger events. The purpose of this method is just processing events every now and then when the script might get too busy, so that bugs like infinite loops can be caught.

`void (No return value.)` **profiler_add_frame_data**(name: `StringName`, data: `Array`)

Calls the `add` callable of the profiler with given `name` and `data`.

`void (No return value.)` **profiler_enable**(name: `StringName`, enable: `bool`, arguments: `Array` = \[\])

Calls the `toggle` callable of the profiler with given `name` and `arguments`. Enables/Disables the same profiler depending on `enable` argument.

`void (No return value.)` **register_message_capture**(name: `StringName`, callable: `Callable`)

Registers a message capture with given `name`. If `name` is "my_message" then messages starting with "my_message:" will be called with the given callable.

The callable must accept a message string and a data array as argument. The callable should return `true` if the message is recognized.

**Note:** The callable will receive the message with the prefix stripped, unlike `EditorDebuggerPlugin._capture()`. See the `EditorDebuggerPlugin` description for an example.

`void (No return value.)` **register_profiler**(name: `StringName`, profiler: `EngineProfiler`)

Registers a profiler with the given `name`. See `EngineProfiler` for more information.

`void (No return value.)` **remove_breakpoint**(line: `int`, source: `StringName`)

Removes a breakpoint with the given `source` and `line`.

`void (No return value.)` **script_debug**(language: `ScriptLanguage`, can_continue: `bool` = true, is_error_breakpoint: `bool` = false)

Starts a debug break in script execution, optionally specifying whether the program can continue based on `can_continue` and whether the break was due to a breakpoint.

`void (No return value.)` **send_message**(message: `String`, data: `Array`)

Sends a message with given `message` and `data` array.

`void (No return value.)` **set_depth**(depth: `int`)

**Experimental:** This method may be changed or removed in future versions.

Sets the current debugging depth.

`void (No return value.)` **set_lines_left**(lines: `int`)

**Experimental:** This method may be changed or removed in future versions.

Sets the current debugging lines that remain.

`void (No return value.)` **unregister_message_capture**(name: `StringName`)

Unregisters the message capture with given `name`.

`void (No return value.)` **unregister_profiler**(name: `StringName`)

Unregisters a profiler with given `name`.