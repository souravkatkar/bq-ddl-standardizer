# Models Directory

This folder is used to store **local GPT models** (in `.gguf` format) that are required for running the application.  
The models themselves are **not included in this repository** due to their size.

---

## 📥 Downloading a Model

We recommend starting with **[Phi-3-mini-4k-instruct-gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)** because it is:

- ✅ Small and lightweight (good for local inference)  
- ✅ Concise and efficient  
- ✅ Runs well on CPU and GPU  

### Steps:

1. Visit the Hugging Face model page:  
   👉 [https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)

2. Select and download a `.gguf` model file (for example, `Phi-3-mini-4k-instruct-q4.gguf`).  
   - `Q4`, `Q5`, etc. are quantization levels.  
   - Lower numbers (Q4) → smaller, faster.  
   - Higher numbers (Q8, FP16) → larger, more accurate.

3. Place the downloaded `.gguf` file inside this folder (`models/`).

---

## ⚙️ Using Different Models

- You are free to download and use **other `.gguf` models** from Hugging Face (e.g., Llama 2, Mistral, etc.).
- If you switch models, you may need to **update the prompt structure in your code** to ensure accurate responses, since each model can behave slightly differently.

Example (Python):

```python
from gpt4all import GPT4All

model = GPT4All("Phi-3-mini-4k-instruct-q4.gguf", model_path="models/")
