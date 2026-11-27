import gc
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

CONFIG_PATH = Path(__file__).with_name("config.json")
REQUIRED_KEYS = ("docs_dir", "output_path", "system_prompt", "models", "prompts")
GEN_KWARGS = dict(max_new_tokens=2048, do_sample=True, temperature=0.7, top_p=0.8, top_k=20)


def load_config(path):
    config = json.loads(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise KeyError(f"Missing keys in {path}: {missing}")
    if not config["models"] or not config["prompts"]:
        raise ValueError("'models' and 'prompts' must not be empty")
    return config


def load_documents(docs_dir):
    docs_dir = Path(docs_dir)
    if not docs_dir.is_dir():
        raise NotADirectoryError(f"docs_dir not found: {docs_dir}")
    files = sorted(docs_dir.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No .txt files in {docs_dir}")
    return [(f, f.read_text(encoding="utf-8")) for f in files]


def load_model(model_name):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        torch_dtype="auto",
        device_map="auto",
    )
    return tokenizer, model


def generate(tokenizer, model, system_prompt, retrieved_text, user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            "Retrieved context:\n"
            "<retrieved_document>\n"
            f"{retrieved_text}\n"
            "</retrieved_document>\n\n"
            f"Question: {user_prompt}"
        )},
    ]
    # enable_thinking only affects Qwen3; templates that don't use it ignore it.
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, **GEN_KWARGS)
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


def main():
    config = load_config(CONFIG_PATH)
    documents = load_documents(config["docs_dir"])
    output_path = Path(config["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as f:
        for model_name in config["models"]:
            tokenizer, model = load_model(model_name)
            try:
                for doc_path, doc_text in documents:
                    for prompt in config["prompts"]:
                        print(f"[{model_name}] {doc_path.name} | {prompt[:50]}")
                        response = generate(
                            tokenizer, model, config["system_prompt"], doc_text, prompt
                        )
                        record = {
                            "model": model_name,
                            "document": str(doc_path),
                            "prompt": prompt,
                            "response": response,
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        f.flush()
            finally:
                del model, tokenizer
                gc.collect()
                torch.cuda.empty_cache()


if __name__ == "__main__":
    main()