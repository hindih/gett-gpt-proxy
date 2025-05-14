from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI()

AUTH_URL = os.getenv("AUTH_URL")
AUTH_PAYLOAD = {
    "client_id": os.getenv("CLIENT_ID"),
    "client_secret": os.getenv("CLIENT_SECRET"),
    "grant_type": "client_credentials",
    "scope": os.getenv("SCOPE", "cab:book")
}
AUTH_HEADERS = {
    "Content-Type": "application/json"
}

@app.post("/auth")
async def authenticate():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(AUTH_URL, json=AUTH_PAYLOAD, headers=AUTH_HEADERS)
            response.raise_for_status()
            return JSONResponse(content=response.json())
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
