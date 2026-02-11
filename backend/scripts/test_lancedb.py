import lancedb
import os
from dotenv import load_dotenv
from lancedb.embeddings import get_registry
import torch

load_dotenv()

# Connect and Load Model
db = lancedb.connect("backend/data/arxiv_lancedb")
table = db.open_table("papers")
# Test for GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device} for embeddings")

# Use the same model as your migration
FREE_MODEL = os.getenv("FREE_MODEL", "BAAI/bge-small-en-v1.5")
embed_func = get_registry().get("huggingface").create(name=FREE_MODEL, device=device)

def search_papers(query: str, limit: int = 5):
    print(f"\n--- Results for: '{query}' ---")
    
    # Step A: Generate query vector
    query_vector = embed_func.compute_query_embeddings([query])[0]
    
    # Step B: Perform Semantic Search
    # We search the 'vector' column for things 'close' to our query_vector
    results = table.search(query_vector) \
        .limit(limit) \
        .to_pandas()

    for i, row in results.iterrows():
        print(f"{i+1}. [{row['id']}] {row['title']}")
        print(f"   Categories: {row['categories']}")
        print(f"   Abstract: {row['abstract'][:150]}...\n")

if __name__ == "__main__":
    # Test with a conceptual query
    search_papers("Which papers suggest the universe is not expanding?")