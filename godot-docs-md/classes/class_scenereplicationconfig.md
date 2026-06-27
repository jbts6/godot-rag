# SceneReplicationConfig

**Inherits:** `Resource` **<** `RefCounted` **<** `Object`

Configuration for properties to synchronize with a `MultiplayerSynchronizer`.

## Enumerations

enum **ReplicationMode**:

`ReplicationMode` **REPLICATION_MODE_NEVER** = `0`

Do not keep the given property synchronized.

`ReplicationMode` **REPLICATION_MODE_ALWAYS** = `1`

Replicate the given property on process by constantly sending updates using unreliable transfer mode.

`ReplicationMode` **REPLICATION_MODE_ON_CHANGE** = `2`

Replicate the given property on process by sending updates using reliable transfer mode when its value changes.

## Method Descriptions

`void (No return value.)` **add_property**(path: `NodePath`, index: `int` = -1)

Adds the property identified by the given `path` to the list of the properties being synchronized, optionally passing an `index`.

**Note:** For details on restrictions and limitations on property synchronization, see `MultiplayerSynchronizer`.

`Array`\[`NodePath`\] **get_properties**() `const`

Returns a list of synchronized property `NodePath`s.

`bool` **has_property**(path: `NodePath`) `const`

Returns `true` if the given `path` is configured for synchronization.

`int` **property_get_index**(path: `NodePath`) `const`

Finds the index of the given `path`.

`ReplicationMode` **property_get_replication_mode**(path: `NodePath`)

Returns the replication mode for the property identified by the given `path`.

`bool` **property_get_spawn**(path: `NodePath`)

Returns `true` if the property identified by the given `path` is configured to be synchronized on spawn.

`bool` **property_get_sync**(path: `NodePath`)

**Deprecated:** Use `property_get_replication_mode()` instead.

Returns `true` if the property identified by the given `path` is configured to be synchronized on process.

`bool` **property_get_watch**(path: `NodePath`)

**Deprecated:** Use `property_get_replication_mode()` instead.

Returns `true` if the property identified by the given `path` is configured to be reliably synchronized when changes are detected on process.

`void (No return value.)` **property_set_replication_mode**(path: `NodePath`, mode: `ReplicationMode`)

Sets the synchronization mode for the property identified by the given `path`.

`void (No return value.)` **property_set_spawn**(path: `NodePath`, enabled: `bool`)

Sets whether the property identified by the given `path` is configured to be synchronized on spawn.

`void (No return value.)` **property_set_sync**(path: `NodePath`, enabled: `bool`)

**Deprecated:** Use `property_set_replication_mode()` with `REPLICATION_MODE_ALWAYS` instead.

Sets whether the property identified by the given `path` is configured to be synchronized on process.

`void (No return value.)` **property_set_watch**(path: `NodePath`, enabled: `bool`)

**Deprecated:** Use `property_set_replication_mode()` with `REPLICATION_MODE_ON_CHANGE` instead.

Sets whether the property identified by the given `path` is configured to be reliably synchronized when changes are detected on process.

`void (No return value.)` **remove_property**(path: `NodePath`)

Removes the property identified by the given `path` from the configuration.