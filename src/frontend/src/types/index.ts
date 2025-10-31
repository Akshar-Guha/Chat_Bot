/**
 * TypeScript type definitions for the application
 */

export type GeneratorType = 'ollama' | 'openai' | 'huggingface' | 'spikingbrain' | 'mock';

export interface GeneratorSettings {
  type?: GeneratorType;
  model?: string;
  api_key?: string;
  api_base?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
}

export interface QueryRequest {
  query: string;
  k?: number;
  filters?: Record<string, any>;
  generator?: GeneratorSettings;
}

export interface SpikeInfo {
  sparsity_ratio: number;
  energy_efficiency: string;
  brain_inspired_features: string[];
  error?: string;
}

export interface QueryResponse {
  query: string;
  answer: string;
  chunks: Chunk[];
  provenance: ProvenanceEntry[];
  metadata: QueryMetadata;
  spike_info?: SpikeInfo;  // SpikingBrain-specific information
  verification?: VerificationMetadata;
}

export interface VerificationMetadata {
  hallucination_score: number;
  support_ratio: number;
  unsupported_claims: number;
}

export interface Chunk {
  chunk_id: string;
  text: string;
  score: number;
  metadata: ChunkMetadata;
}

export interface ChunkMetadata {
  doc_id?: string;
  start_char?: number;
  end_char?: number;
  chunk_index?: number;
  source?: string;
}

export interface ProvenanceEntry {
  chunk_id: string;
  doc_id?: string;
  score?: number;
  text_snippet: string;
}

export interface QueryMetadata {
  model: string;
  generator_type: string;
  num_chunks_retrieved: number;
  num_chunks_cited: number;
  processing_time?: number;
  confidence_score?: number;
  temperature?: number;
  max_length?: number;
  top_p?: number;
  repetition_penalty?: number;
  do_sample?: boolean;
  device?: string;
  num_chunks?: number;
  total_duration_ms?: number;
  cached?: boolean;
  reflection_enabled?: boolean;
  memory_enabled?: boolean;
}

export interface ModelInfo {
  model_name: string;
  model_type: string;
  generator_type: string;
  device: string;
  config: ModelConfig;
}

export interface ModelConfig {
  max_position_embeddings?: number | string;
  hidden_size?: number | string;
  num_attention_heads?: number | string;
  num_hidden_layers?: number | string;
}

export interface DocumentMetadata {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  num_chunks: number;
  upload_date: string;
}

export interface MemoryEntry {
  id: string;
  content: string;
  metadata: Record<string, any>;
  tags: string[];
  created_at: string;
  updated_at?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
  timestamp: string;
}

export interface IndexStats {
  total_documents: number;
  total_chunks: number;
  index_size: string;
  last_updated?: string;
}

export interface FilterOption {
  key: string;
  value: string;
  count: number;
}

export interface SearchFilters {
  doc_type?: string;
  date_range?: {
    start: string;
    end: string;
  };
  tags?: string[];
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

export interface SortState {
  field: string;
  direction: 'asc' | 'desc';
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface QueryFormProps extends BaseComponentProps {
  onSubmit: (request: QueryRequest) => void;
  loading?: boolean;
}

export interface ResultsDisplayProps extends BaseComponentProps {
  response: QueryResponse | null;
  loading: boolean;
  error: string | null;
}

export interface DocumentListProps extends BaseComponentProps {
  documents: DocumentMetadata[];
  loading: boolean;
  onDocumentSelect: (doc: DocumentMetadata) => void;
  onDocumentDelete: (docId: string) => void;
}

// Theme types
export type ThemeMode = 'light' | 'dark';

export interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
}
