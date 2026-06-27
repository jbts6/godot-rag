# EditorFileSystemImportFormatSupportQuery

**Inherits:** `RefCounted` **<** `Object`

Used to query and configure import format support.

## Description

This class is used to query and configure a certain import format. It is used in conjunction with asset format import plugins.

## Method Descriptions

`PackedStringArray` **\_get_file_extensions**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Return the file extensions supported.

`bool` **\_is_active**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Return whether this importer is active.

`bool` **\_query**() `virtual (This method should typically be overridden by the user to have any effect.)` `required (This method is required to be overridden when extending its base class.)` `const`

Query support. Return `false` if import must not continue.