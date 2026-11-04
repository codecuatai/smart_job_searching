"""Train the tiny ordinal logistic scorer used by the offline AI service."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ai.app.engine import matching_features  # noqa: E402


def sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-max(-30, min(30, value))))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(ROOT / 'data/evaluation/matching_pairs.jsonl'))
    parser.add_argument('--output', default=str(ROOT / 'services/ai/models/matching-v2.json'))
    parser.add_argument('--iterations', type=int, default=2500)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding='utf-8').splitlines() if line.strip()]
    vectors = []
    labels = []
    for row in rows:
        _, _, _, coverage, similarity, required_ratio = matching_features(row['profileText'], row['job'])
        vectors.append([1.0, coverage, similarity, required_ratio])
        labels.append(row['label'] / 2)
    weights = [0.0] * 4
    learning_rate = 0.45
    for _ in range(args.iterations):
        gradient = [0.0] * 4
        for vector, target in zip(vectors, labels):
            prediction = sigmoid(sum(a * b for a, b in zip(weights, vector)))
            error = prediction - target
            for index, value in enumerate(vector):
                gradient[index] += error * value / len(rows)
        for index in range(4):
            weights[index] -= learning_rate * gradient[index]
    output = {
        'version': 'hybrid-v2', 'bias': round(weights[0], 6),
        'weights': {'coverage': round(weights[1], 6), 'cosineSimilarity': round(weights[2], 6),
                    'requiredSkillRatio': round(weights[3], 6)},
        'trainedOn': str(Path(args.input).resolve().relative_to(ROOT).as_posix()), 'samples': len(rows),
        'description': 'Ordinal logistic scorer trained by gradient descent on the versioned evaluation fixture.',
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
