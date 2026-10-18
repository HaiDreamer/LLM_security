from pathlib import Path

from datasets import load_dataset

# Configuration
DATASET_NAME = "nvidia/Nemotron-Content-VISafe-v1"
OUTPUT_DIR = Path(r"D:\LLM_security\datasets\nvidia___nemotron-content-vi_safe-v1")
OUTPUT_FILE = OUTPUT_DIR / "visafe.jsonl"

def main() -> None:
    # Create the output directory if it does not exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load the dataset
    print(f"Loading dataset: {DATASET_NAME}")

    ds = load_dataset(
        DATASET_NAME,
        cache_dir=str(OUTPUT_DIR),
    )

    # Display available splits
    print("\nDataset information:")
    print(ds)

    # Export the training split to JSONL
    train_dataset = ds["train"]

    train_dataset.to_json(
        str(OUTPUT_FILE),
        orient="records",
        lines=True,
        force_ascii=False,
    )

    print(f"\nExport completed successfully!")
    print(f"Number of records: {len(train_dataset)}")
    print(f"Output file: {OUTPUT_FILE}")

    # Display the first exported record
    print("\nFirst record:")
    print(train_dataset[0])


if __name__ == "__main__":
    main()
