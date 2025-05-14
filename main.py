from fastapi import FastAPI, HTTPException
import httpx
import os

app = FastAPI()

AUTH_URL = os.getenv("AUTH_URL", "https://api.example.com/auth/token")
AUTH_PAYLOAD = {
    "client_id": os.getenv("CLIENT_ID"),
    "client_secret": os.getenv("CLIENT_SECRET"),
    "grant_type": "client_credentials"
}
AUTH_HEADERS = {
    "Content-Type": "application/json"
}

@app.post("/auth")
async def authenticate():
    async with httpx.AsyncClient() as client:
        response = await client.post(AUTH_URL, json=AUTH_PAYLOAD, headers=AUTH_HEADERS)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Authentication failed")
        return response.json()