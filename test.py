from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("huihui-ai/Llama-3.2-3B-Instruct-abliterated")
m = [{"role": "user", "content": "hi"}]
a = tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
b = tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True, enable_thinking=False)
print(a == b)  # expect True