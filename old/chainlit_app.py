import chainlit as cl
from langchain_community.chat_models import ChatLlamaCpp

from detected_language import detected_language
from vector_search import vector_search

AVAILABLE_MODELS = {
    "gemma": "models/gemma-3-4b-it-IQ4_NL.gguf",
    "mistral": "models/mistral-7b-instruct-v0.1.Q2_K.gguf",
    "qwen": "models/Qwen2.5-VL-7B-Instruct-Q2_K_L.gguf",
}

selected_model_key = list(AVAILABLE_MODELS.keys())[0]

llm = ChatLlamaCpp(
    model_path=selected_model_key,
    temperature=0.7,
    top_p=0.9,
    n_ctx=1000,
    max_tokens=2000,
    streaming=True,
    verbose=False
)

embeddings_model = ""

SYSTEM_PROMPT_BASE = "Je bent een behulpzame AI-assistent."
chat_history = []

async def detect_model_change(text_input: str):
    global selected_model_key, llm
    if text_input.startswith("#"):
        parts = text_input.split(maxsplit=1)
        model_mention = parts[0][1:]
        if model_mention in AVAILABLE_MODELS:
            selected_model_key = model_mention
            llm = ChatLlamaCpp(
                model_path=AVAILABLE_MODELS[selected_model_key],
                temperature=0.7,
                top_p=0.9,
                n_ctx=2048,
                streaming=True,
                verbose=False
            )
            text_input = parts[1] if len(parts) > 1 else ""
            await cl.Message(content=f"Model ingesteld op: {selected_model_key}").send()
    return text_input


@cl.on_chat_start
async def start():
    global selected_model_key
    model_list = "\n".join([f"- {key}" + (" (actief)" if key == selected_model_key else "") for key in AVAILABLE_MODELS])
    await cl.Message(content=f"Beschikbare modellen:\n{model_list}\n\nJe kunt van model wisselen door een bericht te beginnen met #model_naam").send()
    await cl.Message(content="Hallo, stel een vraag!").send()

@cl.on_message
async def main(message: cl.Message):
    global llm
    msg = await cl.Message(content="").send()

    text_input = message.content.strip()
    question = await detect_model_change(text_input)

    language = await detected_language(msg, question)

    english_question, question_type = await detected_question_type(llm, msg, chat_history, question)

    embeddings = await create_embeddings(embeddings_model, msg, english_question)

    context = await vector_search(msg, embeddings)

    await model_thinking(msg, question, language, english_question, question_type, context)

async def model_thinking(msg: cl.Message, question, language, english_question, question_type, context):
    msg.content = "Even geduld, het model denkt na..."
    await msg.update()

    response = ""
    message_is_empty = False
    for chunk in llm.stream(prompt):
        token = chunk.content
        response += token
        if not message_is_empty:
            message_is_empty = True
            msg.content = " "
            await msg.update()

        await msg.stream_token(token)

    # --- Finaliseer bericht ---
    await msg.update()
    print("AI response:", response)








# import time
#
# import chainlit as cl
# import asyncio
# from langchain_community.chat_models import ChatLlamaCpp
# from langdetect import detect
#
# # from loading_animation import start_thinking_animation, start_delayed_animation
# from vector_search import vector_search
#
# animation_state = {"active": False, "text": ""}
#
# async def start_thinking_animation(msg: cl.Message):
#     """Animatie loopt continu zolang active True is."""
#     frames = [".", "..", "...", "....", "...", "..", "."]
#     progress = 0
#     try:
#         while True:
#             if animation_state["active"]:
#                 frame = frames[progress % len(frames)]
#                 msg.content = f"{animation_state['text']}{frame}"
#                 await msg.update()
#                 progress += 1
#             await asyncio.sleep(0.4)
#     except asyncio.CancelledError:
#         msg.content = ""  # maak schoon als de animatie stopt
#         await msg.update()
#         raise
#
# def set_animation(text: str, active: bool = True):
#     animation_state["text"] = text
#     animation_state["active"] = active
#
#
# # --- Beschikbare modellen ---
# AVAILABLE_MODELS = {
#     "gemma": "models/gemma-3-4b-it-IQ4_NL.gguf",
#     "mistral": "models/mistral-7b-instruct-v0.1.Q2_K.gguf",
#     "qwen": "models/Qwen2.5-VL-7B-Instruct-Q2_K_L.gguf",
# }
#
# # --- Basis system prompt ---
# SYSTEM_PROMPT_BASE = (
#     "Je bent een behulpzame AI-assistent. Gebruik de context van de documenten "
#     "en de chatgeschiedenis om de vraag van de gebruiker te beantwoorden."
# )
#
# # --- Chatgeschiedenis ---
# chat_history = []
#
# # --- Standaard model ---
# selected_model_key = list(AVAILABLE_MODELS.keys())[0]
#
# # --- Maak globale LLM instance ---
# llm = ChatLlamaCpp(
#     model_path=AVAILABLE_MODELS[selected_model_key],
#     temperature=0.7,
#     top_p=0.9,
#     n_ctx=100000,
#     max_tokens=2000,
#     streaming=True,
#     verbose=False
# )
#
# # === Chainlit event handlers ===
# @cl.on_chat_start
# async def start():
#     model_list = "\n".join(
#         [f"- {key}" + (" (actief)" if key == selected_model_key else "") for key in AVAILABLE_MODELS]
#     )
#     await cl.Message(
#         content=f"Beschikbare modellen:\n{model_list}\n\nJe kunt van model wisselen door een bericht te beginnen met #model_naam"
#     ).send()
#     await cl.Message(content="Hallo, stel een vraag!").send()
#
#
# @cl.on_message
# async def main(message: cl.Message):
#     user_text = message.content.strip()
#
#     try:
#         detected_lang = detect(user_text)
#     except:
#         detected_lang = "en"
#
#     # --- Bericht aanmaken ---
#     msg = await cl.Message(content="").send()
#
#     # --- Start 1 animatie-task ---
#     animation_task = asyncio.create_task(start_thinking_animation(msg))
#
#     set_animation("🔍 Bezig met zoeken naar relevante informatie")
#     context_passages = await vector_search(user_text, lang=detected_lang)
#
#     animation_task.cancel()
#
#     animation_task = asyncio.create_task(start_thinking_animation(msg))
#     set_animation("🤔 Even geduld, het model denkt na")
#
#
#
#     # --- Prompt voor model ---
#     prompt = (
#         f"{SYSTEM_PROMPT_BASE}\n\n"
#         f"Antwoord in dezelfde taal als de gebruiker ({detected_lang}).\n"
#         f"Context: {context_passages}\n"
#         f"Vraag: {user_text}"
#     )
#
#     response = ""
#     for chunk in llm.stream(prompt):
#         token = chunk.content
#         response += token
#         await msg.stream_token(token)
#
#     # Finaliseer het bericht
#     await msg.update()
#
#
#     print("AI response:", response)












# import chainlit as cl
# from langchain_community.chat_models import ChatLlamaCpp
# from langdetect import detect
#
# # --- Mock vector search functie ---
# def vector_search(query, lang="en"):
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
# SYSTEM_PROMPT_BASE = (
#     "Je bent een behulpzame AI-assistent. Gebruik de context van de documenten "
#     "en de chatgeschiedenis om de vraag van de gebruiker te beantwoorden."
# )
#
# # --- Chatgeschiedenis ---
# chat_history = []
#
# # --- Standaard model ---
# selected_model_key = list(AVAILABLE_MODELS.keys())[0]
#
# # --- Maak globale LLM instance ---
# llm = ChatLlamaCpp(
#     model_path=AVAILABLE_MODELS[selected_model_key],
#     temperature=0.7,
#     top_p=0.9,
#     n_ctx=4000,
#     max_tokens=2000,
#     streaming=True,
#     verbose=False
# )
#
# # --- Chainlit events ---
# @cl.on_chat_start
# async def start():
#     model_list = "\n".join([f"- {key}" + (" (actief)" if key == selected_model_key else "") for key in AVAILABLE_MODELS])
#     await cl.Message(content=f"Beschikbare modellen:\n{model_list}\n\nJe kunt van model wisselen door een bericht te beginnen met #model_naam").send()
#     await cl.Message(content="Hallo, stel een vraag!").send()
#
# @cl.on_message
# async def main(message: cl.Message):
#     global selected_model_key, llm
#
#     user_text = message.content.strip()
#     print("User message:", user_text)
#
#     # --- Model switch ---
#     if user_text.startswith("#"):
#         parts = user_text.split(maxsplit=1)
#         model_mention = parts[0][1:]
#         if model_mention in AVAILABLE_MODELS:
#             selected_model_key = model_mention
#             llm = ChatLlamaCpp(
#                 model_path=AVAILABLE_MODELS[selected_model_key],
#                 temperature=0.7,
#                 top_p=0.9,
#                 n_ctx=4000,
#                 max_tokens=2000,
#                 streaming=True,
#                 verbose=False
#             )
#             user_text = parts[1] if len(parts) > 1 else ""
#             await cl.Message(content=f"Model ingesteld op: {selected_model_key}").send()
#             if not user_text:
#                 return
#
#     # --- Detecteer taal ---
#     try:
#         detected_lang = detect(user_text)
#     except:
#         detected_lang = "en"
#
#     # --- Vector search ---
#     context_passages = vector_search(user_text, lang=detected_lang)
#
#     # --- Voeg user message toe aan geschiedenis ---
#     chat_history.append({
#         "role": "user",
#         "content": user_text,
#         "lang": detected_lang,
#         "context": context_passages
#     })
#
#     # --- Maak system prompt met recente context ---
#     recent_history = chat_history[-4:]  # laatste 2 vragen/antwoorden
#     history_text = ""
#     for msg in recent_history:
#         ctx_text = "\n".join(msg.get("context", []))
#         history_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
#         if ctx_text:
#             history_text += f"Context: {ctx_text}\n"
#
#     prompt = (
#         f"{SYSTEM_PROMPT_BASE}\n\n"
#         f"{history_text}\n"
#         f"Antwoord in dezelfde taal als de gebruiker ({detected_lang}).\n"
#         f"Vraag: {user_text}"
#     )
#
#     def generate_response(prompt):
#         full_text = ""
#         for chunk in llm.stream(prompt):
#             full_text += chunk.content
#         return full_text
#
#     # --- Streaming bericht ---
#     msg = await cl.Message(content="", author=selected_model_key).send()
#
#     # Run sync functie async in aparte thread
#     ai_response = await cl.make_async(generate_response)(prompt)
#
#     # Stuur response token per token naar frontend
#     for token in ai_response:
#         await msg.stream_token(token)
#
#     # --- Voeg AI antwoord toe aan geschiedenis ---
#     chat_history.append({
#         "role": "ai",
#         "content": ai_response,
#         "lang": detected_lang,
#         "context": context_passages
#     })
#
#     await msg.update()




    # # --- Streaming bericht ---
    # msg = await cl.Message(content="", author="Assistant").send()
    # for chunk in llm.stream(prompt):
    #     await msg.stream_token(chunk.content)
    #
    # # --- Voeg AI antwoord toe aan geschiedenis ---
    # chat_history.append({
    #     "role": "ai",
    #     "content": msg.content,
    #     "lang": detected_lang,
    #     "context": context_passages
    # })
    #
    # await msg.update()


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
