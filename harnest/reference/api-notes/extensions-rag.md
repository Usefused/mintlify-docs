

## PostgreSQL configuration

| Option | Default | Purpose |
|---|---|---|
| `dsn` | None | asyncpg DSN; required unless `pool` is supplied |
| `table` | `harnest_rag_chunks` | Safe extension-owned table name |
| `pool` | None | Borrow an existing asyncpg-compatible pool without closing it |
| `setup_schema` | `True` | Create the schema, or validate an operator-managed schema when false |
| `pool_options` | None | Additional options for `asyncpg.create_pool` |
| `embedder` | None | Application-owned embedding adapter |
| `chunker` | `FixedSizeChunker()` | Application chunking policy |
| `namespace` | `default` | Fixed or per-operation tenant namespace |
| `batch_size` | 100 | Chunk texts sent to the embedder per request |

## Public API and bounds

| API | Role |
|---|---|
| `rag.postgres(...)` | Create the stock-PostgreSQL service |
| `rag.memory(...)` | Create the bounded in-memory service |
| `rag.service(...)` | Wrap a custom `RAGBackend` |
| `RAGService` | Lifecycle-owned ingestion, deletion, fetch, and search API |
| `RAGDocument`, `RAGChunk`, `RAGQuery`, `RAGHit` | Immutable provider-neutral data contracts |
| `SearchMode` | Keyword, semantic, or hybrid selection |
| `Embedder`, `Chunker`, `RAGBackend` | Replaceable provider protocols |
| `FixedSizeChunker`, `PostgresBackend`, `MemoryBackend` | Built-in implementations |

The shared boundary permits at most 1,000 documents, 50 million source characters, and 10,000 generated chunks per ingestion request. Documents may contain up to 10 million characters, individual chunks up to 1 million, queries up to 16,384, and embeddings up to 65,536 dimensions. Metadata and filters allow 64 fields, with up to 100 scalar values in one membership filter. Empty text, duplicate identities, nested metadata, boolean vector values, and non-finite numbers fail before model or datastore I/O.
