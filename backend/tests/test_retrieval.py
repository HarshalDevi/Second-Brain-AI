import unittest

from app.services.retrieval import _passes_relevance


class RetrievalRelevanceTest(unittest.TestCase):
    def test_filters_weak_matches(self):
        self.assertFalse(
            _passes_relevance(
                {"score": 0.12, "vector_score": 0.18, "keyword_score": 0.0}
            )
        )

    def test_filters_borderline_hybrid_score(self):
        self.assertFalse(
            _passes_relevance(
                {"score": 0.31, "vector_score": 0.25, "keyword_score": 0.01}
            )
        )

    def test_keeps_strong_hybrid_score(self):
        self.assertTrue(
            _passes_relevance(
                {"score": 0.42, "vector_score": 0.32, "keyword_score": 0.01}
            )
        )

    def test_keeps_keyword_exact_match(self):
        self.assertTrue(
            _passes_relevance(
                {"score": 0.10, "vector_score": 0.12, "keyword_score": 0.08}
            )
        )


if __name__ == "__main__":
    unittest.main()
