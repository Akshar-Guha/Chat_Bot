-- ================================================================================
-- EideticRAG Database Schema - Neon PostgreSQL
-- Comprehensive schema for all API endpoints with Data and Logging tables
-- ================================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- ================================================================================
-- CORE DATA TABLES
-- ================================================================================

-- Documents: Store ingested documents metadata
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id VARCHAR(255) UNIQUE NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    content_hash VARCHAR(64),
    ingestion_status VARCHAR(50) DEFAULT 'pending',
    num_chunks INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ingested_by VARCHAR(255),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_documents_doc_id ON documents(doc_id);
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
CREATE INDEX idx_documents_is_deleted ON documents(is_deleted) WHERE is_deleted = FALSE;

-- Document Chunks: Store processed text chunks with embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    doc_id VARCHAR(255) NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    embedding vector(384), -- all-MiniLM-L6-v2 dimension
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    chunk_size INTEGER,
    chunk_overlap INTEGER,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(doc_id, chunk_index)
);

CREATE INDEX idx_chunks_chunk_id ON document_chunks(chunk_id);
CREATE INDEX idx_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX idx_chunks_metadata ON document_chunks USING GIN(metadata);
CREATE INDEX idx_chunks_text_search ON document_chunks USING GIN(to_tsvector('english', text_content));
-- Vector similarity search index (using HNSW for efficient nearest neighbor search)
CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw(embedding vector_cosine_ops);

-- ================================================================================
-- QUERY & INTERACTION TABLES
-- ================================================================================

-- Queries: Store all user queries
CREATE TABLE IF NOT EXISTS queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id VARCHAR(255) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64),
    intent VARCHAR(50),
    intent_confidence NUMERIC(5,4),
    k_value INTEGER DEFAULT 5,
    filters JSONB DEFAULT '{}'::jsonb,
    use_cache BOOLEAN DEFAULT TRUE,
    use_memory BOOLEAN DEFAULT TRUE,
    use_reflection BOOLEAN DEFAULT TRUE,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_queries_query_id ON queries(query_id);
CREATE INDEX idx_queries_created_at ON queries(created_at DESC);
CREATE INDEX idx_queries_session_id ON queries(session_id);
CREATE INDEX idx_queries_intent ON queries(intent);
CREATE INDEX idx_queries_text_search ON queries USING GIN(to_tsvector('english', query_text));
CREATE INDEX idx_queries_query_hash ON queries(query_hash);

-- Query Results: Store complete query processing results
CREATE TABLE IF NOT EXISTS query_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id VARCHAR(255) UNIQUE NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    answer_length INTEGER,
    model_used VARCHAR(100),
    generator_type VARCHAR(50),
    temperature NUMERIC(3,2),
    num_chunks_retrieved INTEGER,
    chunks_used JSONB DEFAULT '[]'::jsonb,
    provenance JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_query_results_query_id ON query_results(query_id);
CREATE INDEX idx_query_results_model_used ON query_results(model_used);
CREATE INDEX idx_query_results_created_at ON query_results(created_at DESC);

-- Retrieved Chunks: Link between queries and chunks
CREATE TABLE IF NOT EXISTS query_chunk_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id VARCHAR(255) NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    chunk_id VARCHAR(255) NOT NULL REFERENCES document_chunks(chunk_id) ON DELETE CASCADE,
    similarity_score NUMERIC(8,6),
    rank INTEGER,
    used_in_generation BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(query_id, chunk_id)
);

CREATE INDEX idx_query_chunk_query_id ON query_chunk_mappings(query_id);
CREATE INDEX idx_query_chunk_chunk_id ON query_chunk_mappings(chunk_id);
CREATE INDEX idx_query_chunk_score ON query_chunk_mappings(similarity_score DESC);

-- ================================================================================
-- MEMORY SYSTEM TABLES
-- ================================================================================

-- Memory Entries: Store conversation memory
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id VARCHAR(255) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    chunk_ids JSONB DEFAULT '[]'::jsonb,
    chunk_scores JSONB DEFAULT '[]'::jsonb,
    intent VARCHAR(50),
    intent_confidence NUMERIC(5,4),
    model_used VARCHAR(100),
    importance_score NUMERIC(3,2) DEFAULT 0.5,
    user_feedback VARCHAR(20), -- positive, negative, neutral
    feedback_text TEXT,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    is_edited BOOLEAN DEFAULT FALSE,
    original_answer TEXT,
    edit_timestamp TIMESTAMP WITH TIME ZONE,
    is_private BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_memory_entries_memory_id ON memory_entries(memory_id);
CREATE INDEX idx_memory_entries_created_at ON memory_entries(created_at DESC);
CREATE INDEX idx_memory_entries_importance ON memory_entries(importance_score DESC);
CREATE INDEX idx_memory_entries_session_id ON memory_entries(session_id);
CREATE INDEX idx_memory_entries_is_deleted ON memory_entries(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX idx_memory_entries_text_search ON memory_entries USING GIN(to_tsvector('english', query_text || ' ' || answer_text));

-- Memory Index: For semantic search on memories
CREATE TABLE IF NOT EXISTS memory_index (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    index_id VARCHAR(255) UNIQUE NOT NULL,
    memory_id VARCHAR(255) NOT NULL REFERENCES memory_entries(memory_id) ON DELETE CASCADE,
    embedding vector(384),
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    keywords JSONB DEFAULT '[]'::jsonb,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_memory_index_memory_id ON memory_index(memory_id);
CREATE INDEX idx_memory_index_embedding ON memory_index USING hnsw(embedding vector_cosine_ops);
CREATE INDEX idx_memory_index_keywords ON memory_index USING GIN(keywords);

-- Conversation Sessions: Group memories by conversation
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500),
    description TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    memory_ids JSONB DEFAULT '[]'::jsonb,
    query_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    user_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_session_id ON conversation_sessions(session_id);
CREATE INDEX idx_sessions_start_time ON conversation_sessions(start_time DESC);
CREATE INDEX idx_sessions_is_active ON conversation_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_sessions_tags ON conversation_sessions USING GIN(tags);

-- ================================================================================
-- REFLECTION & VERIFICATION TABLES
-- ================================================================================

-- Reflection Results: Store reflection agent results
CREATE TABLE IF NOT EXISTS reflection_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reflection_id VARCHAR(255) UNIQUE NOT NULL,
    query_id VARCHAR(255) NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    initial_answer TEXT NOT NULL,
    final_answer TEXT NOT NULL,
    hallucination_score NUMERIC(5,4),
    support_ratio NUMERIC(5,4),
    unsupported_claims JSONB DEFAULT '[]'::jsonb,
    verification_status VARCHAR(50),
    decision_action VARCHAR(50),
    iterations INTEGER DEFAULT 1,
    max_iterations INTEGER DEFAULT 3,
    improvement_score NUMERIC(5,4),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reflection_reflection_id ON reflection_results(reflection_id);
CREATE INDEX idx_reflection_query_id ON reflection_results(query_id);
CREATE INDEX idx_reflection_hallucination ON reflection_results(hallucination_score DESC);
CREATE INDEX idx_reflection_created_at ON reflection_results(created_at DESC);

-- ================================================================================
-- CACHE TABLES
-- ================================================================================

-- Cache Operations: Track cache usage
CREATE TABLE IF NOT EXISTS cache_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_type VARCHAR(50) NOT NULL, -- embedding, retrieval, query
    cache_key VARCHAR(255) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- hit, miss, set, invalidate
    data_size_bytes INTEGER,
    ttl_seconds INTEGER,
    hit BOOLEAN,
    query_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cache_ops_cache_type ON cache_operations(cache_type);
CREATE INDEX idx_cache_ops_operation ON cache_operations(operation);
CREATE INDEX idx_cache_ops_created_at ON cache_operations(created_at DESC);
CREATE INDEX idx_cache_ops_query_id ON cache_operations(query_id);

-- ================================================================================
-- LOGGING TABLES (History & Audit)
-- ================================================================================

-- API Request Logs: Track all API requests
CREATE TABLE IF NOT EXISTS api_request_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(255) UNIQUE NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    duration_ms NUMERIC(10,2),
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    query_id VARCHAR(255),
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    request_body JSONB,
    response_body JSONB,
    error_message TEXT,
    error_traceback TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_logs_request_id ON api_request_logs(request_id);
CREATE INDEX idx_api_logs_endpoint ON api_request_logs(endpoint);
CREATE INDEX idx_api_logs_method ON api_request_logs(method);
CREATE INDEX idx_api_logs_status_code ON api_request_logs(status_code);
CREATE INDEX idx_api_logs_created_at ON api_request_logs(created_at DESC);
CREATE INDEX idx_api_logs_query_id ON api_request_logs(query_id);
CREATE INDEX idx_api_logs_duration ON api_request_logs(duration_ms DESC);

-- Document Ingestion Logs: Track document processing
CREATE TABLE IF NOT EXISTS document_ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingestion_id VARCHAR(255) UNIQUE NOT NULL,
    doc_id VARCHAR(255) REFERENCES documents(doc_id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    status VARCHAR(50) NOT NULL, -- processing, completed, failed
    num_chunks_created INTEGER DEFAULT 0,
    duration_ms NUMERIC(10,2),
    error_message TEXT,
    error_traceback TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ingestion_logs_ingestion_id ON document_ingestion_logs(ingestion_id);
CREATE INDEX idx_ingestion_logs_doc_id ON document_ingestion_logs(doc_id);
CREATE INDEX idx_ingestion_logs_status ON document_ingestion_logs(status);
CREATE INDEX idx_ingestion_logs_started_at ON document_ingestion_logs(started_at DESC);

-- Retrieval Logs: Track retrieval operations
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retrieval_id VARCHAR(255) UNIQUE NOT NULL,
    query_id VARCHAR(255) NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    strategy VARCHAR(50),
    num_chunks_retrieved INTEGER,
    avg_similarity_score NUMERIC(8,6),
    min_similarity_score NUMERIC(8,6),
    max_similarity_score NUMERIC(8,6),
    policy_used JSONB DEFAULT '{}'::jsonb,
    duration_ms NUMERIC(10,2),
    cache_hit BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_retrieval_logs_retrieval_id ON retrieval_logs(retrieval_id);
CREATE INDEX idx_retrieval_logs_query_id ON retrieval_logs(query_id);
CREATE INDEX idx_retrieval_logs_strategy ON retrieval_logs(strategy);
CREATE INDEX idx_retrieval_logs_created_at ON retrieval_logs(created_at DESC);
CREATE INDEX idx_retrieval_logs_duration ON retrieval_logs(duration_ms DESC);

-- Generation Logs: Track LLM generation operations
CREATE TABLE IF NOT EXISTS generation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_id VARCHAR(255) UNIQUE NOT NULL,
    query_id VARCHAR(255) NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    model VARCHAR(100) NOT NULL,
    generator_type VARCHAR(50),
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tokens_total INTEGER,
    temperature NUMERIC(3,2),
    top_p NUMERIC(3,2),
    max_tokens INTEGER,
    duration_ms NUMERIC(10,2),
    cost_usd NUMERIC(10,6),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_generation_logs_generation_id ON generation_logs(generation_id);
CREATE INDEX idx_generation_logs_query_id ON generation_logs(query_id);
CREATE INDEX idx_generation_logs_model ON generation_logs(model);
CREATE INDEX idx_generation_logs_created_at ON generation_logs(created_at DESC);
CREATE INDEX idx_generation_logs_tokens_total ON generation_logs(tokens_total DESC);

-- Memory Operation Logs: Track memory CRUD operations
CREATE TABLE IF NOT EXISTS memory_operation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_id VARCHAR(255) UNIQUE NOT NULL,
    operation VARCHAR(50) NOT NULL, -- create, read, update, delete, search
    memory_id VARCHAR(255),
    success BOOLEAN DEFAULT TRUE,
    duration_ms NUMERIC(10,2),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_memory_ops_operation_id ON memory_operation_logs(operation_id);
CREATE INDEX idx_memory_ops_operation ON memory_operation_logs(operation);
CREATE INDEX idx_memory_ops_memory_id ON memory_operation_logs(memory_id);
CREATE INDEX idx_memory_ops_created_at ON memory_operation_logs(created_at DESC);
CREATE INDEX idx_memory_ops_success ON memory_operation_logs(success);

-- ================================================================================
-- PERFORMANCE & METRICS TABLES
-- ================================================================================

-- Performance Metrics: Aggregate performance data
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type VARCHAR(100) NOT NULL, -- query_processing, document_ingestion, retrieval, generation, etc.
    operation_id VARCHAR(255),
    duration_ms NUMERIC(10,2),
    success BOOLEAN DEFAULT TRUE,
    resource_usage JSONB DEFAULT '{}'::jsonb, -- CPU, memory, etc.
    throughput NUMERIC(10,2),
    latency_p50 NUMERIC(10,2),
    latency_p95 NUMERIC(10,2),
    latency_p99 NUMERIC(10,2),
    error_rate NUMERIC(5,4),
    metadata JSONB DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_perf_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX idx_perf_metrics_recorded_at ON performance_metrics(recorded_at DESC);
CREATE INDEX idx_perf_metrics_success ON performance_metrics(success);
CREATE INDEX idx_perf_metrics_duration ON performance_metrics(duration_ms DESC);

-- System Statistics: Store system-wide statistics
CREATE TABLE IF NOT EXISTS system_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stat_name VARCHAR(100) UNIQUE NOT NULL,
    stat_value NUMERIC,
    stat_value_json JSONB,
    description TEXT,
    category VARCHAR(50), -- index, cache, memory, api, etc.
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_system_stats_stat_name ON system_statistics(stat_name);
CREATE INDEX idx_system_stats_category ON system_statistics(category);
CREATE INDEX idx_system_stats_updated_at ON system_statistics(updated_at DESC);

-- ================================================================================
-- ERROR & AUDIT TABLES
-- ================================================================================

-- Error Logs: Centralized error tracking
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_id VARCHAR(255) UNIQUE NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    error_traceback TEXT,
    context VARCHAR(100), -- query_processing, document_ingestion, etc.
    severity VARCHAR(20), -- error, warning, critical
    query_id VARCHAR(255),
    doc_id VARCHAR(255),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    request_id VARCHAR(255),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_error_logs_error_id ON error_logs(error_id);
CREATE INDEX idx_error_logs_error_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_context ON error_logs(context);
CREATE INDEX idx_error_logs_severity ON error_logs(severity);
CREATE INDEX idx_error_logs_created_at ON error_logs(created_at DESC);
CREATE INDEX idx_error_logs_resolved ON error_logs(resolved) WHERE resolved = FALSE;

-- Audit Trail: Track all data modifications
CREATE TABLE IF NOT EXISTS audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(255) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_audit_trail_table_name ON audit_trail(table_name);
CREATE INDEX idx_audit_trail_record_id ON audit_trail(record_id);
CREATE INDEX idx_audit_trail_operation ON audit_trail(operation);
CREATE INDEX idx_audit_trail_changed_at ON audit_trail(changed_at DESC);

-- ================================================================================
-- VIEWS FOR ANALYTICS
-- ================================================================================

-- Query Performance Summary View
CREATE OR REPLACE VIEW v_query_performance_summary AS
SELECT 
    DATE_TRUNC('hour', q.created_at) as time_bucket,
    COUNT(DISTINCT q.query_id) as total_queries,
    AVG(arl.duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY arl.duration_ms) as p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY arl.duration_ms) as p95_duration_ms,
    COUNT(CASE WHEN arl.status_code >= 400 THEN 1 END) as error_count,
    COUNT(CASE WHEN co.hit = TRUE THEN 1 END) as cache_hits,
    COUNT(CASE WHEN co.hit = FALSE THEN 1 END) as cache_misses
FROM queries q
LEFT JOIN api_request_logs arl ON q.query_id = arl.query_id
LEFT JOIN cache_operations co ON q.query_id = co.query_id AND co.operation = 'hit'
GROUP BY time_bucket
ORDER BY time_bucket DESC;

-- Document Processing Summary View
CREATE OR REPLACE VIEW v_document_summary AS
SELECT 
    d.doc_id,
    d.filename,
    d.num_chunks,
    d.created_at,
    COUNT(DISTINCT dc.id) as actual_chunk_count,
    AVG(dc.chunk_size) as avg_chunk_size,
    SUM(dc.token_count) as total_tokens
FROM documents d
LEFT JOIN document_chunks dc ON d.doc_id = dc.doc_id
WHERE d.is_deleted = FALSE
GROUP BY d.doc_id, d.filename, d.num_chunks, d.created_at;

-- Memory Usage Summary View
CREATE OR REPLACE VIEW v_memory_usage_summary AS
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as memories_created,
    AVG(importance_score) as avg_importance,
    COUNT(CASE WHEN user_feedback = 'positive' THEN 1 END) as positive_feedback,
    COUNT(CASE WHEN user_feedback = 'negative' THEN 1 END) as negative_feedback,
    COUNT(CASE WHEN is_edited = TRUE THEN 1 END) as edited_memories
FROM memory_entries
WHERE is_deleted = FALSE
GROUP BY day
ORDER BY day DESC;

-- System Health Dashboard View
CREATE OR REPLACE VIEW v_system_health AS
SELECT 
    (SELECT COUNT(*) FROM documents WHERE is_deleted = FALSE) as total_documents,
    (SELECT COUNT(*) FROM document_chunks) as total_chunks,
    (SELECT COUNT(*) FROM queries WHERE created_at > NOW() - INTERVAL '24 hours') as queries_24h,
    (SELECT COUNT(*) FROM memory_entries WHERE is_deleted = FALSE) as total_memories,
    (SELECT AVG(duration_ms) FROM api_request_logs WHERE created_at > NOW() - INTERVAL '1 hour') as avg_response_time_1h,
    (SELECT COUNT(*) FROM error_logs WHERE resolved = FALSE AND created_at > NOW() - INTERVAL '24 hours') as unresolved_errors_24h,
    (SELECT hit_rate FROM (
        SELECT 
            CASE 
                WHEN COUNT(CASE WHEN hit = FALSE THEN 1 END) = 0 THEN 0
                ELSE COUNT(CASE WHEN hit = TRUE THEN 1 END)::NUMERIC / 
                     (COUNT(CASE WHEN hit = TRUE THEN 1 END) + COUNT(CASE WHEN hit = FALSE THEN 1 END))::NUMERIC
            END as hit_rate
        FROM cache_operations 
        WHERE created_at > NOW() - INTERVAL '1 hour'
    ) sub) as cache_hit_rate_1h;

-- ================================================================================
-- FUNCTIONS & TRIGGERS
-- ================================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_entries_updated_at BEFORE UPDATE ON memory_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate query hash
CREATE OR REPLACE FUNCTION generate_query_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.query_hash = MD5(LOWER(TRIM(NEW.query_text)));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply query hash trigger
CREATE TRIGGER generate_query_hash_trigger BEFORE INSERT ON queries
    FOR EACH ROW EXECUTE FUNCTION generate_query_hash();

-- Function for audit logging (optional - can be enabled per table)
CREATE OR REPLACE FUNCTION audit_log_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (table_name, record_id, operation, old_values)
        VALUES (TG_TABLE_NAME, OLD.id::TEXT, 'DELETE', row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (table_name, record_id, operation, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id::TEXT, 'UPDATE', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (table_name, record_id, operation, new_values)
        VALUES (TG_TABLE_NAME, NEW.id::TEXT, 'INSERT', row_to_json(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================
-- INITIAL DATA & STATISTICS
-- ================================================================================

-- Initialize system statistics
INSERT INTO system_statistics (stat_name, stat_value, description, category) VALUES
    ('total_queries', 0, 'Total number of queries processed', 'api'),
    ('total_documents', 0, 'Total number of documents ingested', 'index'),
    ('total_chunks', 0, 'Total number of document chunks', 'index'),
    ('total_memories', 0, 'Total number of memory entries', 'memory'),
    ('cache_hit_rate', 0, 'Overall cache hit rate', 'cache'),
    ('avg_query_time_ms', 0, 'Average query processing time', 'performance')
ON CONFLICT (stat_name) DO NOTHING;

-- ================================================================================
-- COMMENTS & DOCUMENTATION
-- ================================================================================

COMMENT ON TABLE documents IS 'Core document metadata and ingestion tracking';
COMMENT ON TABLE document_chunks IS 'Processed text chunks with vector embeddings for semantic search';
COMMENT ON TABLE queries IS 'User queries with intent classification and configuration';
COMMENT ON TABLE query_results IS 'Complete query processing results including generated answers';
COMMENT ON TABLE memory_entries IS 'Conversation memory for context-aware responses';
COMMENT ON TABLE reflection_results IS 'Reflection agent verification and hallucination detection results';
COMMENT ON TABLE api_request_logs IS 'Complete API request/response audit trail';
COMMENT ON TABLE performance_metrics IS 'System performance monitoring and optimization data';
COMMENT ON TABLE error_logs IS 'Centralized error tracking and resolution';

-- ================================================================================
-- GRANTS & PERMISSIONS (Adjust based on your needs)
-- ================================================================================

-- Grant necessary permissions (adjust user as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ================================================================================
-- COMPLETION
-- ================================================================================

SELECT 'EideticRAG database schema created successfully!' as status;
