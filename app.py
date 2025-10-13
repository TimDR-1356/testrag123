import chainlit as cl
from langchain_community.chat_models import ChatLlamaCpp

# Initialiseer het model
model_path = "models/gemma-3-27b-it-UD-IQ2_XXS.gguf"  # elk compatible .gguf model
llm = ChatLlamaCpp(
    model_path=model_path,
    temperature=0.7,
    top_p=0.9,
    n_ctx=2048,
    streaming=True,  # streaming tokens naar UI
    verbose=False
)

SYSTEM_PROMPT = "Je bent een behulpzame AI-assistent."

@cl.on_chat_start
async def start():
    await cl.Message(content="Hallo! Stel een vraag.").send()

@cl.on_message
async def main(message: cl.Message):
    # Maak een leeg bericht dat we gaan updaten
    msg = await cl.Message(content="", author="Assistant").send()

    # Combineer system + user prompt in 1 string
    user_input = f"{SYSTEM_PROMPT}\n\nVraag: {message.content}"

    # Stream tokens direct naar Chainlit
    for chunk in llm.stream(user_input):
        await msg.stream_token(chunk.content)

    # Finaliseer het bericht
    await msg.update()
