

import json
import asyncio
import websockets as ws
from typing import Set, Tuple, Dict
from Models import *
from random import randint

class Server:
    def __init__(self) -> None:
        self.clients: Set[ws.WebSocketServerProtocol] = set()
        self.event_queue: asyncio.Queue[Tuple[ws.WebSocketServerProtocol, Message]] = asyncio.Queue()

    async def start(self, host: str, port: int):
        ''' start server '''
        print('why are you running?')
        async with ws.serve(self.handle_connection, host, port, open_timeout=10000000000, close_timeout=10000000000):
            # await asyncio.Future()
            try:
                while True:
                    sender, event = await self.event_queue.get()
                    message = await self.handle_event(sender, event)

            except KeyboardInterrupt:
                pass

    async def handle_event(self, sender: ws.WebSocketServerProtocol, event: Message):
        respone = None

        print(f'handling event action: {event.action}')

        if event.action == Action.JOIN:
            print('in join action')
            if len(self.clients) == 1:
                response = PlayerSpotMessage(message=Player.PLAYER_1, player_type=Player_Type.HUMAN)
            else:
                response = PlayerSpotMessage(message=Player.PLAYER_2, player_type=Player_Type.HUMAN)
            print('preparing to send', response.model_dump_json())
            await sender.send(response.model_dump_json())
            if len(self.clients) == 2:
                print('preparing to send PLAY')
                response = Message(message=randint(0, 10000), action=Action.GAME_START)
                await self.broadcast(None, response.model_dump_json())
                print('sent')
        
        elif event.action == Action.STRIKE:
            print('Server received STRIKE action')
            await self.broadcast(sender, event.model_dump_json())
        
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
    
    async def add_event(self, event: Tuple[ws.WebSocketServerProtocol, str]):
        client, message = event
        message_type = json.loads(message)['action']
        action = Action(message_type)
        message_model = ACTION_TO_MESSAGE[action]
        event = (client, message_model.model_validate_json(message))

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