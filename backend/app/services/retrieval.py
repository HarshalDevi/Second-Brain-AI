from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def retrieve_top_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    query_text: str,
    limit: int = 8,
):
    vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    candidate_limit = max(limit * 4, 24)

    sql = text("""
    WITH usable_chunks AS (
      SELECT *
      FROM chunks
      WHERE length(text) >= 40
        AND text !~ '[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]'
        AND (
          length(text) - length(regexp_replace(text, '[A-Za-z0-9 .,;:!?()''"/-]', '', 'g'))
        )::float / GREATEST(length(text), 1) > 0.72
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
      FULL OUTER JOIN kw k ON k.chunk_id = v.chunk_id
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
    LIMIT :limit
    """)

    result = await db.execute(
        sql,
        {
            "qvec": vector_str,
            "query": query_text,
            "limit": limit,
            "candidate_limit": candidate_limit,
        },
    )

    return result.mappings().all()