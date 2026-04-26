# ADR-003: PostgreSQL with Full-Text Search

## Status
Accepted

## Context
NoteKeeper requires:
- Relational data with ACID compliance
- Full-text search across note titles and content
- JSON support for flexible metadata
- Cost-effective managed solution

## Decision
We will use **PostgreSQL 15** with native **Full-Text Search** capabilities.

## Rationale

### Why PostgreSQL?
1. **ACID Compliance**: Data integrity for user content
2. **Full-Text Search**: Built-in tsvector/tsquery support
3. **JSON Support**: JSONB for flexible metadata
4. **Managed Service**: Azure Database for PostgreSQL
5. **Cost**: No additional search service needed

### Why Not Elasticsearch?
1. **Complexity**: Additional service to manage
2. **Cost**: Higher infrastructure costs
3. **Sync**: Need to maintain data synchronization
4. **Scale**: PostgreSQL FTS sufficient for expected load

## Schema Design

### Full-Text Search Column
```sql
ALTER TABLE notes ADD COLUMN search_vector tsvector;

-- GIN index for fast search
CREATE INDEX idx_notes_search ON notes USING GIN(search_vector);

-- Update trigger
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := 
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Search Query
```sql
SELECT * FROM notes
WHERE search_vector @@ plainto_tsquery('english', $1)
  AND user_id = $2
ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC;
```

## Performance

### Expected Performance
- Search latency: < 50ms for 100K notes
- Index size: ~30% of text content
- Query throughput: 1000 queries/second

### Optimization Strategies
1. **GIN Index**: Fast full-text search
2. **Limit Results**: Pagination with cursor
3. **Materialized Views**: For complex aggregations
4. **Query Caching**: Redis cache for popular searches

## Scaling Path

### Current
- Single PostgreSQL instance
- Azure Database for PostgreSQL Flexible Server (B1ms)

### Future
1. Read replicas for query load
2. Connection pooling with PgBouncer
3. Partitioning for large tables
4. Elasticsearch if search complexity grows

## Date
April 26, 2026
