# MultiplayerPeerExtension

**Inherits:** `MultiplayerPeer` **<** `PacketPeer` **<** `RefCounted` **<** `Object`

Class that can be inherited to implement custom multiplayer API networking layers via GDExtension.

## Description

This class is designed to be inherited from a GDExtension plugin to implement custom networking layers for the multiplayer API (such as WebRTC). All the methods below **must** be implemented to have a working custom multiplayer implementation. See also `MultiplayerAPI`.

## Method Descriptions

`void (No return value.)` **\_close**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the multiplayer peer should be immediately closed (see `MultiplayerPeer.close()`).

`void (No return value.)` **\_disconnect_peer**(peer: `int`, force: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the connected `peer` should be forcibly disconnected (see `MultiplayerPeer.disconnect_peer()`).

`int` **\_get_available_packet_count**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the available packet count is internally requested by the `MultiplayerAPI`.

`ConnectionStatus` **\_get_connection_status**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the connection status is requested on the `MultiplayerPeer` (see `MultiplayerPeer.get_connection_status()`).

`int` **\_get_max_packet_size**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the maximum allowed packet size (in bytes) is requested by the `MultiplayerAPI`.

`Error` **\_get_packet**(r_buffer: `const uint8_t **`, r_buffer_size: `int32_t*`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called when a packet needs to be received by the `MultiplayerAPI`, with `r_buffer_size` being the size of the binary `r_buffer` in bytes.

`int` **\_get_packet_channel**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called to get the channel over which the next available packet was received. See `MultiplayerPeer.get_packet_channel()`.

`TransferMode` **\_get_packet_mode**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called to get the transfer mode the remote peer used to send the next available packet. See `MultiplayerPeer.get_packet_mode()`.

`int` **\_get_packet_peer**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the ID of the `MultiplayerPeer` who sent the most recent packet is requested (see `MultiplayerPeer.get_packet_peer()`).

`PackedByteArray` **\_get_packet_script**() `virtual (This method should typically be overridden by the user to have any effect.)`

Called when a packet needs to be received by the `MultiplayerAPI`, if `_get_packet()` isn't implemented. Use this when extending this class via GDScript.

`int` **\_get_transfer_channel**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the transfer channel to use is read on this `MultiplayerPeer` (see `MultiplayerPeer.transfer_channel`).

`TransferMode` **\_get_transfer_mode**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the transfer mode to use is read on this `MultiplayerPeer` (see `MultiplayerPeer.transfer_mode`).

`int` **\_get_unique_id**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the unique ID of this `MultiplayerPeer` is requested (see `MultiplayerPeer.get_unique_id()`). The value must be between `1` and `2147483647`.

`bool` **\_is_refusing_new_connections**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Called when the "refuse new connections" status is requested on this `MultiplayerPeer` (see `MultiplayerPeer.refuse_new_connections`).

`bool` **\_is_server**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Called when the "is server" status is requested on the `MultiplayerAPI`. See `MultiplayerAPI.is_server()`.

`bool` **\_is_server_relay_supported**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Called to check if the server can act as a relay in the current configuration. See `MultiplayerPeer.is_server_relay_supported()`.

`void (No return value.)` **\_poll**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the `MultiplayerAPI` is polled. See `MultiplayerAPI.poll()`.

`Error` **\_put_packet**(buffer: `const uint8_t*`, buffer_size: `int`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called when a packet needs to be sent by the `MultiplayerAPI`, with `buffer_size` being the size of the binary `buffer` in bytes.

`Error` **\_put_packet_script**(buffer: `PackedByteArray`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called when a packet needs to be sent by the `MultiplayerAPI`, if `_put_packet()` isn't implemented. Use this when extending this class via GDScript.

`void (No return value.)` **\_set_refuse_new_connections**(enable: `bool`) `virtual (This method should typically be overridden by the user to have any effect.)`

Called when the "refuse new connections" status is set on this `MultiplayerPeer` (see `MultiplayerPeer.refuse_new_connections`).

`void (No return value.)` **\_set_target_peer**(peer: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the target peer to use is set for this `MultiplayerPeer` (see `MultiplayerPeer.set_target_peer()`).

`void (No return value.)` **\_set_transfer_channel**(channel: `int`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the channel to use is set for this `MultiplayerPeer` (see `MultiplayerPeer.transfer_channel`).

`void (No return value.)` **\_set_transfer_mode**(mode: `TransferMode`) `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)`

Called when the transfer mode is set on this `MultiplayerPeer` (see `MultiplayerPeer.transfer_mode`).