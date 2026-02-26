from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def retrieve_top_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    query_text: str,
    limit: int = 8,
):
    # pgvector requires string input
    vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = text("""
    WITH q AS (
      SELECT CAST(:qvec AS vector) AS qvec
    ),
    vec AS (
      SELECT
        c.id AS chunk_id,
        c.document_id,
        c.chunk_index,
        c.text,
        d.title AS doc_title,
        d.created_at AS doc_created_at,
        1 - (e.embedding <=> (SELECT qvec FROM q)) AS vector_score
      FROM chunk_embeddings e
      JOIN chunks c ON c.id = e.chunk_id
      JOIN documents d ON d.id = c.document_id
      ORDER BY e.embedding <=> (SELECT qvec FROM q)
      LIMIT :limit
    ),
    kw AS (
      SELECT
        c.id AS chunk_id,
        ts_rank_cd(
          to_tsvector('english', COALESCE(c.tsv, c.text)),
          plainto_tsquery('english', :query)
        ) AS keyword_score
      FROM chunks c
      ORDER BY keyword_score DESC
      LIMIT :limit
    )
    SELECT
      v.chunk_id,
      v.document_id,
      v.chunk_index,
      v.text,
      v.doc_title,
      v.doc_created_at,
      v.vector_score,
      COALESCE(k.keyword_score, 0) AS keyword_score,
      -- ✅ unified score used by LLM
      (0.8 * v.vector_score + 0.2 * COALESCE(k.keyword_score, 0)) AS score
    FROM vec v
    LEFT JOIN kw k ON k.chunk_id = v.chunk_id
    ORDER BY score DESC
    """)

    result = await db.execute(
        sql,
        {
            "qvec": vector_str,
            "query": query_text,
            "limit": limit,
        },
    )

    return result.mappings().all()