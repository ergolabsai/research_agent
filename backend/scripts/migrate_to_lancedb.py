# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

# backend/scripts/migrate_to_lancedb.py
import lancedb
import ijson
import os
from typing import Optional
from dotenv import load_dotenv
from lancedb.pydantic import LanceModel
from lancedb.embeddings import get_registry
import time
import torch

load_dotenv()

# Startup
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Embedding Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "").lower()
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-2")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
FREE_MODEL = os.getenv("FREE_MODEL", "BAAI/bge-small-en-v1.5")

def get_embedding_func():
    if EMBEDDING_PROVIDER == "voyageai" and VOYAGE_API_KEY:
        return get_registry().get("voyageai").create(name=VOYAGE_MODEL)
    if EMBEDDING_PROVIDER == "openai" and OPENAI_API_KEY:
        return get_registry().get("openai").create(name=OPENAI_MODEL)
    return get_registry().get("huggingface").create(name=FREE_MODEL, device=device)

embed_func = get_embedding_func()

# Set the dimension correctly based on the provider
if EMBEDDING_PROVIDER == "voyageai":
    DIM = 1024
elif EMBEDDING_PROVIDER == "openai":
    DIM = 1536
else:
    DIM = 384  # Default for BGE-small-en-v1.5

# --- Dynamic Schema Definition ---
def normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")

class Paper(LanceModel):
    id: str
    submitter: Optional[str]
    authors: str
    title: str
    comments: Optional[str]
    journal_ref: Optional[str]
    doi: Optional[str]
    report_no: Optional[str]
    categories: str
    license: Optional[str]
    abstract: str 
    update_date: str

def migrate(skip=0, limit=10000):
    start = time.time()
    db = lancedb.connect("backend/data/arxiv_lancedb")
    VALID_FIELDS = set(Paper.model_fields.keys())
    table_name = "papers"
    # Check if table already exists from a previous run
    if table_name in db.list_tables().tables:
        table = db.open_table(table_name)
    else:
        table = None
    print(f"Starting migration: skipping first {skip} papers, processing {limit}...")

    with open("backend/data/arxiv.json", "rb") as f:
        parser = ijson.items(f, '', multiple_values=True)
        batch = []
        count_this_session = 0
        
        for idx, paper in enumerate(parser):
            # Skip logic based on your function argument
            if idx < skip:
                continue
                
            record = {normalize_key(k): v for k, v in paper.items() if normalize_key(k) in VALID_FIELDS}
            batch.append(record)
            
            if len(batch) >= 1000:
                # Build rich context for embedding ((TODO: add number of citations, publication date, authors?? maybe mcp blocks those?))
                texts = [
                    f"Title: {item['title']}\nCategories: {item['categories']}\nAbstract: {item['abstract']}" 
                    for item in batch
                ]
                vectors = embed_func.compute_query_embeddings(texts)
                for i, r in enumerate(batch):
                    r["vector"] = vectors[i]
                
                if table is None:
                    print("Creating new table. Deleting existing data if any...")
                    table = db.create_table(table_name, data=batch, mode="create")
                else:
                    # Append for all subsequent runs
                    table.add(batch)
                
                count_this_session += len(batch)
                batch = []
                print(f"Ingested {count_this_session} papers this session (Current JSON index: {idx})\t\tTime elapsed: {time.time() - start:.2f} seconds")
                start = time.time()
            
            if count_this_session >= limit:
                break
        
        # Handle the final partial batch
        if batch:
            texts = [f"Title: {item['title']}\nCategories: {item['categories']}\nAbstract: {item['abstract']}" for item in batch]
            vectors = embed_func.compute_query_embeddings(texts)
            for i, r in enumerate(batch):
                r["vector"] = vectors[i]
            
            if table is None:
                print("Creating new table. Deleting existing data if any...")
                table = db.create_table(table_name, data=batch, mode="create")
            else:
                table.add(batch)

    print(f"Creating Full-Text Search index for {table.count_rows()} total rows...")
    table.create_fts_index(["title", "abstract"], replace=True, use_tantivy=True)
    print("Migration complete!")

if __name__ == "__main__":
    if not os.path.exists("backend/data/arxiv.json"):
        print("Error: arxiv.json file not found in backend/data/")
        print("Please download the arXiv dataset and place it at backend/data/arxiv.json before running this script.")
        print("https://www.kaggle.com/datasets/Cornell-University/arxiv?resource=download")
        exit(1)
    if not os.path.exists("backend/data"):
        print("Creating data directory...")
        os.makedirs("backend/data")

    # Session 1: migrate(skip=0, limit=2951000)
    migrate(skip=2951540, limit=1000) 
