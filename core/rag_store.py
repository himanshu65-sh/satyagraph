from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from core.database import LiveAuditDatabase

class LiveVectorRAG:
    """
    Live Hybrid Vector RAG engine that indexes real-time fetched RSS/API records
    into SQLite and performs TF-IDF + Cosine Similarity semantic retrieval.
    """

    def __init__(self, db: LiveAuditDatabase):
        self.db = db
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    def ingest_documents(self, docs: list):
        if docs:
            self.db.upsert_live_documents(docs)

    def retrieve_relevant(self, query: str, candidate_docs: list = None, top_k: int = 8) -> list:
        pool = list(candidate_docs) if candidate_docs else []
        stored_docs = self.db.get_all_live_documents(limit=250)

        seen_urls = {d["url"] for d in pool}
        for d in stored_docs:
            if d["url"] not in seen_urls:
                pool.append(d)
                seen_urls.add(d["url"])

        if not pool:
            return []

        corpus = [f"{d['title']} {d['summary']} {d['source_name']}" for d in pool]
        try:
            tfidf_matrix = self.vectorizer.fit_transform(corpus + [query])
            query_vec = tfidf_matrix[-1]
            doc_vecs = tfidf_matrix[:-1]
            similarities = cosine_similarity(query_vec, doc_vecs).flatten()

            scored_docs = []
            for idx, score in enumerate(similarities):
                doc_copy = dict(pool[idx])
                doc_copy["relevance_score"] = round(float(score), 4)
                scored_docs.append(doc_copy)

            scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored_docs[:top_k]
        except Exception:
            return pool[:top_k]
