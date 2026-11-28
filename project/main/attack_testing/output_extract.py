# extract the output from results.jsonl
import json
from pathlib import Path

RESULTS_PATH = Path(r"D:\LLM_security\project\main\attack_testing\results.jsonl")


def print_model_outputs(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Results file not found: {path}")

    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                output = " ".join(record["response"].split())
                print(f"{record['model']} | {output}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Skipping line {line_no}: {e!r}")


if __name__ == "__main__":
    print_model_outputs(RESULTS_PATH)