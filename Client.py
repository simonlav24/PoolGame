

import json
import asyncio
import websockets as ws
import uuid
from StateMachine import Player
from Models import *

class Client:
    def __init__(self) -> None:
        self.id = str(uuid.uuid1())
        self.client = None
        self.event_queue = asyncio.Queue()
    
    async def start(self, host, port):
        await self.connect(host, port)

        message = Message(id=str(self.id), action=Action.JOIN)
        await self.send(message)

    async def connect(self, host, port):
        self.client = await ws.connect(f'ws://{host}:{port}')

    async def disconnect(self):
        self.client.close()

    async def send(self, message: Message):
        print('sending message')
        await self.client.send(message.model_dump_json())

    async def listen(self) -> Message:
        message = await self.client.recv()

        print('received message from server')
        message_type = json.loads(message)['action']
        action = Action(message_type)
        message_model = ACTION_TO_MESSAGE[action]

        print(f'[client] {message_model}')
        print(f'[client]', message_model.model_validate_json(message))
        return message_model.model_validate_json(message)

async def main():
    host = 'localhost'
    port = 8000

    client = Client()
    await client.start(host, port)
    await client.listen()

if __name__ == '__main__':
    asyncio.run(main())