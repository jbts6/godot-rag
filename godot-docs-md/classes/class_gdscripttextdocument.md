# GDScriptTextDocument

**Deprecated:** This class may be changed or removed in future versions.

**Inherits:** `RefCounted` **<** `Object`

Document related language server functionality.

## Description

Provides language server functionality related to documents.

## Method Descriptions

`Array` **codeLens**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **colorPresentation**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **completion**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Variant` **declaration**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **definition**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`void (No return value.)` **didChange**(params: `Variant`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`void (No return value.)` **didClose**(params: `Variant`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`void (No return value.)` **didOpen**(params: `Variant`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`void (No return value.)` **didSave**(params: `Variant`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **documentLink**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **documentSymbol**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **foldingRange**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Variant` **hover**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Variant` **nativeSymbol**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Variant` **prepareRename**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Array` **references**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Dictionary` **rename**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`Dictionary` **resolve**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`void (No return value.)` **show_native_symbol_in_editor**(symbol_id: `String`)

**Deprecated:** Use `ScriptEditor.goto_help()` instead.

`Variant` **signatureHelp**(params: `Dictionary`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.

`void (No return value.)` **willSaveWaitUntil**(params: `Variant`)

**Deprecated:** Accessing LSP endpoints directly might lead to unwanted side effects. Connect to the server via TCP, like a regular language server client.