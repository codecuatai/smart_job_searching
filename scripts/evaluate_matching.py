"""Evaluate the explainable matching model on a small, versioned JSONL fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ai.app.engine import match  # noqa: E402


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(ROOT / 'data/evaluation/matching_pairs.jsonl'))
    args = parser.parse_args()
    rows = load_rows(Path(args.input))
    predicted = [match(row['profileText'] if 'resumeText' in row else '', row['job'], row.get('resumeText', row['profileText']))['matchScore'] for row in rows]
    expected = [row['label'] for row in rows]
    predicted_class = [2 if score >= 75 else 1 if score >= 35 else 0 for score in predicted]
    accuracy = sum(a == b for a, b in zip(expected, predicted_class)) / len(rows)
    macro = []
    for label in (0, 1, 2):
        tp = sum(p == label and y == label for p, y in zip(predicted_class, expected))
        fp = sum(p == label and y != label for p, y in zip(predicted_class, expected))
        fn = sum(p != label and y == label for p, y in zip(predicted_class, expected))
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        macro.append((precision, recall, 2 * precision * recall / (precision + recall) if precision + recall else 0))
    precision = sum(item[0] for item in macro) / 3
    recall = sum(item[1] for item in macro) / 3
    f1 = sum(item[2] for item in macro) / 3
    mae = sum(abs(score - label * 50) for score, label in zip(predicted, expected)) / len(rows)
    result = {
        'modelVersion': match('', {'tags': ['Python'], 'requirements': [], 'description': ''})['modelVersion'],
        'samples': len(rows), 'accuracy': round(accuracy, 4), 'macroPrecision': round(precision, 4),
        'macroRecall': round(recall, 4), 'macroF1': round(f1, 4), 'maeAgainstOrdinalScale': round(mae, 4),
        'thresholds': {'notFitBelow': 35, 'partialBelow': 75, 'fitAtLeast': 75},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
