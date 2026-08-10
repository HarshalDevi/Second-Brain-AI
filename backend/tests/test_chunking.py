import unittest

from app.services.chunking import chunk_text


class ChunkTextTest(unittest.TestCase):
    def test_chunks_start_on_sentence_or_paragraph_boundaries(self):
        text = (
            "MS Dhoni was born in Ranchi. He is known for calm captaincy. "
            "He plays the helicopter shot.\n\n"
            "Dhoni led India to major titles. He is a wicket-keeper batter. "
            * 20
        )

        chunks = chunk_text(text, max_chars=240, overlap=80)

        self.assertGreater(len(chunks), 2)
        for chunk in chunks:
            self.assertTrue(chunk.text[0].isupper() or chunk.text[0].isdigit())
            self.assertFalse(chunk.text.startswith("oni"))

    def test_normalizes_excess_spacing(self):
        chunks = chunk_text("Alpha   beta.\n\n\nGamma\t delta.")

        self.assertEqual(chunks[0].text, "Alpha beta.\n\nGamma delta.")


if __name__ == "__main__":
    unittest.main()