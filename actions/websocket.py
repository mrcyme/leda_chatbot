import asyncio
import websockets
import json
import time


async def echo(websocket):
    while True:
        with open("research_state.json") as f:
            data = json.load(f)
        await websocket.send(json.dumps(data))
        time.sleep(2)


async def main():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
