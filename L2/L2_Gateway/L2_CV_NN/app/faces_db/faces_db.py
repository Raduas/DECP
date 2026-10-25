import pickle
from pathlib import Path


class FaceDB:
    def __init__(self, path="faces_db/faces.pkl"):
        self.path = Path(path)
        self.data = {}  # jméno -> [embedding, ...]
        if self.path.exists():
            self.data = pickle.loads(self.path.read_bytes())

    def add(self, name, embedding):
        self.data.setdefault(name, []).append(embedding)
        self.path.write_bytes(pickle.dumps(self.data))

    def identify(self, recognizer, embedding):
        best_name, best_score = None, -1.0
        for name, embs in self.data.items():
            score = max(recognizer.compare(embedding, e) for e in embs)
            if score > best_score:
                best_name, best_score = name, score
        if best_score >= recognizer.COSINE_THRESHOLD:
            return best_name, best_score
        return "unknown", best_score
