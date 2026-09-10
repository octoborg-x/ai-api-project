import numpy as np

documents = [
    {
        "text": "Customers can request a refund within 30 days.",
        "embedding": np.array([0.95, 0.10, 0.05]),
    },
    {
        "text": "You can reset your password from account settings.",
        "embedding": np.array([0.05, 0.95, 0.10]),
    },
    {
        "text": "Shipping usually takes between 3 and 5 business days.",
        "embedding": np.array([0.10, 0.05, 0.95]),
    },
]


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


query_embedding = np.array([0.90, 0.15, 0.05])


results = []

for document in documents:
    score = cosine_similarity(query_embedding, document["embedding"])

    results.append(
        {
            "text": document["text"],
            "score": score,
        }
    )


results.sort(key=lambda x: x["score"], reverse=True)


for result in results:
    print(f"{result['score']:.3f} " f"- {result['text']}")
