"""Simple RAG: TF-IDF retrieval over a knowledge base + Claude for answer generation."""
import os, glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic

MODEL = "claude-sonnet-4-5"   # change if needed
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def load_chunks(folder="docs", size=500):
    chunks = []
    for path in glob.glob(os.path.join(folder, "*.txt")):
        text = open(path, encoding="utf-8").read()
        for i in range(0, len(text), size):
            chunks.append((os.path.basename(path), text[i:i + size]))
    return chunks


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vec = TfidfVectorizer(stop_words="english")
        self.matrix = self.vec.fit_transform([c[1] for c in chunks])

    def search(self, query, k=3):
        scores = cosine_similarity(self.vec.transform([query]), self.matrix)[0]
        top = scores.argsort()[::-1][:k]
        return [self.chunks[i] for i in top]


def answer(question, retriever):
    context = "\n\n".join(f"[{src}] {txt}" for src, txt in retriever.search(question))
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system="Answer ONLY using the provided context. If the answer is not there, say you don't know.",
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
    )
    return msg.content[0].text


if __name__ == "__main__":
    chunks = load_chunks()
    if not chunks:
        raise SystemExit("Add .txt files to the docs/ folder first.")
    r = Retriever(chunks)
    print("RAG chatbot ready. Type 'exit' to quit.")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        print("Bot:", answer(q, r))
