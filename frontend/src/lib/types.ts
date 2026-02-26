export type DocumentRow = {
  id: number;
  title: string;
  source_type: string;
  status: string;
  error?: string | null;
};

export type ChunkOut = {
  id: number;
  chunk_index: number;
  text: string;
};

export type ChunkRow = {
  chunk_id: string;
  document_id: number;
  chunk_index: number;
  text: string;
  score?: number;
  doc_title?: string;
};

export type IngestJobOut = {
  status: string;
  stage?: string;
  error?: string | null;
};

export type ChatResponse = {
  answer: string;
  conversation_id: number;
  citations?: ChunkRow[];
};