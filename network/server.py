from typing import Optional, Set, Tuple, Dict, Any
import asyncio
import json
import random
import websockets as ws
from network.events import EventType, Event, Status, PlayerType, EventFactory
from Definitions import PlayerSpot

class GameServer:
    def __init__(self):
        self.clients: Set[ws.WebSocketServerProtocol] = set()
        self.event_queue: asyncio.Queue[Tuple[ws.WebSocketServerProtocol, Event]] = asyncio.Queue()
        self.seed: int = random.randint(0, 1_000_000)
        self.num_players: int = 0
        self.listener_task: asyncio.Task = None

    async def register(self, websocket):
        self.clients.add(websocket)

    async def unregister(self, websocket):
        self.clients.remove(websocket)
    
    def create_response(self, event_type: EventType, payload_data: Optional[Dict[str, Any]]=None) -> Event:
        if not payload_data:
            payload_data = {}

        payload_class = EventFactory.get_payload_model(event_type)
        payload = payload_class(**payload_data)
        event = EventFactory.create_event(event_type, payload, sender_id='server')
        return event

    async def handle_event(self, client: ws.WebSocketServerProtocol, event: Event) -> Optional[Event]:
        response = None
        
        if event.event_type == EventType.JOIN:
            print(f"Handling join event for {event.payload.player_id}")
            if self.num_players >= 2:
                response = self.create_status_response(Status.FAILURE, reason='Server is full', original_event=event)
            else:
                self.num_players += 1
                payload = {
                    'player_id': event.payload.player_id,
                    'player_type': PlayerType.PLAYER,
                    'spot': PlayerSpot.PLAYER1 if self.num_players == 1 else PlayerSpot.PLAYER2,
                }
                response = self.create_response(EventType.JOIN_RESPONSE, payload_data=payload)

            if self.num_players == 2:
                await self.send_event(client, response)
                response = None
                payload = {
                    'seed': self.seed,
                }
                start_game_event = self.create_response(EventType.START_GAME, payload_data=payload)
                await self.broadcast_event(start_game_event)
        elif event.event_type == EventType.LEAVE:
            print(f"Handling leave event for {event.payload.player_id}")
            if self.num_players > 0:
                print(f"Player left: {event.payload.player_id}")
                self.num_players -= 1
                payload = {'status': Status.SUCCESS}
            else:
                payload = {
                    'status': Status.SUCCESS,
                    'reason': 'No players to leave'
                }
            
            response = self.create_response(EventType.STATUS_RESPONSE, payload_data=payload)
        else:
            print(f"Broadcasting event: {event}")
            await self.broadcast_event(event, exclude=event.sender_id)

        return response

    async def event_listener(self):
        while True:
            client, event = await self.event_queue.get()
            response = await self.handle_event(client, event)
            if response:
                await self.send_event(client, response)

    async def send_event(self, client: ws.WebSocketServerProtocol, event: Event) -> None:
        
        if client in self.clients:
            print(f'send_event: {event=}')
            await client.send(event.model_dump_json())
        else:
            print(f"Client {client} is not connected")

    async def broadcast_event(self, event: Event, exclude: Optional[ws.WebSocketServerProtocol] = None) -> None:
        for client in self.clients:
            if exclude and client == exclude:
                continue
            await self.send_event(client, event)

    async def handler(self, websocket: ws.WebSocketServerProtocol, path: str):
        await self.register(websocket)
        try:
            async for message in websocket:
                event_data = json.loads(message)
                print(f"Received event: {event_data}")
                event = EventFactory.from_dict(event_data)
                await self.event_queue.put((websocket, event))
                
        finally:
            await self.unregister(websocket)

    def shutdown(self):
        self.listener_task.cancel()

    def run(self):
        loop = asyncio.get_event_loop()
        self.listener_task = loop.create_task(self.event_listener())
        start_server = ws.serve(self.handler, "localhost", 6789)
        loop.run_until_complete(start_server)
        loop.run_forever()

def run_server():
    print('why are you running?')
    server = GameServer()

    try:
        server.run()
    except KeyboardInterrupt:
        server.shutdown()
        print("Server stopped")

if __name__ == "__main__":
    run_server()