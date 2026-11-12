# NEXORA Order Agent Architecture

## System Overview
NEXORA Order Agent is an AI layer in front of existing billing tools (Vyapar, Tally, Zoho). It ingests messy customer order messages (WhatsApp chat, PDFs, audio notes), extracts structured lines using Google Gemini structured JSON output, matches items across 4 confidence layers, enforces strict business validation rules, drafts clarification questions for ambiguous lines, and presents a split-view review screen for human clerks.

Orders are only created when approved by an authorized clerk.

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEXORA Domain Pipeline                       │
└─────────────────────────────────────────────────────────────────┘
                               │
 1. Receive                    ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ Ingest raw message (dedup hash, channel, timestamp)           │
 └─────────────────────────────┬─────────────────────────────────┘
                               │
 2. Understand (Async Job)     ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ Gemini 2.0 Flash Batched Structured JSON Extraction           │
 │ Validates Pydantic schema; prompt injection treated as data   │
 └─────────────────────────────┬─────────────────────────────────┘
                               │
 3. Match (4-Layer Cascade)    ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ Layer 1: Learned Retailer Shorthand (Score = 1.00)            │
 │ Layer 2: Exact Catalogue Normalised Code/Name (Score = 0.99)  │
 │ Layer 3: RapidFuzz Token Set Ratio (Spelling/Transliteration) │
 │ Layer 4: pgvector Cosine Similarity (Embeddings)              │
 └─────────────────────────────┬─────────────────────────────────┘
                               │
 4. Flag & Validate            ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ 🟢 Green: Confident match & all business checks pass          │
 │ 🟡 Yellow: Stock low / bulk spike / unit warning              │
 │ 🔴 Red: Ambiguous candidates / missing unit / unclear         │
 └─────────────────────────────┬─────────────────────────────────┘
                               │
 5. Clarify                    ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ Pre-drafted WhatsApp question generated for RED lines         │
 └─────────────────────────────┬─────────────────────────────────┘
                               │
 6. Review & Approve (Clerk)   ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ Split-View Review Screen; inline candidate picker             │
 │ Database Trigger enforces zero RED lines before INSERT        │
 └─────────────────────────────┬─────────────────────────────────┘
                               │
 7. Record, Learn & Export     ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ Freeze order_items snapshot; append-only audit log            │
 │ Learn retailer shorthand alias; generate bill-ready CSV       │
 └───────────────────────────────────────────────────────────────┘
```

## pgvector Strategy: Exact Search vs Iterative Scan
In multi-tenant setups with Row-Level Security, an HNSW index graph can experience filtered recall degradation if the query's `tenant_id` matches only a small percentage of total vectors.
- **For Catalogues $< 10,000$ products:** Exact cosine similarity search (`ORDER BY embedding <=> query_vector LIMIT 5`) provides 100% recall with sub-millisecond execution times.
- **For Catalogues $\ge 10,000$ products:** Enable `SET LOCAL hnsw.iterative_scan = 'relaxed_order';` to allow HNSW to dynamically traverse further down the graph until sufficient tenant-matched rows are found.
