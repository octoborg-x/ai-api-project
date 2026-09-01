import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

MODEL = os.environ["MODEL_NAME"]

def ask_streaming(prompt: str) -> str:
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            full_response += delta

    print()  # newline at the end
    return full_response

if __name__ == "__main__":
    ask_streaming("Explain what a REST API is in 2 sentences.")