---
id: capabilities-knowledge-0001
title: arXiv as the initial corpus
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

A knowledge base of papers requires a source. Several options:

- **arXiv** — open, large (~2M+ papers), bulk-downloadable, metadata-rich. Strong coverage in physics, math, CS, statistics, recent biology. Weaker in clinical medicine, law, humanities.
- **Semantic Scholar Open Corpus** — broader coverage including non-arXiv venues, but quality and metadata completeness vary.
- **OpenAlex** — broad, includes citation graph, but newer and less battle-tested.
- **Closed-source aggregators** — Web of Science, Scopus. Paid, license-restricted.
- **Self-curated** — too small to be useful at the start.

The validation use-case is currently centered on physics, math, and CS papers. arXiv covers these natively.

## Decision

The local paper index is populated initially from an **arXiv mirror**: bulk metadata + abstracts, ingested into the `PaperIndex` port. External lookups (Semantic Scholar) are used as a fallback for papers cited by submitted papers that are not in arXiv.

The corpus is not a hard constraint: the `PaperIndex` port is source-agnostic. Other corpora can be added (or replace arXiv) without changing the use-cases.

## Consequences

**Easy:**
- Coverage of the target domains is strong with one source.
- arXiv's bulk download mechanism is mature and well-documented.
- Identifiers (`arXiv:XXXX.YYYYY`) are stable and easy to normalize.
- Re-ingestion (refresh embeddings, update metadata) is a batch operation against a single corpus.

**Hard:**
- Papers cited from non-arXiv venues require external lookup, which adds latency to the Librarian's gather pass.
- arXiv lacks venue/peer-review status for many papers. The validation pipeline must not treat "in arXiv" as "peer-reviewed."
- Domains outside arXiv's coverage (clinical, law, humanities) are effectively unsupported by the local index until a second corpus is added.

**Forecloses:**
- A unified "all papers everywhere" experience without adding more sources. Acceptable for now; the validation product is targeted at arXiv-covered fields.

## Alternatives considered

- **OpenAlex as primary corpus** — viable; broader coverage and includes a citation graph. Rejected because metadata quality on arXiv is higher for the target domains, and arXiv has full-text PDFs accessible. OpenAlex is a candidate for a *second* corpus.
- **Semantic Scholar Open Corpus as primary** — rejected. Better used as a *complement* (external lookups for cited non-arXiv papers) than as the local index source.
- **Web of Science / Scopus** — rejected. Licensing model is incompatible with the project's open development practices.

## Review trigger

- A meaningful fraction of submitted papers cite work outside arXiv's coverage. At that point: add OpenAlex or a domain-specific corpus as a second `PaperIndex` adapter, or use the existing external-lookup capability for these cases.
- A user demographic emerges (e.g., medical researchers) whose papers are systematically not in arXiv. Time to broaden.
