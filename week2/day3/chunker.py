from dataclasses import dataclass
from openai import OpenAI


@dataclass
class Chunk:
    id: str
    text: str
    document_id: str
    page: int | None
    embedding: list[float]


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate a real embedding using the OpenAI client."""
    client = OpenAI()  # Automatically loads OPENAI_API_KEY from the environment
    response = client.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding


text_content = "Customers can request a refund within 30 days."
real_embedding = generate_embedding(text_content)

chunk = Chunk(
    id="doc1_chunk_001",
    text="Customers can request a refund within 30 days.",
    text=text_content,
    document_id="refund_policy",
    page=3,
    embedding=[]
    embedding=real_embedding
)

print(f"Generated embedding with dimensionality: {len(chunk.embedding)}")
print(f"Sample dimensions: {chunk.embedding[:5]}...")