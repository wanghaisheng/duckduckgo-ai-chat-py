import httpx
import asyncio
import json

STATUS_URL = "https://duckduckgo.com/duckchat/v1/status"
CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"
STATUS_HEADERS = {"x-vqd-accept": "1"}

class Chat:
    def __init__(self, vqd: str, model: str, proxy: str = None):
        self.old_vqd = vqd
        self.new_vqd = vqd
        self.model = model
        self.messages = []
        self.proxy = proxy  # Store proxy in the instance

    async def fetch(self, content: str) -> httpx.Response:
        self.messages.append({"content": content, "role": "user"})
        payload = {
            "model": self.model,
            "messages": self.messages,
        }
        async with httpx.AsyncClient(proxies=self.proxy) as client:  # Use self.proxy
            response = await client.post(CHAT_URL, headers={"x-vqd-4": self.new_vqd, "Content-Type": "application/json"}, json=payload)
            if not response.is_success:
                raise Exception(f"{response.status_code}: Failed to send message. {response.text}")
            return response

    async def fetch_full(self, content: str) -> str:
        response = await self.fetch(content)
        text = ""
        async for events in response.aiter_text():
            events=events[6:].split('data:')
            # Debug information
            print(f"Debug: Received event data: {type(events)}")  # Log the event data
            print('11111111')

            # Check if the event is a valid JSON string
            for  event in events:
                json_data = event  # Remove the "data: " prefix
                print('222222222',json_data)
                if json_data == "[DONE]":
                    continue  # Stop processing if we receive [DONE]
                try:
                    message_data = json.loads(json_data)
                    if "message"  in message_data:
                        text += message_data["message"]

  # Parse the JSON data
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {json_data}")  # Log the error
                    continue  # Skip to the next event if JSON is invalid
            else:
                print(f"Unexpected event format: {event}")  # Log unexpected formats
                continue  # Skip to the next event

        print('?///////',text)
        self.new_vqd = response.headers.get("x-vqd-4", self.new_vqd)
        self.messages.append({"content": text, "role": "assistant"})
        return text

    async def fetch_stream(self, content: str):
        response = await self.fetch(content)
        async for event in response.aiter_text():
            message_data = json.loads(event)
            if "message" not in message_data:
                break
            yield message_data["message"]

    def redo(self):
        self.new_vqd = self.old_vqd
        self.messages.pop()
        self.messages.pop()

async def init_chat(model: str, proxy: str = None) -> Chat:
    async with httpx.AsyncClient(proxies=proxy) as client:
        status_response = await client.get(STATUS_URL, headers=STATUS_HEADERS)
        vqd = status_response.headers.get("x-vqd-4")
        if not vqd:
            raise Exception(f"{status_response.status_code}: Failed to initialize chat. {status_response.text}")
        return Chat(vqd, model, proxy)  # Pass proxy to Chat instance

# Example usage
if __name__ == "__main__":
    model = "gpt-4o-mini"  # Example model
    proxy = "socks5://127.0.0.1:1080"  # Replace with your proxy if needed

    async def main():
        chat = await init_chat(model, proxy)
        response = await chat.fetch_full("Hello, how are you?")
        print('==========',response)

    asyncio.run(main())
