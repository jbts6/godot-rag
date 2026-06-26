import unittest

from rag.rst import _preprocess_rst
from rst2md_batch import clean_markdown


class PreprocessRstTests(unittest.TestCase):
    def test_removes_github_url_hide_and_trailing_blank_line(self):
        rst = ":github_url: hide\n\nTitle\n=====\n"

        self.assertEqual(_preprocess_rst(rst), "Title\n=====\n")

    def test_converts_tabs_and_code_tab_blocks_to_code_blocks(self):
        rst = (
            ".. tabs::\n"
            "\n"
            " .. code-tab:: gdscript GDScript\n"
            "\n"
            "    var box = AABB(Vector3(5, 0, 5))\n"
            "    var absolute = box.abs()\n"
            "\n"
            " .. code-tab:: csharp C#\n"
            "\n"
            "    var box = new Aabb(new Vector3(5, 0, 5));\n"
            "\n"
            "Following prose.\n"
        )

        self.assertEqual(
            _preprocess_rst(rst),
            ".. code-block:: gdscript\n"
            "\n"
            "   var box = AABB(Vector3(5, 0, 5))\n"
            "   var absolute = box.abs()\n"
            "\n"
            ".. code-block:: csharp\n"
            "\n"
            "   var box = new Aabb(new Vector3(5, 0, 5));\n"
            "\n"
            "Following prose.\n",
        )

    def test_code_tab_uses_first_argument_token_as_language(self):
        rst = (
            ".. tabs::\n"
            "\n"
            " .. code-tab:: gdscript 3D GDScript\n"
            "\n"
            "    print(\"3D\")\n"
        )

        self.assertIn(".. code-block:: gdscript", _preprocess_rst(rst))
        self.assertNotIn("3D GDScript", _preprocess_rst(rst))

    def test_preserves_nested_code_body_indentation(self):
        rst = (
            ".. tabs::\n"
            "\n"
            " .. code-tab:: gdscript\n"
            "\n"
            "    if visible:\n"
            "        print(\"shown\")\n"
        )

        self.assertEqual(
            _preprocess_rst(rst),
            ".. code-block:: gdscript\n"
            "\n"
            "   if visible:\n"
            "       print(\"shown\")\n",
        )


class CleanMarkdownTests(unittest.TestCase):
    def test_removes_classref_noise_lines(self):
        markdown = """
# AStarGrid2D

classref-introduction-group

Grid-based pathfinding.

classref-section-separator

More details.
"""

        self.assertEqual(
            clean_markdown(markdown),
            "# AStarGrid2D\n\nGrid-based pathfinding.\n\nMore details.",
        )

    def test_simplifies_godot_cross_references_but_keeps_display_text(self):
        markdown = (
            "**Inherits:** `RefCounted<class_RefCounted>` **\\<** "
            "`Object<class_Object>`\n\n"
            "Returns `Vector3<class_Vector3>` from `get_position<class_Node3D_method_get_position>`."
        )

        self.assertEqual(
            clean_markdown(markdown),
            "**Inherits:** `RefCounted` **<** `Object`\n\n"
            "Returns `Vector3` from `get_position`.",
        )

    def test_removes_anchor_icons_without_removing_method_text(self):
        markdown = (
            "`bool<class_bool>` **is_valid_filename**() "
            "`🔗<class_StringName_method_is_valid_filename>`\n\n"
            "Returns `true` for valid file names."
        )

        self.assertEqual(
            clean_markdown(markdown),
            "`bool` **is_valid_filename**()\n\nReturns `true` for valid file names.",
        )

    def test_does_not_clean_inside_fenced_code_blocks(self):
        markdown = """
```gdscript
print("classref-section-separator")
print("`Vector3<class_Vector3>`")
```

classref-section-separator

Outside `Vector3<class_Vector3>`.
"""

        self.assertEqual(
            clean_markdown(markdown),
            '```gdscript\nprint("classref-section-separator")\n'
            'print("`Vector3<class_Vector3>`")\n```\n\nOutside `Vector3`.',
        )

    def test_does_not_clean_inside_indented_code_blocks(self):
        markdown = """
Example:

    print("classref-section-separator")
    print("`Vector3<class_Vector3>`")

Outside `Vector3<class_Vector3>`.
"""

        self.assertEqual(
            clean_markdown(markdown),
            'Example:\n\n    print("classref-section-separator")\n'
            '    print("`Vector3<class_Vector3>`")\n\nOutside `Vector3`.',
        )

    def test_simplifies_const_and_vararg_boilerplate(self):
        markdown = (
            "`const (This method has no side effects. It doesn't modify any of the instance's member variables.)` "
            "`vararg (This method accepts any number of arguments after the ones described here.)`"
        )

        self.assertEqual(clean_markdown(markdown), "`const` `vararg`")

    def test_removes_empty_api_headings_but_keeps_non_empty_headings(self):
        markdown = (
            "## Properties\n"
            "\n"
            "## Methods\n"
            "\n"
            "`void` **do_it**()\n"
            "\n"
            "## Operators\n"
        )

        self.assertEqual(clean_markdown(markdown), "## Methods\n\n`void` **do_it**()")

    def test_unescapes_hash_and_asterisk_outside_code(self):
        markdown = "Use \\# for color names and \\* for wildcard prose."

        self.assertEqual(clean_markdown(markdown), "Use # for color names and * for wildcard prose.")

    def test_does_not_unescape_hash_or_asterisk_inside_code_blocks(self):
        markdown = (
            "```gdscript\n"
            "var color = \"\\#fff\"\n"
            "var glob = \"\\*\"\n"
            "```\n"
            "\n"
            "Outside \\# and \\*."
        )

        self.assertEqual(
            clean_markdown(markdown),
            "```gdscript\n"
            "var color = \"\\#fff\"\n"
            "var glob = \"\\*\"\n"
            "```\n"
            "\n"
            "Outside # and *.",
        )


if __name__ == "__main__":
    unittest.main()
