from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pdf_processing import save_pdf, process_pdf
from agent import expand_query, retrieve_chunks, rerank_chunks, generate_answer

app = FastAPI()

# Allow frontend (Streamlit) to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store collection in memory (single user/session)
COLLECTION = None
PDF_TEXTS = None

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global COLLECTION, PDF_TEXTS
    file_path = await save_pdf(file, file.filename)
    collection, texts = process_pdf(file_path)
    COLLECTION = collection
    PDF_TEXTS = texts
    return {"message": "PDF processed and indexed.", "num_chunks": len(texts)}

@app.post("/chat")
def chat_with_pdf(query: str = Form(...)):
    global COLLECTION
    if COLLECTION is None:
        return {"error": "No PDF uploaded yet."}
    # Expand query
    aug_queries = expand_query(query)
    joint_queries = [query] + aug_queries
    # Retrieve
    docs = retrieve_chunks(COLLECTION, joint_queries, n_results=10)
    # Rerank
    ranked = rerank_chunks(query, docs)
    top_docs = [doc for doc, score in ranked[:5]]
    context = "\n\n".join(top_docs)
    # Generate answer
    answer = generate_answer(query, context)
    return {"answer": answer, "context": top_docs} 





