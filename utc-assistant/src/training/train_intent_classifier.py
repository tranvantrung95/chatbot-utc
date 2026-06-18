"""Train a lightweight intent classifier from labeled dataset."""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET = BASE_DIR / "data" / "analytics" / "intent_dataset.jsonl"
DEFAULT_MODELS_DIR = BASE_DIR / "models"


def _load_dataset(dataset_path: Path) -> tuple[list[str], list[str]]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    questions: list[str] = []
    intents: list[str] = []
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        question = str(payload.get("question", "")).strip()
        intent = str(payload.get("intent", "")).strip()
        if question and intent:
            questions.append(question)
            intents.append(intent)
    if not questions:
        raise ValueError("Dataset is empty after filtering invalid rows")
    return questions, intents


def _dump_artifact(path: Path, artifact: object) -> None:
    try:
        import joblib  # type: ignore
    except ImportError:
        joblib = None

    if joblib is not None:
        joblib.dump(artifact, path)
        return

    with path.open("wb") as handle:
        pickle.dump(artifact, handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train phase-1 intent classifier.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR)
    parser.add_argument(
        "--algorithm",
        choices=["logreg", "linearsvc"],
        default="logreg",
    )
    args = parser.parse_args()

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.svm import LinearSVC
    except ImportError as exc:  # pragma: no cover - depends on optional dependency.
        raise SystemExit(
            "scikit-learn chưa được cài. Cài `scikit-learn` rồi chạy lại script train."
        ) from exc

    questions, intents = _load_dataset(args.dataset)

    if args.algorithm == "logreg":
        classifier = LogisticRegression(max_iter=500)
    else:
        classifier = LinearSVC()

    model = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", classifier),
        ]
    )
    model.fit(questions, intents)

    args.models_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.models_dir / "intent_classifier.joblib"
    label_map_path = args.models_dir / "intent_label_map.json"
    thresholds_path = args.models_dir / "router_thresholds.json"

    _dump_artifact(model_path, model)
    label_map_path.write_text(
        json.dumps({intent: intent for intent in sorted(set(intents))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not thresholds_path.exists():
        thresholds_path.write_text(json.dumps({}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved classifier to {model_path}")


if __name__ == "__main__":
    main()
