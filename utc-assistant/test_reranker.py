from sentence_transformers import CrossEncoder
model = CrossEncoder("BAAI/bge-reranker-base", max_length=512)
pairs = [["hello", "hello world"]]
scores = model.predict(pairs)
print(type(scores), scores)
