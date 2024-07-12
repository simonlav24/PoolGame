

import json
import asyncio
import websockets as ws
from typing import Set, Tuple, Dict
from StateMachine import Player

class Server:
    def __init__(self) -> None:
        self.clients: Set[ws.WebSocketServerProtocol] = set()
        self.event_queue: asyncio.Queue[Tuple[ws.WebSocketServerProtocol, Dict]] = asyncio.Queue()

    async def start(self, host: str, port: int):
        ''' start server '''
        print('why are you running?')
        async with ws.serve(self.handle_connection, host, port):
            # await asyncio.Future()
            try:
                while True:
                    sender, event = await self.event_queue.get()

                    message = await self.handle_event(sender, event)
                    
                    # print('broadcasting message')
                    # await self.broadcast(sender, event)
            except KeyboardInterrupt:
                pass

    async def handle_event(self, sender: ws.WebSocketServerProtocol, event: str):
        event = json.loads(event)
        action = event['action']
        respone = None

        print(f'handling event action: {action}')

        if action == 'enter game':
            if len(self.clients) == 1:
                respone = {
                    'action': 'player spot',
                    'message': '1'
                }
            else:
                respone = {
                    'action': 'player spot',
                    'message': '2'
                }
            await sender.send(json.dumps(respone))
            if len(self.clients) == 2:
                game_start_message = {
                    'action': 'game start'
                }
                await self.broadcast(None, json.dumps(game_start_message))
        
        return respone


    async def handle_connection(self, client: ws.WebSocketServerProtocol):
        self.clients.add(client)
        print(f'new client, {client}')

        try:
            async for message in client:
                print(f'server got message ')
                await self.add_event((client, message))
            #     data = json.loads(message)
            #     await self.handle_message(client, data)
            ...

        except ws.ConnectionClosedError:
            pass

        finally:
            self.clients.remove(client)

    async def handle_message(self, client, message):
        print(message)
    
    async def add_event(self, event):
        await self.event_queue.put(event)
    
    async def broadcast(self, client_sender, message):
        
        for client in self.clients:
            if client == client_sender:
                continue
            await client.send(message)


if __name__ == '__main__':
    host = 'localhost'
    port = 8000

    server = Server()
    asyncio.run(server.start(host, port))