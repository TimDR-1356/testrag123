import asyncio
import chainlit as cl

async def start_thinking_animation(msg: cl.Message, text: str, delay: float = 0):
    print("start_thinking_animation")
    frames = [".", "..", "...", "....", "...", "..", "."]
    progress = 0

    try:
        if delay > 0:
            await asyncio.sleep(delay)

        while True:
            frame = frames[progress % len(frames)]
            msg.content = f"{text}{frame}"
            await msg.update()
            progress += 1
            await asyncio.sleep(0.4)
    except asyncio.CancelledError:
        raise