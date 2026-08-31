import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

MODEL = os.environ.get("MODEL_NAME", "cohere/north-mini-code:free")

def ask(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
    # print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    print(ask("Explain what a REST API is in 2 sentences."))