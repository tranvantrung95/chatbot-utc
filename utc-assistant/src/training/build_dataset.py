"""Build a lightweight training dataset from runtime router logs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent.parent
RUNTIME_DIR = BASE_DIR / "data" / "runtime"
DEFAULT_ROUTER_EVENTS = RUNTIME_DIR / "router_events.jsonl"
DEFAULT_QUESTIONS = RUNTIME_DIR / "questions.json"
DEFAULT_OUTPUT_JSONL = BASE_DIR / "data" / "analytics" / "intent_dataset.jsonl"
DEFAULT_OUTPUT_CSV = BASE_DIR / "data" / "analytics" / "intent_dataset.csv"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _read_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def build_examples(router_events_path: Path, questions_path: Path) -> list[dict[str, Any]]:
    router_events = _read_jsonl(router_events_path)
    questions = _read_json(questions_path)
    examples = []

    for event in router_events:
        question = str(event.get("question", "")).strip()
        intent = str(event.get("intent", "")).strip()
        if question and intent:
            examples.append(
                {
                    "question": question,
                    "intent": intent,
                    "route": event.get("route", ""),
                    "retrieval_tier": event.get("retrieval_tier", ""),
                    "source": "router_events",
                }
            )

    for entry in questions:
        question = str(entry.get("question", "")).strip()
        intent = str(entry.get("intent", "")).strip()
        if question and intent:
            examples.append(
                {
                    "question": question,
                    "intent": intent,
                    "route": entry.get("route", ""),
                    "retrieval_tier": entry.get("retrieval_tier", ""),
                    "source": "questions",
                }
            )

    deduped = {}
    for example in examples:
        deduped[(example["question"], example["intent"])] = example
    return list(deduped.values())


def write_outputs(examples: list[dict[str, Any]], output_jsonl: Path, output_csv: Path) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")

    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["question", "intent", "route", "retrieval_tier", "source"],
        )
        writer.writeheader()
        writer.writerows(examples)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build intent training dataset from runtime logs.")
    parser.add_argument("--router-events", type=Path, default=DEFAULT_ROUTER_EVENTS)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    args = parser.parse_args()

    examples = build_examples(args.router_events, args.questions)
    write_outputs(examples, args.output_jsonl, args.output_csv)
    print(f"Wrote {len(examples)} examples to {args.output_jsonl} and {args.output_csv}")


if __name__ == "__main__":
    main()
