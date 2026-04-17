from groq import Groq
import os
from dotenv import load_dotenv
from app.services.rag_service import query_pdf

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ MEMORY STORAGE
user_memory = {}
MAX_HISTORY = 10

def ask_llm(user_id: str, question: str):
    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": "You are a helpful AI study assistant."}
        ]

    # 🔥 Get context from PDF
    context = query_pdf(question)

    # ✅ Improved Prompt (VERY IMPORTANT)
    full_question = f"""
You are a helpful AI assistant.

Use ONLY the context below to answer the question.
If the answer is not in the context, say "I don't know".

Give a clear and concise answer.

Context:
{context}

Question:
{question}
"""

    user_memory[user_id].append({"role": "user", "content": full_question})

    # ✅ Limit memory size
    user_memory[user_id] = user_memory[user_id][-MAX_HISTORY:]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=user_memory[user_id]
    )

    answer = response.choices[0].message.content

    user_memory[user_id].append({"role": "assistant", "content": answer})

    return answer