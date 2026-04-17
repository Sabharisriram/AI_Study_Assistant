from groq import Groq
import os
from dotenv import load_dotenv
from app.services.rag_service import query_pdf
from app.services.web_search_service import search_web
from app.services.memory_service import get_user_memory, update_user_memory

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def summarize_history(text: str) -> str:
    if len(text) < 600:
        return text
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"Summarize in 3 lines:\n{text[:1200]}"}],
        max_tokens=120
    )
    return res.choices[0].message.content.strip()


def execute_tool(action: str, action_input: str, user_id: str) -> dict:
    if action == "RAG":
        context, sources = query_pdf(action_input, user_id=user_id)
        if not context:
            return {"data": "NO_DOCUMENT_CONTENT", "source": [], "empty": True}
        return {"data": context, "source": sources, "empty": False}

    elif action == "WEB":
        try:
            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f"Convert into a concise web search query (max 10 words):\n{action_input[:400]}"}],
                max_tokens=50
            )
            refined = res.choices[0].message.content.strip()
        except Exception:
            refined = action_input

        results   = search_web(refined)
        formatted = "".join(
            f"Title: {r.get('title','')}\nSnippet: {r.get('snippet','')}\n\n"
            for r in results[:5]
        )
        return {"data": formatted[:2000], "source": ["Web"], "empty": not formatted.strip()}

    return {"data": "Invalid action", "source": [], "empty": True}


def agent(user_id: str, question: str) -> str:
    print(f"\n{'='*50}\nUSER: {user_id}\nQUESTION: {question}\n{'='*50}")

    memory       = get_user_memory(user_id, question)
    history_text = "\n".join(memory)[:600]
    summary      = summarize_history(history_text) if history_text else "No previous context."

    steps       = []
    all_sources = set()

    # Step 1: Always RAG first
    print("\n[Step 1] Forcing RAG...")
    rag_result      = execute_tool("RAG", question, user_id)
    rag_had_content = not rag_result["empty"]

    if rag_had_content:
        all_sources.update(rag_result["source"])
    steps.append({"action": "RAG", "observation": rag_result["data"]})

    # Step 2: WEB fallback only if RAG was empty
    if not rag_had_content:
        print("\n[Step 2] RAG empty — asking LLM for WEB/NONE decision...")
        try:
            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f"""User asked: "{question}"
Uploaded document search returned nothing.
Decide: WEB (search internet) or NONE (answer from knowledge)?

Thought: <reasoning>
Action: WEB or NONE
Action Input: <query if WEB>"""}],
                max_tokens=100
            )
            output       = res.choices[0].message.content.strip()
            action       = "NONE"
            action_input = question

            for line in output.split("\n"):
                line = line.strip()
                if line.lower().startswith("action:"):
                    action = "WEB" if "WEB" in line.upper() else "NONE"
                elif line.lower().startswith("action input:"):
                    v = line.split(":", 1)[1].strip()
                    if v:
                        action_input = v

            if action == "WEB":
                web_result = execute_tool("WEB", action_input, user_id)
                if not web_result["empty"]:
                    all_sources.update(web_result["source"])
                steps.append({"action": "WEB", "observation": web_result["data"]})

        except Exception as e:
            print(f"[Step 2] Failed: {e}")

    full_context = "\n\n".join(
        f"[{s['action']} Result]\n{s['observation']}"
        for s in steps
        if s["observation"] != "NO_DOCUMENT_CONTENT"
    )

    final_prompt = f"""You are an AI study assistant. Answer using ONLY the context below.

RULES:
- If context has the answer: give a clear structured answer
- If context is empty: say "I couldn't find this in the uploaded documents."
- No hallucination
- Format: 3 to 6 bullet points starting with "• "

Conversation history: {summary}
Question: {question}
Context:
{full_context[:3000] if full_context else "No context retrieved."}

Answer:"""

    final  = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": final_prompt}],
        max_tokens=600
    )
    answer = final.choices[0].message.content.strip()

    source_text  = "\n".join(f"- {s}" for s in all_sources)
    final_output = f"{answer}\n\n**Sources:**\n{source_text if source_text else '- General Knowledge'}"

    update_user_memory(user_id, "user",      question)
    update_user_memory(user_id, "assistant", answer)

    return final_output