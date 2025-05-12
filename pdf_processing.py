import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from helper_utils import extract_text_from_pdf

UPLOAD_DIR = "uploads"

embedding_function = SentenceTransformerEmbeddingFunction()


async def save_pdf(file, filename):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


def process_pdf(file_path, collection_name="pdf_chunks"):
    # Extract text
    text = extract_text_from_pdf(file_path)
    # Split into chunks
    character_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""], chunk_size=1000, chunk_overlap=0
    )
    character_split_texts = character_splitter.split_text(text)
    token_splitter = SentenceTransformersTokenTextSplitter(
        chunk_overlap=0, tokens_per_chunk=256
    )
    token_split_texts = []
    for t in character_split_texts:
        token_split_texts += token_splitter.split_text(t)
    # Store in ChromaDB
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name=collection_name, embedding_function=embedding_function
    )
    ids = [str(i) for i in range(len(token_split_texts))]
    collection.add(ids=ids, documents=token_split_texts)
    return collection, token_split_texts 