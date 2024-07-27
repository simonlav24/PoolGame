

import json
import asyncio
import websockets as ws
import uuid
from StateMachine import Player
from Models import *

SENTINEL = None

class Client:
    def __init__(self) -> None:
        self.id = str(uuid.uuid1())
        self.client = None
        self.event_queue = asyncio.Queue()
        self.loop_task = None
    
    async def start(self, host, port):
        await self.connect(host, port)

        self.loop_task = asyncio.create_task(self.loop())

        message = Message(id=str(self.id), action=Action.JOIN)
        await self.send(message)

    async def connect(self, host, port):
        self.client = await ws.connect(f'ws://{host}:{port}')

    async def disconnect(self):
        await self.event_queue.put(SENTINEL)
        await asyncio.gather(self.loop_task)
        self.client.close()

    async def send(self, message: Message):
        print('sending message')
        await self.client.send(message.model_dump_json())

    async def listen(self, timeout: float=None) -> Message:
        try:
            print('event_queue get')
            get_await = self.event_queue.get()
            message = await asyncio.wait_for(get_await, timeout)

        except asyncio.TimeoutError:
            pass

        return message

    async def loop(self) -> None:

        async for message in self.client:
            print('in loop 1')
            # message = await self.client.recv()
            print('in loop 2')

            # if message == SENTINEL:
            #     print('received sentinel')
            #     break

            print('received message from server')
            message_type = json.loads(message)['action']
            action = Action(message_type)
            message_model = ACTION_TO_MESSAGE[action]

            print(f'[client] {message_model}')
            print(f'[client]', message_model.model_validate_json(message))

            # todo: if sentinel, break

            print('before put_nowait')
            await self.event_queue.put_nowait(message_model.model_validate_json(message))
            print('finished one loop')

async def main():
    host = 'localhost'
    port = 8000

    client = Client()
    await client.start(host, port)
    await client.listen()

if __name__ == '__main__':
    asyncio.run(main())