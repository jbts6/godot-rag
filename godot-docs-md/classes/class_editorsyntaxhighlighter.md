# EditorSyntaxHighlighter

**Inherits:** `SyntaxHighlighter` **<** `Resource` **<** `RefCounted` **<** `Object`

**Inherited By:** `GDScriptSyntaxHighlighter`

Base class for `SyntaxHighlighter` used by the `ScriptEditor`.

## Description

Base class that all `SyntaxHighlighter`s used by the `ScriptEditor` extend from.

Add a syntax highlighter to an individual script by calling `ScriptEditorBase.add_syntax_highlighter()`. To apply to all scripts on open, call `ScriptEditor.register_syntax_highlighter()`.

## Method Descriptions

`EditorSyntaxHighlighter` **\_create**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Virtual method which creates a new instance of the syntax highlighter.

`String` **\_get_name**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Virtual method which can be overridden to return the syntax highlighter name.

`PackedStringArray` **\_get_supported_languages**() `virtual (This method should typically be overridden by the user to have any effect.)` `const`

Virtual method which can be overridden to return the supported language names.