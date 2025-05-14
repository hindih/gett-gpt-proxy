from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import logging

app = FastAPI()

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy")

AUTH_URL = os.getenv("AUTH_URL")
AUTH_PAYLOAD = {
    "client_id": os.getenv("CLIENT_ID"),
    "client_secret": os.getenv("CLIENT_SECRET"),
    "grant_type": "client_credentials",
    "scope": os.getenv("SCOPE", "demand_partner")
}
AUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded"
}

@app.post("/auth")
async def authenticate():
    async with httpx.AsyncClient() as client:
        try:
            logger.info("====== AUTH REQUEST START ======")
            logger.info(f"URL: {AUTH_URL}")
            logger.info(f"Headers: {AUTH_HEADERS}")
            logger.info(f"Payload: {AUTH_PAYLOAD}")

            response = await client.post(AUTH_URL, data=AUTH_PAYLOAD, headers=AUTH_HEADERS)

            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Body: {response.text}")
            logger.info("====== AUTH REQUEST END ======")

            response.raise_for_status()
            return JSONResponse(content=response.json())
        except httpx.HTTPStatusError as e:
            logger.error(" HTTP error during auth request")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Body: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error(" Unexpected error during auth request")
            logger.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))
