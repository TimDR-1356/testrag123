import chainlit as cl
from langchain_community.chat_models import ChatLlamaCpp
from langchain.prompts import ChatPromptTemplate
from langdetect import detect
import json

# https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/tree/main
# https://huggingface.co/DavidAU/Mistral-Small-3.1-24B-Instruct-2503-MAX-NEO-Imatrix-GGUF/tree/main

# Model path
model_path = "models/Mistral-Small-3.1-24B-Instruct-2503-MAX-NEO-D_AU-IQ2_XS-imat.gguf"

# Initialize model
llm = ChatLlamaCpp(
    model_path=model_path,
    temperature=0.7,
    top_p=0.9,
    n_ctx=4096,
    streaming=True,
    verbose=False
)

# 🔹 Example context file (you could load this from a real .json file)
context_data = [
    {
        "id": 1,
        "fileName": "user_manual.txt",
        "text": "Hermiron is a cloud platform that allows customers to deploy PostgreSQL databases.",
        "textTranslated": "Hermiron is een cloudplatform waarmee klanten PostgreSQL-databases kunnen implementeren."
    },
    {
        "id": 2,
        "fileName": "release_notes.txt",
        "text": "Version 2.1 introduces MongoDB support and improved user authentication.",
        "textTranslated": "Versie 2.1 introduceert ondersteuning voor MongoDB en verbeterde gebruikersauthenticatie."
    }
]

# 🔹 Base system instructions
BASE_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Always respond in the same language as the user. "
    "You have access to a JSON context with information. "
    "Instructions: "
    "1. If any part of the context is relevant to the user's question, use it to answer and clearly mention the fileName. "
    "2. If none of the context is relevant, do NOT use the warning preemptively. Instead, start your answer with a short warning in the user's language like: "
    "'There is no specific information available in the context about this topic, but I can provide an answer based on my own knowledge.' "
    "3. Always answer as completely and helpfully as possible, using context if available and your own knowledge if not."
)


# Create a ChatPromptTemplate
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("user", "{user_input}")
])

@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! Ask me something — I can also use my context if relevant.").send()

@cl.on_message
async def main(message: cl.Message):
    # Detect user language
    try:
        user_language = detect(message.content)
    except Exception:
        user_language = "en"

    # 🔹 Build dynamic system prompt
    system_prompt = (
        f"{BASE_SYSTEM_PROMPT} "
        f"The user's language is '{user_language}'. "
        f"The JSON context is as follows:\n\n{json.dumps(context_data, indent=2)}"
    )

    # Combine messages
    prompt = prompt_template.format_messages(
        system_prompt=system_prompt,
        user_input=message.content
    )

    # Stream model response
    msg = await cl.Message(content="", author="Assistant").send()
    for chunk in llm.stream(prompt):
        if chunk.content:
            await msg.stream_token(chunk.content)
    await msg.update()
