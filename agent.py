import os
import google.generativeai as genai
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from sentence_transformers import CrossEncoder
from helper_utils import word_wrap

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
GEMINI_MODEL_NAME = "models/gemini-2.0-pro-exp"
gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

embedding_function = SentenceTransformerEmbeddingFunction()
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def expand_query(query):
    prompt = (
        "You are a knowledgeable financial research assistant. "
        "Your users are inquiring about an annual report. "
        "For the given question, propose up to five related questions to assist them in finding the information they need. "
        "Provide concise, single-topic questions (without compounding sentences) that cover various aspects of the topic. "
        "Ensure each question is complete and directly related to the original inquiry. "
        "List each question on a separate line without numbering."
    )
    full_prompt = f"{prompt}\n\nUser question: {query}\n"
    response = gemini_model.generate_content(full_prompt)
    content = response.text.strip().split("\n")
    content = [line for line in content if line.strip()]
    return content

def retrieve_chunks(collection, queries, n_results=3):
    results = collection.query(query_texts=queries, n_results=n_results, include=["documents"])
    # flatten and deduplicate
    docs = set()
    for docs_list in results["documents"]:
        for doc in docs_list:
            docs.add(doc)
    return list(docs)

def rerank_chunks(query, docs):
    pairs = [[query, doc] for doc in docs]
    scores = cross_encoder.predict(pairs)
    # sort by score descending
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return ranked

def generate_answer(query, context):
    prompt = f"""
    You are a knowledgeable financial research assistant.\n\nBased on the following context, answer the query as if you are providing a helpful, concise, and accurate response:\n\n{context}\n\nAnswer the query: '{query}'
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip() 