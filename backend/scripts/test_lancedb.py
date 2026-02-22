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

def vector_search(query: str, limit: int = 5):
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
        print(row.keys())
        print(f"   Vector (first 5 dims): {row['vector'][:5]}")  # Show part of the vector for verification
        print("Distance:", row['_distance'])  # Show distance for relevance
    return results

def fts_search(query: str, limit: int = 5):
    print(f"\n--- FTS Results for: '{query}' ---")
    
    # .search(query) without a vector automatically triggers FTS 
    # if the query is a string and an FTS index exists.
    results = table.search(query) \
        .limit(limit) \
        .to_pandas()

    if results.empty:
        print("No matches found.")
        return

    for i, row in results.iterrows():
        # FTS uses '_score' (higher is better) instead of '_distance'
        score = row.get('_score', 'N/A')
        print(f"{i+1}. [{row['id']}] {row['title']}")
        print(f"   Score: {score}")
        print(f"   Abstract: {row['abstract'][:150]}...\n")
    return results 


if __name__ == "__main__":
    # Test with a conceptual query
    vector_search(
        "Here we present a three-wavelength, nanosecond-pulsed laser diagnostic for the joint retrieval of temperature and particle-size distributions in WEE. To address the coupling challenge in extinction measurements within plasma-particle multiphase flows, a spectral-ratio decoupling model is developed to transform the inverse problem into a deterministic, closed-form solution, effectively isolating the temperature-dependent absorption alpha(T) from the size-dependent scattering beta(D). Furthermore, we implement a structured index-driven inversion (SID-Inv) strategy, which accelerates the inversion by four orders of magnitude compared to iterative methods. Our diagnostic platform captured tri-wavelength images covering the complete WEE evolution, which lasts only tens of microseconds. The reconstructed fields resolve the coupled evolution of plasma temperature and particle growth and coalescence, revealing a cooling-condensation pathway: the peak temperature decreased from 5742 K at 5.5 mus to 5133 K at 10 mus, while the characteristic particle diameter increased from 121.5 to 130.5 nm. This framework enables pixel-wise, synchronous retrieval in WEE and is applicable to other non-isothermal plasma-particle events.", 
        limit=5)