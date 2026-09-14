-- Enable pgvector and uuid extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Context documents table
CREATE TABLE IF NOT EXISTS contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    project VARCHAR(128) NOT NULL DEFAULT 'global',
    author_device VARCHAR(128) DEFAULT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW index for fast approximate nearest neighbor search with cosine distance
CREATE INDEX IF NOT EXISTS idx_contexts_embedding_hnsw 
ON contexts USING hnsw (embedding vector_cosine_ops);

-- GIN index for efficient tag filtering
CREATE INDEX IF NOT EXISTS idx_contexts_tags 
ON contexts USING gin (tags);

-- BTree index on project
CREATE INDEX IF NOT EXISTS idx_contexts_project 
ON contexts (project);

-- Full-text search index for hybrid ranking
CREATE INDEX IF NOT EXISTS idx_contexts_fts 
ON contexts USING gin (to_tsvector('simple', title || ' ' || content));

-- Atomic project facts table (FLCR: Fact-Level Conflict Resolution)
CREATE TABLE IF NOT EXISTS project_facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project VARCHAR(128) NOT NULL DEFAULT 'global',
    entity VARCHAR(128) NOT NULL,
    attribute VARCHAR(128) NOT NULL,
    value JSONB NOT NULL,
    source_agent VARCHAR(128) NOT NULL DEFAULT 'unknown',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    superseded_by UUID REFERENCES project_facts(id),
    conflict_flag BOOLEAN NOT NULL DEFAULT false,
    conflict_details JSONB DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_project_facts_lookup 
ON project_facts (project, entity, attribute);

CREATE INDEX IF NOT EXISTS idx_project_facts_active 
ON project_facts (project, is_active);

-- Centralized Skills Registry (Cross-Agent Skills Replication)
CREATE TABLE IF NOT EXISTS fleet_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL UNIQUE,
    version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    description TEXT,
    content_md TEXT NOT NULL,
    files_bundle JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_agent VARCHAR(128) NOT NULL DEFAULT 'unknown',
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fleet_skills_name ON fleet_skills (name);
CREATE INDEX IF NOT EXISTS idx_fleet_skills_tags ON fleet_skills USING gin (tags);

-- Centralized MCP Server Registry (Cross-Agent MCP Replication)
CREATE TABLE IF NOT EXISTS fleet_mcp_servers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL UNIQUE,
    transport VARCHAR(32) NOT NULL DEFAULT 'stdio',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_agent VARCHAR(128) NOT NULL DEFAULT 'unknown',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fleet_mcp_servers_name ON fleet_mcp_servers (name);


