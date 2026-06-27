# OpenXRSpatialContextPersistenceConfig

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `OpenXRStructureBase` **<** `RefCounted` **<** `Object`

Configuration header for spatial persistence.

## Description

Configuration header for spatial persistence. Pass this to `OpenXRSpatialEntityExtension.create_spatial_context()` as the next parameter to create a spatial context with spatial persistence capabilities.

## Method Descriptions

`void (No return value.)` **add_persistence_context**(persistence_context: `RID`)

Adds a persistence context to this configuration. You must add at least one persistence context to create a valid configuration. You can create a persistence context by calling `OpenXRSpatialAnchorCapability.create_persistence_context()`.

`Array` **get_persistence_contexts**() `const`

Gets the persistence context(s) (as `RID`s) received by `add_persistence_context()`.

`void (No return value.)` **remove_persistence_context**(persistence_context: `RID`)

Removes a persistence context.