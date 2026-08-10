export type DocumentRow = {
  id: number;
  title: string | null;
  source_type: string;
  source_uri?: string | null;
  mime_type?: string | null;
  size_bytes?: number | null;
  status: string;
  error?: string | null;
  created_at?: string | null;
  ingested_at?: string | null;
  source_published_at?: string | null;
  workspace_id?: string | null;
};

export type ChunkOut = {
  id: number;
  document_id: number;
  chunk_index: number;
  text: string;
  created_at?: string | null;
};

export type ChunkRow = {
  chunk_id: number | string;
  document_id: number;
  chunk_index: number;
  text: string;
  score?: number;
  title?: string | null;
  doc_title?: string | null;
};

export type IngestJobOut = {
  document_id?: number;
  status: string;
  stage?: string;
  error?: string | null;
};

export type ChatResponse = {
  answer: string;
  conversation_id: number;
  citations?: ChunkRow[];
};