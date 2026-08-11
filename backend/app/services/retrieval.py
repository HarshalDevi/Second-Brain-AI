import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MIN_SCORE = 0.35
MIN_VECTOR_SCORE = 0.35
MIN_KEYWORD_SCORE = 0.04
SHORT_CHUNK_MAX_CHARS = 160
STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "did",
    "do",
    "for",
    "get",
    "got",
    "happen",
    "happened",
    "i",
    "in",
    "is",
    "know",
    "learn",
    "learned",
    "me",
    "my",
    "of",
    "recent",
    "recently",
    "that",
    "the",
    "thing",
    "to",
    "what",
    "with",
    "you",
}


def _terms(text_value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]+", text_value.lower())
        if len(term) >= 3 and term not in STOP_WORDS
    }


def _query_terms(query_text: str) -> list[str]:
    return sorted(_terms(query_text))


def _has_short_note_overlap(row, query_text: str) -> bool:
    chunk_text = str(row["text"] or "")
    if len(chunk_text) > SHORT_CHUNK_MAX_CHARS:
        return False
    return bool(_terms(query_text) & _terms(chunk_text))


def _passes_relevance(row, query_text: str = "") -> bool:
    score = float(row["score"] or 0)
    vector_score = float(row["vector_score"] or 0)
    keyword_score = float(row["keyword_score"] or 0)
    return (
        score >= MIN_SCORE
        or vector_score >= MIN_VECTOR_SCORE
        or keyword_score >= MIN_KEYWORD_SCORE
        or _has_short_note_overlap(row, query_text)
    )


async def retrieve_top_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    query_text: str,
    workspace_id: str,
    limit: int = 8,
):
    vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    candidate_limit = max(limit * 6, 36)

    sql = text("""
    WITH usable_chunks AS (
      SELECT c.*
      FROM chunks c
      JOIN documents d ON d.id = c.document_id
      WHERE d.workspace_id = :workspace_id
        AND d.status = 'ready'
        AND length(c.text) >= 12
        AND c.text !~ '[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]'
        AND (
          length(c.text) - length(regexp_replace(c.text, '[A-Za-z0-9 .,;:!?()''"/-]', '', 'g'))
        )::float / GREATEST(length(c.text), 1) > 0.72
    ),
    q AS (
      SELECT
        CAST(:qvec AS vector) AS qvec,
        websearch_to_tsquery('english', :query) AS query_terms
    ),
    vec AS (
      SELECT
        c.id AS chunk_id,
        c.document_id,
        c.chunk_index,
        c.text,
        d.title AS doc_title,
        d.created_at AS doc_created_at,
        1 - (e.embedding <=> (SELECT qvec FROM q)) AS vector_score,
        row_number() OVER (ORDER BY e.embedding <=> (SELECT qvec FROM q)) AS vector_rank
      FROM chunk_embeddings e
      JOIN usable_chunks c ON c.id = e.chunk_id
      JOIN documents d ON d.id = c.document_id
      ORDER BY e.embedding <=> (SELECT qvec FROM q)
      LIMIT :candidate_limit
    ),
    kw AS (
      SELECT
        c.id AS chunk_id,
        c.document_id,
        c.chunk_index,
        c.text,
        d.title AS doc_title,
        d.created_at AS doc_created_at,
        ts_rank_cd(
          to_tsvector('english', COALESCE(c.tsv, c.text)),
          (SELECT query_terms FROM q)
        ) AS keyword_score,
        row_number() OVER (
          ORDER BY ts_rank_cd(
            to_tsvector('english', COALESCE(c.tsv, c.text)),
            (SELECT query_terms FROM q)
          ) DESC
        ) AS keyword_rank
      FROM usable_chunks c
      JOIN documents d ON d.id = c.document_id
      WHERE (SELECT query_terms FROM q) @@ to_tsvector('english', COALESCE(c.tsv, c.text))
      ORDER BY keyword_score DESC
      LIMIT :candidate_limit
    ),
    term_matches AS (
      SELECT
        c.id AS chunk_id,
        c.document_id,
        c.chunk_index,
        c.text,
        d.title AS doc_title,
        d.created_at AS doc_created_at,
        0.05 AS keyword_score,
        row_number() OVER (ORDER BY length(c.text) ASC) AS keyword_rank
      FROM usable_chunks c
      JOIN documents d ON d.id = c.document_id
      WHERE EXISTS (
        SELECT 1
        FROM unnest(:query_terms) AS term
        WHERE c.text ILIKE '%' || term || '%'
      )
      LIMIT :candidate_limit
    ),
    keyword_candidates AS (
      SELECT * FROM kw
      UNION ALL
      SELECT * FROM term_matches
    ),
    deduped_kw AS (
      SELECT DISTINCT ON (chunk_id)
        chunk_id, document_id, chunk_index, text, doc_title, doc_created_at, keyword_score, keyword_rank
      FROM keyword_candidates
      ORDER BY chunk_id, keyword_score DESC, keyword_rank ASC
    ),
    candidates AS (
      SELECT
        COALESCE(v.chunk_id, k.chunk_id) AS chunk_id,
        COALESCE(v.document_id, k.document_id) AS document_id,
        COALESCE(v.chunk_index, k.chunk_index) AS chunk_index,
        COALESCE(v.text, k.text) AS text,
        COALESCE(v.doc_title, k.doc_title) AS doc_title,
        COALESCE(v.doc_created_at, k.doc_created_at) AS doc_created_at,
        COALESCE(v.vector_score, 0) AS vector_score,
        COALESCE(k.keyword_score, 0) AS keyword_score,
        v.vector_rank,
        k.keyword_rank
      FROM vec v
      FULL OUTER JOIN deduped_kw k ON k.chunk_id = v.chunk_id
    )
    SELECT
      chunk_id,
      document_id,
      chunk_index,
      text,
      doc_title,
      doc_created_at,
      vector_score,
      keyword_score,
      vector_rank,
      keyword_rank,
      (
        0.72 * vector_score +
        0.18 * LEAST(keyword_score, 1) +
        0.10 * (
          COALESCE(1.0 / NULLIF(vector_rank, 0), 0) +
          COALESCE(1.0 / NULLIF(keyword_rank, 0), 0)
        )
      ) AS score
    FROM candidates
    ORDER BY score DESC, vector_score DESC, keyword_score DESC
    LIMIT :candidate_limit
    """)

    result = await db.execute(
        sql,
        {
            "qvec": vector_str,
            "query": query_text,
            "workspace_id": workspace_id,
            "candidate_limit": candidate_limit,
            "query_terms": _query_terms(query_text),
        },
    )

    rows = [row for row in result.mappings().all() if _passes_relevance(row, query_text)]
    return rows[:limit]

