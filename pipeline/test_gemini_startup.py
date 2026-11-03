import os, sys, time
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

def test_startup_gemini():
    model_name = os.getenv("GEMINI_MODEL")
    if not model_name:
        raise ValueError("GEMINI_MODEL env var is not set!")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY env var is not set!")

    print(f"Initializing Gemini client with model from GEMINI_MODEL='{model_name}'...")
    client = genai.Client(api_key=api_key)
    
    # Minimal thinking config for extraction / latency
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        temperature=0.1
    )
    
    prompt = "Extract ticker and exchange as JSON from: 'Reliance Industries Ltd trades on NSE under RELIANCE'."
    t0 = time.time()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    elapsed = round(time.time() - t0, 3)

    usage = response.usage_metadata
    total_tokens = getattr(usage, "total_token_count", 0)
    prompt_tokens = getattr(usage, "prompt_token_count", 0)
    candidates_tokens = getattr(usage, "candidates_token_count", 0)
    thinking_tokens = max(total_tokens - prompt_tokens - candidates_tokens, 0)

    print(f"✅ Startup Gemini Test Call Succeeded in {elapsed}s:")
    print(f"   Model:           {model_name}")
    print(f"   Input tokens:    {prompt_tokens}")
    print(f"   Output tokens:   {candidates_tokens}")
    print(f"   Thinking tokens: {thinking_tokens} (billed as output; minimal budget enforced = 0)")
    print(f"   Total tokens:    {total_tokens}")
    print(f"   Response text:   {response.text.strip()}")

if __name__ == "__main__":
    test_startup_gemini()

