import chainlit as cl
from langchain_community.chat_models import ChatLlamaCpp
from langdetect import detect

# --- Mock vector search functie ---
def vector_search(query, lang="en"):
    if "Python" in query:
        return ["Python is een programmeertaal...", "Je kunt functies definiëren met def ..."]
    else:
        return ["Geen specifieke info gevonden, default info in het Engels."]

# --- Beschikbare modellen ---
AVAILABLE_MODELS = {
    "gemma": "models/gemma-3-4b-it-IQ4_NL.gguf",
    "mistral": "models/mistral-7b-instruct-v0.1.Q2_K.gguf",
    "qwen": "models/Qwen2.5-VL-7B-Instruct-Q2_K_L.gguf",
}

# --- Basis system prompt ---
SYSTEM_PROMPT_BASE = (
    "Je bent een behulpzame AI-assistent. Gebruik de context van de documenten "
    "en de chatgeschiedenis om de vraag van de gebruiker te beantwoorden."
)

# --- Chatgeschiedenis ---
chat_history = []

# --- Standaard model ---
selected_model_key = list(AVAILABLE_MODELS.keys())[0]

# --- Maak globale LLM instance ---
llm = ChatLlamaCpp(
    model_path=AVAILABLE_MODELS[selected_model_key],
    temperature=0.7,
    top_p=0.9,
    n_ctx=4000,
    max_tokens=2000,
    streaming=True,
    verbose=False
)

# --- Chainlit events ---
@cl.on_chat_start
async def start():
    model_list = "\n".join([f"- {key}" + (" (actief)" if key == selected_model_key else "") for key in AVAILABLE_MODELS])
    await cl.Message(content=f"Beschikbare modellen:\n{model_list}\n\nJe kunt van model wisselen door een bericht te beginnen met @model_naam").send()
    await cl.Message(content="Hallo, stel een vraag!").send()

@cl.on_message
async def main(message: cl.Message):
    global selected_model_key, llm

    user_text = message.content.strip()
    print("User message:", user_text)

    # --- Model switch ---
    if user_text.startswith("@"):
        parts = user_text.split(maxsplit=1)
        model_mention = parts[0][1:]
        if model_mention in AVAILABLE_MODELS:
            selected_model_key = model_mention
            llm = ChatLlamaCpp(
                model_path=AVAILABLE_MODELS[selected_model_key],
                temperature=0.7,
                top_p=0.9,
                n_ctx=4000,
                max_tokens=2000,
                streaming=True,
                verbose=False
            )
            user_text = parts[1] if len(parts) > 1 else ""
            await cl.Message(content=f"Model ingesteld op: {selected_model_key}").send()
            if not user_text:
                return

    # --- Detecteer taal ---
    try:
        detected_lang = detect(user_text)
    except:
        detected_lang = "en"

    # --- Vector search ---
    context_passages = vector_search(user_text, lang=detected_lang)

    # --- Voeg user message toe aan geschiedenis ---
    chat_history.append({
        "role": "user",
        "content": user_text,
        "lang": detected_lang,
        "context": context_passages
    })

    # --- Maak system prompt met recente context ---
    recent_history = chat_history[-4:]  # laatste 2 vragen/antwoorden
    history_text = ""
    for msg in recent_history:
        ctx_text = "\n".join(msg.get("context", []))
        history_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
        if ctx_text:
            history_text += f"Context: {ctx_text}\n"

    prompt = (
        f"{SYSTEM_PROMPT_BASE}\n\n"
        f"{history_text}\n"
        f"Antwoord in dezelfde taal als de gebruiker ({detected_lang}).\n"
        f"Vraag: {user_text}"
    )

    # --- Streaming bericht ---
    msg = await cl.Message(content="", author="Assistant").send()
    for chunk in llm.stream(prompt):
        await msg.stream_token(chunk.content)

    # --- Voeg AI antwoord toe aan geschiedenis ---
    chat_history.append({
        "role": "ai",
        "content": msg.content,
        "lang": detected_lang,
        "context": context_passages
    })

    await msg.update()


#
# import chainlit as cl
# from langchain_community.chat_models import ChatLlamaCpp
# from langdetect import detect
#
# # --- Mock vector search functie ---
# def vector_search(query, lang="en"):
#     """
#     Simuleert een vector search.
#     Vervang dit door FAISS, Chroma, Pinecone etc.
#     Retourneert relevante teksten
#     """
#     if "Python" in query:
#         return ["Python is een programmeertaal...", "Je kunt functies definiëren met def ..."]
#     else:
#         return ["Geen specifieke info gevonden, default info in het Engels."]
#
# # --- Beschikbare modellen ---
# AVAILABLE_MODELS = {
#     "gemma": "models/gemma-3-4b-it-IQ4_NL.gguf",
#     "mistral": "models/mistral-7b-instruct-v0.1.Q2_K.gguf",
#     "qwen": "models/Qwen2.5-VL-7B-Instruct-Q2_K_L.gguf",
# }
#
# # --- Basis system prompt ---
# SYSTEM_PROMPT = "Je bent een behulpzame AI-assistent."
#
# # --- Chatgeschiedenis met metadata ---
# chat_history = []  # elk item: {"role": "user"/"ai", "content": "...", "lang": "...", "context": [...]}
#
# # --- Laatst geselecteerde model en LLM instance ---
# selected_model_key = list(AVAILABLE_MODELS.keys())[0]
# llm = ChatLlamaCpp(
#     model_path=AVAILABLE_MODELS[selected_model_key],
#     temperature=0.7,
#     top_p=0.9,
#     n_ctx=2048,
#     streaming=True,
#     verbose=False
# )
#
# # --- Chainlit events ---
# @cl.on_chat_start
# async def start():
#     model_list = "\n".join([f"- {key}" + (" (actief)" if key == selected_model_key else "") for key in AVAILABLE_MODELS])
#     await cl.Message(content=f"Beschikbare modellen:\n{model_list}\n\nJe kunt van model wisselen door een bericht te beginnen met @model_naam").send()
#     await cl.Message(content="Hallo, stel een vraag!").send()
#
# @cl.on_message
# async def main(message: cl.Message):
#     global selected_model_key, llm
#
#     user_text = message.content.strip()
#     print("User message:", user_text)
#
#     # --- Check voor model switch ---
#     if user_text.startswith("@"):
#         parts = user_text.split(maxsplit=1)
#         model_mention = parts[0][1:]  # haal de @ weg
#         if model_mention in AVAILABLE_MODELS:
#             selected_model_key = model_mention
#             # Maak nieuwe LLM instance met het nieuwe model
#             llm = ChatLlamaCpp(
#                 model_path=AVAILABLE_MODELS[selected_model_key],
#                 temperature=0.7,
#                 top_p=0.9,
#                 n_ctx=2048,
#                 streaming=True,
#                 verbose=False
#             )
#             # Verwijder model tag uit bericht
#             user_text = parts[1] if len(parts) > 1 else ""
#             await cl.Message(content=f"Model ingesteld op: {selected_model_key}").send()
#             if not user_text:
#                 return  # niks meer te doen als alleen model gekozen werd
#
#     # --- Detecteer taal ---
#     try:
#         detected_lang = detect(user_text)
#     except:
#         detected_lang = "en"
#
#     # --- Vector search ---
#     context_passages = vector_search(user_text, lang=detected_lang)
#     if not context_passages:
#         context_passages = vector_search(user_text, lang="en")
#
#     # --- Voeg user message toe aan geschiedenis ---
#     chat_history.append({
#         "role": "user",
#         "content": user_text,
#         "lang": detected_lang,
#         "context": context_passages
#     })
#
#     # --- Bouw prompt met korte system prompt + context + recente geschiedenis ---
#     recent_history = chat_history[-4:]  # laatste 2 vragen + antwoorden
#     history_text = ""
#     for msg in recent_history:
#         ctx_text = "\n".join(msg.get("context", []))
#         history_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
#         if ctx_text:
#             history_text += f"Context: {ctx_text}\n"
#
#     prompt = (
#         f"{SYSTEM_PROMPT}\n\n"
#         f"{history_text}\n"
#         f"Antwoord in dezelfde taal als de gebruiker ({detected_lang}).\n"
#         f"Vraag: {user_text}"
#     )
#
#     # --- Maak leeg bericht voor streaming ---
#     msg = await cl.Message(content="", author="Assistant").send()
#
#     # --- Stream tokens naar Chainlit ---
#     for chunk in llm.stream(prompt):
#         await msg.stream_token(chunk.content)
#
#     # --- Voeg AI antwoord toe aan geschiedenis ---
#     chat_history.append({
#         "role": "ai",
#         "content": msg.content,
#         "lang": detected_lang,
#         "context": context_passages
#     })
#
#     # --- Finaliseer ---
#     await msg.update()
