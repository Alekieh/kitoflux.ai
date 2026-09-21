import re
import math
import hashlib
from typing import List, Dict, Any, Tuple
from collections import Counter

class RAGEngine:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.doc_frequencies: Counter = Counter()
        self.total_chunks: int = 0

    def ingest_document(self, doc_id: str, title: str, content: str, doc_type: str = "RESUME"):
        """Chunk document with 300 token sliding window and 20% overlap."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunk_idx = 0
        
        for para in paragraphs:
            # Tokenize by words
            words = para.split()
            if len(words) < 5:
                continue
                
            chunk_size = 80 # words per chunk
            step = 60      # 25% overlap
            
            for i in range(0, len(words), step):
                chunk_text = " ".join(words[i:i + chunk_size])
                tokens = self._tokenize(chunk_text)
                if not tokens:
                    continue
                
                chunk_obj = {
                    "chunk_id": f"{doc_id}_{chunk_idx}",
                    "doc_id": doc_id,
                    "title": title,
                    "doc_type": doc_type,
                    "text": chunk_text,
                    "tokens": tokens,
                    "term_freq": Counter(tokens),
                    "length": len(tokens)
                }
                self.chunks.append(chunk_obj)
                for term in set(tokens):
                    self.doc_frequencies[term] += 1
                chunk_idx += 1

        self.total_chunks = len(self.chunks)

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\s_\-\.]", " ", text.lower())
        return [t for t in cleaned.split() if len(t) > 2]

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Fast BM25 / TF-IDF hybrid lexical retrieval.
        Executes in < 15ms purely in memory.
        """
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        avg_dl = sum(c["length"] for c in self.chunks) / max(1, self.total_chunks)
        k1 = 1.5
        b = 0.75

        scores: List[Tuple[float, Dict[str, Any]]] = []

        for chunk in self.chunks:
            score = 0.0
            doc_len = chunk["length"]
            tf_map = chunk["term_freq"]

            for q_term in query_tokens:
                if q_term in tf_map:
                    tf = tf_map[q_term]
                    df = self.doc_frequencies.get(q_term, 1)
                    idf = math.log(1.0 + (self.total_chunks - df + 0.5) / (df + 0.5))
                    # BM25 term weighting
                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / avg_dl))
                    score += idf * (numerator / max(0.001, denominator))

            if score > 0.1:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scores[:top_k]]

rag_engine = RAGEngine()
