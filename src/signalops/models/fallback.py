"""TF-IDF + LogisticRegression fallback classifier for when LLM is unavailable."""

from __future__ import annotations

from typing import Any


class TFIDFFallbackClassifier:
    """Offline TF-IDF + LogisticRegression classifier as fallback."""

    def __init__(self) -> None:
        self.vectorizer: Any = None
        self.classifier: Any = None
        self.is_trained = False

    def train(self, texts: list[str], labels: list[str]) -> dict[str, Any]:
        """Train from labeled examples. Returns training metrics."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score
        except ImportError:
            raise ImportError(
                "scikit-learn is required for the fallback classifier. "
                "Install it with: pip install scikit-learn"
            )

        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        features = self.vectorizer.fit_transform(texts)

        self.classifier = LogisticRegression(max_iter=1000, random_state=42)
        self.classifier.fit(features, labels)
        self.is_trained = True

        # Cross-validation score
        n_splits = min(5, len(texts))
        if n_splits >= 2:
            scores = cross_val_score(self.classifier, features, labels, cv=n_splits)
            accuracy = float(scores.mean())
        else:
            accuracy = 0.0

        return {"accuracy": accuracy, "n_examples": len(texts)}

    def predict(self, text: str) -> tuple[str, float]:
        """Returns (label, confidence)."""
        if not self.is_trained or self.vectorizer is None or self.classifier is None:
            raise RuntimeError("Classifier not trained — call train() first")

        features = self.vectorizer.transform([text])
        predicted_label = self.classifier.predict(features)[0]
        probabilities = self.classifier.predict_proba(features)[0]
        confidence = float(max(probabilities))

        return predicted_label, confidence

    def save(self, path: str) -> None:
        """Serialize model with joblib."""
        try:
            import joblib
        except ImportError:
            raise ImportError("joblib is required. Install it with: pip install joblib")

        joblib.dump({"vectorizer": self.vectorizer, "classifier": self.classifier}, path)

    def load(self, path: str) -> None:
        """Load serialized model."""
        try:
            import joblib
        except ImportError:
            raise ImportError("joblib is required. Install it with: pip install joblib")

        data = joblib.load(path)
        self.vectorizer = data["vectorizer"]
        self.classifier = data["classifier"]
        self.is_trained = True
