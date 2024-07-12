

import json
import asyncio
import websockets as ws
import uuid
from StateMachine import Player

class Client:
    def __init__(self) -> None:
        self.id = uuid.uuid1()
        self.client = None
        self.event_queue = asyncio.Queue()
    
    async def start(self, host, port):
        await self.connect(host, port)

        message = {
            'id': str(self.id),
            'action': 'enter game',
            'message': 'yo i want to pool'
        }
        await self.send(message)

        

        # async with ws.connect(f'ws://{host}:{port}') as client:
        #     self.client = client
        #     await self.send_hello()
        # self.client = None

    async def connect(self, host, port):
        self.client = await ws.connect(f'ws://{host}:{port}')

    async def disconnect(self):
        self.client.close()

    async def send(self, message):
        print('sending message')
        await self.client.send(json.dumps(message))

    async def listen(self):
        print('[client] listening')
        response = await self.client.recv()
        print(f'[client] {response}')
        return response

    async def send_hello(self):
        message = {
            'id': '123',
            'message': f'yo sup. me name in {self.id}'
        }
        await self.client.send(json.dumps(message))

async def main():
    host = 'localhost'
    port = 8000

    client = Client()
    await client.start(host, port)
    await client.listen()

if __name__ == '__main__':
    asyncio.run(main())