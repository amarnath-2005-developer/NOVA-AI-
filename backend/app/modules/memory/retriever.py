import numpy as np
from app.modules.memory.embedder import embed_text
from app.modules.memory.memory_store import MemoryStore

_store = MemoryStore()

async def get_relevant_memories(user_id: str, query_text: str, k: int = 3) -> list[str]:
    """
    Retrieves the top-k most relevant memories for a user based on semantic similarity.
    Uses brute-force cosine similarity (dot product on normalized vectors).
    """
    if not query_text.strip():
        return []

    # 1. Embed the query
    q_emb = np.array(embed_text(query_text))

    # 2. Fetch user's memories
    memories = await _store.get_user_memories(user_id)
    if not memories:
        return []

    # 3. Calculate similarities
    # We use dot product because vectors are normalized by the embedder
    results = []
    for doc in memories:
        m_emb = np.array(doc["embedding"])
        # Dot product of normalized vectors = Cosine Similarity
        similarity = np.dot(q_emb, m_emb)
        results.append((similarity, doc["text"]))

    # 4. Sort by similarity (descending) and return top-k
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Optional: Filter by a threshold (e.g., 0.5) to avoid irrelevant junk
    top_k = [text for sim, text in results[:k] if sim > 0.4]
    
    return top_k
