from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")

messages = [
    {"role": "system", "content": "..."},   # optional layer
    {"role": "user", "content": "Summarize this policy: ..."},
]
text = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True,
    enable_thinking=False,   # default is True
)
inputs = tokenizer([text], return_tensors="pt").to(model.device)
out = model.generate(**inputs, max_new_tokens=2048)
print(tokenizer.decode(out[0][len(inputs.input_ids[0]):], skip_special_tokens=True))