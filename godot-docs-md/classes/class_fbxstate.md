# FBXState

**Experimental:** This class may be changed or removed in future versions.

**Inherits:** `GLTFState` **<** `Resource` **<** `RefCounted` **<** `Object`

## Description

The FBXState handles the state data imported from FBX files.

## Property Descriptions

`bool` **allow_geometry_helper_nodes** = `false`

- `void (No return value.)` **set_allow_geometry_helper_nodes**(value: `bool`)
- `bool` **get_allow_geometry_helper_nodes**()

If `true`, the import process used auxiliary nodes called geometry helper nodes. These nodes help preserve the pivots and transformations of the original 3D model during import.