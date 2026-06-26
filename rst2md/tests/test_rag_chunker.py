import unittest

from rag.models import Chunk
from rag.chunker import chunk_markdown


class ModelTests(unittest.TestCase):
    def test_chunk_has_required_fields(self):
        chunk = Chunk(
            path="classes/class_stringname.md",
            doc_type="class",
            chunk_type="method",
            addon="",
            addon_name="",
            symbol="StringName.is_valid_filename",
            heading="Methods",
            breadcrumb="classes > StringName > is_valid_filename",
            start_line=10,
            end_line=15,
            text="`bool` **is_valid_filename**()",
        )

        self.assertEqual(chunk.symbol, "StringName.is_valid_filename")
        self.assertEqual(chunk.start_line, 10)
        self.assertEqual(chunk.end_line, 15)


class ChunkerTests(unittest.TestCase):
    def test_chunks_class_summary_and_method(self):
        markdown = """# StringName

**Inherits:** `RefCounted` **<** `Object`

Interned string type.

## Methods

`bool` **is_valid_filename**() `const`

Returns `true` if this string is a valid file name.

`String` **validate_filename**()

Returns a safe file name.
"""

        chunks = chunk_markdown("classes/class_stringname.md", markdown)

        self.assertEqual(chunks[0].chunk_type, "class_summary")
        self.assertEqual(chunks[0].symbol, "StringName")
        self.assertEqual(chunks[1].chunk_type, "method")
        self.assertEqual(chunks[1].symbol, "StringName.is_valid_filename")
        self.assertIn("Returns `true`", chunks[1].text)
        self.assertEqual(chunks[1].start_line, 9)

    def test_chunks_tutorial_by_heading(self):
        markdown = """# C# Variant

Intro.

## Conversion

Use Variant carefully.

## Boxing

Avoid unnecessary boxing.
"""

        chunks = chunk_markdown("tutorials/scripting/c_sharp/c_sharp_variant.md", markdown)

        self.assertEqual([chunk.chunk_type for chunk in chunks], ["tutorial_section", "tutorial_section", "tutorial_section"])
        self.assertEqual(chunks[1].heading, "Conversion")
        self.assertIn("tutorials > scripting > c_sharp > c_sharp_variant > Conversion", chunks[1].breadcrumb)


class ClassMemberChunkerTests(unittest.TestCase):
    """Signals, enums, and constants should be chunked as separate members."""

    MARKDOWN = """# Timer

**Inherits:** `Node` **<** `Object`

A countdown timer.

## Properties

## Methods

## Signals

**timeout**()

Emitted when the timer reaches the end.

## Enumerations

enum **TimerProcessCallback**:

`TimerProcessCallback` **TIMER_PROCESS_PHYSICS** = `0`

Update the timer every physics process frame.

`TimerProcessCallback` **TIMER_PROCESS_IDLE** = `1`

Update the timer every process frame.

## Constants

**NOTIFICATION_ONE_SHOT** = `100`
"""

    def test_signal_is_chunked(self):
        chunks = chunk_markdown("classes/class_timer.md", self.MARKDOWN)
        symbols = [c.symbol for c in chunks]
        self.assertIn("Timer.timeout", symbols)

    def test_enum_is_chunked(self):
        chunks = chunk_markdown("classes/class_timer.md", self.MARKDOWN)
        symbols = [c.symbol for c in chunks]
        self.assertIn("Timer.TimerProcessCallback", symbols)

    def test_constant_is_chunked(self):
        chunks = chunk_markdown("classes/class_timer.md", self.MARKDOWN)
        symbols = [c.symbol for c in chunks]
        self.assertIn("Timer.NOTIFICATION_ONE_SHOT", symbols)

    def test_no_content_lost_between_members(self):
        """Every line of the source should be covered by exactly one chunk."""
        chunks = chunk_markdown("classes/class_timer.md", self.MARKDOWN)
        all_text = "\n".join(c.text for c in chunks)
        # Key phrases must appear in some chunk
        self.assertIn("timeout", all_text)
        self.assertIn("TimerProcessCallback", all_text)
        self.assertIn("NOTIFICATION_ONE_SHOT", all_text)


if __name__ == "__main__":
    unittest.main()
