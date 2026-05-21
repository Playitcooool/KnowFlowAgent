# KnowFlow Agent: An Explainable Markdown-Based Enterprise Knowledge Agent

## 1. Overview

KnowFlow Agent is a lightweight enterprise knowledge question-answering system built around a structured Markdown knowledge base, LLM-based routing, query rewriting, parallel `grep` retrieval, evidence verification, and adaptive retry.

Unlike traditional embedding-based RAG systems, KnowFlow does not rely on chunking documents into vector embeddings as the primary retrieval method. Instead, it converts all documents into Markdown, organizes them into a hierarchical knowledge base, generates human-readable indexes, and uses LLM-guided keyword search to retrieve precise evidence with file-level and line-level traceability.

The core idea is:

> Convert documents into Markdown, organize them into folders, generate indexes, route user queries to relevant folders, rewrite queries multiple times, search with `grep` in parallel, summarize evidence with an LLM, and retry with broader search scopes when the evidence is insufficient.

---

## 2. Motivation

Traditional RAG systems usually follow this pipeline:

```text
Documents → Chunking → Embedding → Vector Database → Similarity Search → LLM Answer
```

This approach works well for semantic search, but it has several limitations in enterprise knowledge-base scenarios:

1. **Low explainability**: Vector search may retrieve semantically similar but contextually incorrect chunks.
2. **Index maintenance cost**: Documents must be re-chunked and re-embedded after updates.
3. **Difficult debugging**: It is hard to know why a specific chunk was retrieved.
4. **Weak line-level traceability**: Answers are often linked to chunks rather than exact file paths and line numbers.
5. **Extra infrastructure**: A vector database and embedding pipeline increase deployment complexity.

KnowFlow Agent is designed for scenarios where documents are mostly textual and structured, such as:

- Enterprise policy documents
- Technical documentation
- API references
- Engineering guidelines
- IT operation manuals
- HR / finance / legal workflows
- GitHub issues and troubleshooting records
- Internal project documentation

For these scenarios, exact keyword search, document hierarchy, metadata, and traceable evidence are often more valuable than purely semantic retrieval.

---

## 3. System Goals

KnowFlow Agent aims to provide:

1. **Low-cost retrieval** without requiring a vector database as the default component.
2. **Explainable answers** with file paths, document names, and line numbers.
3. **Fast document updates** because Markdown files can be searched immediately after modification.
4. **LLM-guided query routing** based on generated knowledge-base indexes.
5. **Multi-query search** through LLM-based query rewriting.
6. **Adaptive retry** when the initial retrieval results are insufficient.
7. **Pluggable retrieval architecture** so that BM25 or embedding-based retrieval can be added later.

---

## 4. High-Level Architecture

```text
                         ┌────────────────────┐
                         │   Raw Documents     │
                         │ PDF / Word / HTML   │
                         │ Markdown / Issues   │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Document Converter  │
                         │ → Markdown          │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Metadata Extractor  │
                         │ title / summary     │
                         │ tags / department   │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ LLM Classifier      │
                         │ multi-label routing │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Index Builder       │
                         │ index.md            │
                         │ local_index.md      │
                         │ manifest.json       │
                         └─────────┬──────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
                 ▼                                   ▼
        ┌────────────────┐                  ┌────────────────┐
        │ Query Router    │                  │ Knowledge Base  │
        │ uses index.md   │                  │ Markdown files  │
        └───────┬────────┘                  └────────────────┘
                │
                ▼
        ┌────────────────┐
        │ Query Rewriter  │
        │ generates N     │
        │ search queries  │
        └───────┬────────┘
                │
                ▼
        ┌────────────────┐
        │ Parallel Grep   │
        │ Retriever       │
        └───────┬────────┘
                │
                ▼
        ┌────────────────┐
        │ Context Reader  │
        │ expands matched │
        │ line ranges     │
        └───────┬────────┘
                │
                ▼
        ┌────────────────┐
        │ Evidence Ranker │
        │ dedup / score   │
        └───────┬────────┘
                │
                ▼
        ┌────────────────┐
        │ Answer Agent    │
        │ grounded answer │
        └───────┬────────┘
                │
                ▼
        ┌────────────────┐
        │ Verifier Agent  │
        │ answerable?     │
        └───────┬────────┘
                │
       ┌────────┴────────┐
       │                 │
       ▼                 ▼
  Final Answer     Adaptive Retry
                   broader folders /
                   broader queries /
                   full-library search
```

---

## 5. Document Ingestion Pipeline

### 5.1 Raw Document Sources

The system can support multiple document types:

```text
data/raw/
  employee_handbook.pdf
  reimbursement_policy.docx
  api_docs.html
  engineering_guideline.md
  github_issues.json
```

Supported sources may include:

- PDF files
- Word documents
- HTML pages
- Markdown files
- GitHub issues or discussions
- Plain text files
- Exported enterprise documents

### 5.2 Markdown Conversion

All documents are converted into Markdown format.

Example tools:

- `markitdown`
- `pandoc`
- `docling`
- `pymupdf4llm`
- `unstructured`

Output structure:

```text
data/markdown/
  employee_handbook.md
  reimbursement_policy.md
  api_docs.md
  engineering_guideline.md
  github_issues.md
```

Markdown is chosen because it is:

- Easy to search with `grep` or `ripgrep`
- Easy for LLMs to read
- Friendly to headings and document structure
- Simple to version-control
- Suitable for file path and line number citations

---

## 6. Knowledge Base Organization

### 6.1 Folder-Based Organization

After conversion, the LLM classifies documents into topic folders.

Example structure:

```text
knowledge_base/
  index.md
  manifest.json

  hr/
    local_index.md
    employee_handbook.md
    leave_policy.md
    onboarding.md

  finance/
    local_index.md
    reimbursement_policy.md
    invoice_policy.md
    travel_policy.md

  it/
    local_index.md
    account_access.md
    device_policy.md
    vpn_policy.md

  engineering/
    local_index.md
    code_review.md
    deployment_process.md
    database_access.md
    incident_response.md
```

### 6.2 Multi-Label Classification

A document should not be restricted to only one category. For example, a database access policy may belong to:

- IT
- Security
- Engineering
- Database

Therefore, the system should support multi-label metadata.

Example front matter:

```yaml
---
title: Production Database Access Policy
tags: [it, security, engineering, database, access]
departments: [IT, Engineering, Security]
doc_type: policy
source: data/raw/database_access.pdf
updated_at: 2026-05-01
---
```

### 6.3 Physical Files vs Logical Views

There are two possible ways to organize files:

#### Option A: Physical Folder Placement

Each document is placed in one primary folder, while metadata stores secondary labels.

```text
knowledge_base/engineering/database_access.md
```

#### Option B: Logical Views

Documents are stored once, while folders act as logical views.

```text
docs/database_access.md
views/engineering/database_access.md -> ../../docs/database_access.md
views/security/database_access.md -> ../../docs/database_access.md
```

Option B is more robust because it avoids losing documents due to wrong classification.

---

## 7. Index Design

### 7.1 Root Index: `index.md`

The root index explains what each top-level folder is responsible for.

Example:

```md
# Enterprise Knowledge Base Index

## hr
Responsible for employee handbook, leave policy, onboarding, performance review,
benefits, workplace rules, and employee lifecycle processes.

Typical keywords: leave, onboarding, employee, attendance, performance, benefits.

## finance
Responsible for reimbursement, invoices, travel expenses, payment approval,
budget, procurement, and financial workflows.

Typical keywords: reimbursement, invoice, payment, travel, expense, approval, budget.

## it
Responsible for accounts, permissions, devices, VPN, GitHub access, software,
troubleshooting, and IT ticket processes.

Typical keywords: account, permission, GitHub, VPN, device, ticket, access.

## engineering
Responsible for development guidelines, deployment, code review, API standards,
database access, incident response, and rollback procedures.

Typical keywords: deployment, code review, API, database, incident, rollback.
```

The Query Router uses this file to decide which folders are relevant to a user query.

### 7.2 Local Index: `local_index.md`

Each folder has a local index describing the documents inside that folder.

Example:

```md
# Finance Local Index

## reimbursement_policy.md
Explains reimbursement workflow, invoice requirements, approval thresholds,
reimbursement deadlines, and required supporting materials.

## travel_policy.md
Explains business travel application, hotel standards, transportation standards,
meal allowance, and travel expense approval process.

## invoice_policy.md
Explains invoice title, invoice type, electronic invoice requirements, VAT invoice
requirements, and invalid invoice cases.
```

The File Router can use `local_index.md` to narrow the search from folder level to file level.

### 7.3 Manifest File: `manifest.json`

The manifest stores structured metadata.

Example:

```json
{
  "documents": [
    {
      "id": "doc_001",
      "path": "knowledge_base/finance/reimbursement_policy.md",
      "title": "Reimbursement Policy",
      "summary": "Explains employee reimbursement workflow, invoice requirements, approval thresholds, and deadlines.",
      "tags": ["finance", "reimbursement", "invoice", "approval", "travel"],
      "departments": ["Finance", "HR"],
      "doc_type": "policy",
      "updated_at": "2026-05-01"
    }
  ]
}
```

The manifest is useful for:

- Filtering documents
- Permission control
- Search scope restriction
- UI display
- Debugging retrieval decisions

---

## 8. Query-Time Workflow

### 8.1 User Query

Example user query:

```text
If my travel reimbursement is over 5000 yuan, who needs to approve it?
```

### 8.2 Query Router

The Query Router reads `index.md` and selects relevant folders.

Example output:

```json
{
  "target_dirs": ["finance", "hr"],
  "reason": "The question is about travel reimbursement and approval rules, which are likely covered by finance and possibly HR policies."
}
```

### 8.3 File Router

The File Router reads `local_index.md` files from the selected folders and chooses likely documents.

Example output:

```json
{
  "target_files": [
    "knowledge_base/finance/reimbursement_policy.md",
    "knowledge_base/finance/travel_policy.md"
  ],
  "reason": "These files cover reimbursement thresholds and travel expense approval rules."
}
```

### 8.4 Query Rewriting

The Query Rewriter generates multiple keyword-based search queries.

Example:

```json
{
  "queries": [
    "travel reimbursement 5000 approval",
    "reimbursement amount exceeds 5000 approver",
    "expense approval threshold 5000",
    "business travel expense approval",
    "invoice reimbursement department manager finance approval"
  ]
}
```

For Chinese documents, the query rewriter may generate Chinese keyword variants:

```json
{
  "queries": [
    "差旅 报销 5000 审批",
    "报销 金额 超过 5000 审批人",
    "费用 报销 审批 阈值",
    "出差 报销 部门负责人 财务负责人"
  ]
}
```

### 8.5 Parallel Grep Retrieval

The system executes `grep` or `ripgrep` queries in parallel.

Example command:

```bash
rg -n -i -C 5 "差旅|报销|5000|审批" knowledge_base/finance knowledge_base/hr
```

Recommended options:

```text
-n      Show line numbers
-i      Case-insensitive search
-C 5    Include 5 lines of context before and after each match
--glob  Limit search by file type or folder
```

### 8.6 Context Expansion

The initial grep results may be too narrow. The Context Reader expands each hit into a larger range.

Example:

```text
Hit: reimbursement_policy.md:42
Expanded context: reimbursement_policy.md lines 35-55
```

This helps the LLM understand the surrounding policy details.

### 8.7 Evidence Ranking and Deduplication

Parallel grep may return duplicated or overlapping snippets. The Evidence Ranker should:

1. Merge overlapping line ranges.
2. Remove duplicate snippets.
3. Score snippets by keyword coverage.
4. Prefer authoritative documents.
5. Prefer more recent documents if metadata is available.
6. Keep the top-k evidence items for answer generation.

Example evidence object:

```json
{
  "file": "knowledge_base/finance/reimbursement_policy.md",
  "line_start": 38,
  "line_end": 51,
  "score": 0.87,
  "matched_terms": ["reimbursement", "5000", "approval"],
  "text": "..."
}
```

### 8.8 Answer Generation

The Answer Agent generates a grounded answer based only on retrieved evidence.

The answer should include:

- Direct answer
- Supporting evidence
- File path and line number citations
- Uncertainty if the evidence is incomplete

Example answer:

```text
For travel reimbursement over 5000 yuan, the reimbursement must first be approved by the department manager and then reviewed by the finance manager. This is based on `finance/reimbursement_policy.md`, lines 38-51.
```

### 8.9 Evidence Verification

The Verifier Agent determines whether the evidence is sufficient to answer the user query.

Example output:

```json
{
  "answerable": true,
  "confidence": 0.84,
  "evidence_files": [
    "knowledge_base/finance/reimbursement_policy.md",
    "knowledge_base/finance/travel_policy.md"
  ],
  "missing_info": [],
  "reason": "The retrieved evidence includes both the reimbursement threshold and the required approver."
}
```

If the answer is not sufficiently supported:

```json
{
  "answerable": false,
  "confidence": 0.36,
  "missing_info": [
    "No explicit approver for reimbursements over 5000 yuan was found."
  ],
  "reason": "The retrieved evidence mentions reimbursement but does not specify the approval authority."
}
```

Then the system triggers adaptive retry.

---

## 9. Adaptive Retry Strategy

If the system cannot produce a sufficiently supported answer, it retries with a broader strategy.

Recommended retry levels:

```text
Level 1: Search selected files with precise rewritten queries.
Level 2: Search selected folders with more query rewrites.
Level 3: Expand to adjacent folders suggested by the LLM.
Level 4: Search the entire knowledge base with precise queries.
Level 5: Search the entire knowledge base with broader queries.
Level 6: Return an explicit insufficient-evidence response.
```

Example retry decision:

```json
{
  "retry_level": 3,
  "strategy": "expand_related_dirs",
  "new_target_dirs": ["finance", "hr", "it"],
  "reason": "The current evidence does not identify the approver. The approval process may be described in HR or IT workflow documents."
}
```

This makes the system more reliable than a one-shot grep search.

---

## 10. Agent Components

### 10.1 Document Converter

Responsible for converting raw documents into Markdown.

Input:

```text
PDF / Word / HTML / Markdown / JSON
```

Output:

```text
Markdown files with preserved headings and readable structure
```

### 10.2 Metadata Extractor

Extracts:

- Title
- Summary
- Keywords
- Department
- Document type
- Updated date
- Source path

### 10.3 Classifier Agent

Uses an LLM to assign multi-label categories to documents.

Output example:

```json
{
  "primary_category": "finance",
  "secondary_categories": ["hr", "travel"],
  "tags": ["reimbursement", "invoice", "approval", "business travel"]
}
```

### 10.4 Index Builder

Generates:

- Root `index.md`
- Folder-level `local_index.md`
- `manifest.json`

### 10.5 Query Router Agent

Reads `index.md` and decides which folders are likely relevant.

### 10.6 File Router Agent

Reads selected `local_index.md` files and decides which documents should be searched first.

### 10.7 Query Rewriter Agent

Generates multiple keyword-based search queries from the user question.

### 10.8 Grep Retriever

Executes parallel `grep` or `ripgrep` commands against selected folders or files.

### 10.9 Context Reader

Expands matched lines into larger context windows.

### 10.10 Evidence Ranker

Deduplicates, ranks, and filters retrieved evidence.

### 10.11 Answer Agent

Generates final user-facing answer grounded in evidence.

### 10.12 Verifier Agent

Checks whether the answer is fully supported by evidence.

---

## 11. Retrieval Algorithm

Pseudo-code:

```python
def answer_query(user_query: str):
    state = {
        "query": user_query,
        "retry_level": 1,
        "max_retry": 5,
        "evidence": []
    }

    while state["retry_level"] <= state["max_retry"]:
        target_dirs = route_query_with_index(user_query, retry_level=state["retry_level"])
        target_files = route_files_with_local_index(user_query, target_dirs)
        rewritten_queries = rewrite_query(user_query, n=5, retry_level=state["retry_level"])

        grep_results = parallel_grep(
            queries=rewritten_queries,
            target_files=target_files,
            target_dirs=target_dirs,
            context_lines=5
        )

        expanded_context = expand_context(grep_results, window_size=20)
        ranked_evidence = rank_and_deduplicate(expanded_context)
        answer = generate_answer(user_query, ranked_evidence)
        verification = verify_answer(user_query, answer, ranked_evidence)

        if verification["answerable"] and verification["confidence"] >= 0.75:
            return answer

        state["retry_level"] += 1

    return generate_insufficient_evidence_response(user_query, state["evidence"])
```

---

## 12. Example End-to-End Flow

### User Query

```text
How do I apply for GitHub repository access if I am a new employee?
```

### Step 1: Folder Routing

Selected folders:

```json
["it", "hr", "engineering"]
```

Reason:

- HR may contain onboarding rules.
- IT may contain account and permission application processes.
- Engineering may contain GitHub repository management guidelines.

### Step 2: File Routing

Selected files:

```json
[
  "knowledge_base/hr/onboarding.md",
  "knowledge_base/it/account_access.md",
  "knowledge_base/engineering/repository_management.md"
]
```

### Step 3: Query Rewriting

```json
[
  "new employee GitHub access",
  "GitHub repository permission application",
  "onboarding account access GitHub",
  "repository access approval process",
  "GitHub permission IT ticket"
]
```

### Step 4: Grep Retrieval

```bash
rg -n -i -C 5 "GitHub|repository|access|permission|onboarding" knowledge_base/it knowledge_base/hr knowledge_base/engineering
```

### Step 5: Evidence and Answer

The system retrieves lines from onboarding, IT account access, and engineering repository management documents, then produces a grounded answer with citations.

---

## 13. Evaluation Design

The system can be evaluated using a manually constructed test set.

### 13.1 Evaluation Dataset

```text
eval_set/
  single_doc_qa.json
  multi_doc_qa.json
  troubleshooting_qa.json
  policy_reasoning_qa.json
```

Example item:

```json
{
  "question": "Who approves travel reimbursement over 5000 yuan?",
  "expected_files": [
    "finance/reimbursement_policy.md",
    "finance/travel_policy.md"
  ],
  "expected_answer_keywords": [
    "department manager",
    "finance manager",
    "approval"
  ]
}
```

### 13.2 Metrics

Recommended metrics:

1. **Answer accuracy**: Whether the final answer is correct.
2. **Citation accuracy**: Whether cited files and line numbers support the answer.
3. **Evidence recall**: Whether the system retrieves the expected documents.
4. **Retry rate**: How often the system needs adaptive retry.
5. **No-answer precision**: Whether the system refuses to answer when evidence is insufficient.
6. **Latency**: End-to-end response time.
7. **Search cost**: Number of grep calls and LLM calls.

### 13.3 Baselines

Potential baselines:

- Single grep query without LLM rewriting
- Full-library grep without routing
- BM25 retrieval
- Embedding-based vector retrieval
- Hybrid retrieval

This makes the project stronger because it can compare different retrieval strategies.

---

## 14. Advantages Over Traditional Embedding RAG

| Dimension | Traditional Embedding RAG | KnowFlow Agent |
|---|---|---|
| Primary retrieval | Vector similarity | LLM-routed keyword search |
| Data format | Chunks + embeddings | Markdown files + indexes |
| Explainability | Medium | High |
| Citation granularity | Chunk-level | File-level and line-level |
| Update cost | Re-chunk and re-embed | Search immediately after file update |
| Infrastructure | Requires vector database | Requires only filesystem and grep |
| Debuggability | Harder | Easier |
| Semantic search | Strong | Depends on query rewriting |
| Exact keyword matching | Sometimes unstable | Strong |
| Best use cases | FAQ and semantic search | Policies, technical docs, operational docs |

---

## 15. Limitations

KnowFlow Agent also has limitations:

1. **Weak semantic recall**: If the query uses words very different from the document, grep may fail.
2. **Query rewriting quality matters**: The system depends on the LLM generating useful search terms.
3. **Large search outputs**: Broad grep queries may return too many irrelevant results.
4. **Classification errors**: Documents may be routed to the wrong folder if classification is poor.
5. **Non-text content**: Tables, images, and scanned PDFs may require additional processing.
6. **Long documents**: Context expansion must avoid sending too much text to the LLM.

---

## 16. Possible Extensions

### 16.1 BM25 Retriever

Add BM25 as a fallback retrieval method.

```text
Grep Retriever → BM25 Retriever → Optional Vector Retriever
```

### 16.2 Embedding Fallback

Use embedding-based retrieval only when grep and BM25 fail.

This gives the system a hybrid retrieval strategy while preserving the explainability of grep-first retrieval.

### 16.3 Permission-Aware Search

Use metadata to restrict search scope based on user permissions.

Example:

```json
{
  "user_role": "engineering_intern",
  "allowed_dirs": ["engineering", "it/public", "hr/public"]
}
```

### 16.4 Incremental Index Update

When a document changes, only regenerate metadata and local indexes for the affected folder.

### 16.5 Agent Trace Visualization

Show users:

- Selected folders
- Rewritten queries
- Grep commands
- Retrieved evidence
- Retry decisions
- Final citations

This improves trust and debuggability.

### 16.6 Evaluation Dashboard

Track:

- Retrieval success rate
- Citation accuracy
- Average retries
- Latency
- LLM token usage
- Query failure cases

---

## 17. Suggested Tech Stack

### Backend

- FastAPI
- LangGraph
- Pydantic
- Python subprocess / async execution for `ripgrep`

### Retrieval

- ripgrep
- Optional BM25
- Optional vector retriever

### Document Processing

- markitdown
- pandoc
- pymupdf4llm
- docling

### Storage

- Filesystem for Markdown files
- JSON / SQLite / PostgreSQL for metadata

### Frontend

- Vue3 or React
- Markdown renderer
- Agent trace panel
- Evidence viewer

### Deployment

- Docker
- Docker Compose

---

## 18. MVP Scope

A minimal viable version should include:

1. Convert PDF / Word / Markdown documents into Markdown.
2. Generate a root `index.md` and folder-level `local_index.md` files.
3. Route user queries to relevant folders using the root index.
4. Generate 3 to 5 rewritten grep queries.
5. Run parallel `ripgrep` searches.
6. Expand matched line ranges.
7. Generate an answer with file and line references.
8. Verify answer sufficiency.
9. Retry with broader scope up to a fixed limit.

Recommended MVP folder structure:

```text
knowflow-agent/
  app/
    main.py
    agents/
      query_router.py
      file_router.py
      query_rewriter.py
      answer_agent.py
      verifier.py
    retrieval/
      grep_retriever.py
      context_reader.py
      evidence_ranker.py
    ingestion/
      converter.py
      classifier.py
      index_builder.py
    schemas/
      document.py
      retrieval.py
      answer.py

  knowledge_base/
    index.md
    manifest.json
    hr/
      local_index.md
    finance/
      local_index.md
    it/
      local_index.md
    engineering/
      local_index.md

  eval_set/
    single_doc_qa.json
    multi_doc_qa.json

  README.md
```

---

## 19. Resume Description

### Project Name

**KnowFlow Agent: Explainable Enterprise Knowledge Agent Based on Markdown and Grep**

### One-Sentence Description

Built an explainable enterprise knowledge QA agent using FastAPI, LangGraph, Markdown, and ripgrep, enabling LLM-based folder routing, multi-query rewriting, parallel grep retrieval, evidence verification, adaptive retry, and file-line-level citation.

### Resume Bullets

- Built a multi-source document ingestion pipeline that converts PDF, Word, HTML, and Markdown files into unified Markdown while preserving headings, file paths, and line-level traceability.
- Designed an LLM-driven knowledge organization workflow that extracts document summaries, tags, and multi-label categories, then generates root-level and folder-level Markdown indexes for query routing.
- Implemented a LangGraph-based agent workflow with Query Router, File Router, Query Rewriter, Grep Retriever, Context Reader, Evidence Ranker, Answer Agent, and Verifier Agent.
- Used parallel ripgrep search over selected folders and rewritten queries, combined with context expansion, evidence deduplication, and ranking to produce grounded answers with exact file and line references.
- Designed an adaptive retry mechanism that expands search scope, relaxes query constraints, and triggers full-library search when evidence is insufficient, reducing hallucination and improving answer coverage.
- Added a pluggable retriever interface to support future BM25 and embedding-based hybrid retrieval while keeping grep-first retrieval as the default explainable strategy.

---

## 20. Summary

KnowFlow Agent is a practical alternative to traditional embedding-first RAG for enterprise knowledge bases. Its main strength is not semantic similarity search, but explainable, controllable, and debuggable retrieval over structured Markdown documents.

The system is especially suitable for policy documents, technical documentation, engineering guidelines, IT workflows, and other enterprise knowledge sources where exact evidence and traceability matter.

The key innovation is the combination of:

1. Markdown-based document normalization
2. LLM-generated hierarchical indexes
3. Query routing through `index.md`
4. Multi-query rewriting
5. Parallel grep retrieval
6. Evidence verification
7. Adaptive retry
8. File and line-level citations

This makes KnowFlow Agent a strong project for demonstrating practical Agentic Search, enterprise knowledge management, and explainable RAG system design.
