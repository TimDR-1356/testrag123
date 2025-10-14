import chainlit as cl
from langdetect import detect

async def detected_language(msg: cl.Message, user_text):
    msg.content = "Detecting language..."
    await msg.update()

    if not user_text or len(user_text.split()) < 3:
        # Tekst te kort
        return "en"

    try:
        return detect(user_text)
    except:
        return "en"
