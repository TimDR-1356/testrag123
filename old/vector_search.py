import asyncio
import chainlit as cl
from loading_animation import start_thinking_animation

async def vector_search(msg: cl.Message, embeddings):
    animation_task = asyncio.create_task(start_thinking_animation(msg, "Bezig met zoeken naar relevante informatie", 2))
    await asyncio.sleep(5)

    animation_task.cancel()
    return ""