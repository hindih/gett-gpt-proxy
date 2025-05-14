from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
import os
import logging

app = FastAPI()

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy")

# Auth configuration
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

# Gett booking config
GETT_BOOK_URL = "https://api.sandbox.gett.com/v1/private/orders/create"
PARTNER_ID = os.getenv("PARTNER_ID")

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
            logger.error("HTTP error during auth request")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Body: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error("Unexpected error during auth request")
            logger.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/book_ride")
async def book_ride(request: Request):
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    async with httpx.AsyncClient() as client:
        # Step 1: Get bearer token
        auth_response = await client.post(f"{request.base_url}auth")
        if auth_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to authenticate with Gett")
        access_token = auth_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=500, detail="Missing access token in auth response")

        # Step 2: Build booking payload
        passenger = {
            "name": body["passenger_name"],
            "phone": body["passenger_phone"]
        }

        booking_payload = {
            "lc": "en",
            "partner_id": PARTNER_ID,
            "user_accepted_terms_and_privacy": body.get("user_accepted_terms_and_privacy", True),
            "category": "transportation",
            "product_id": body["product_id"],
            "stops": [
                {
                    "type": "origin",
                    "actions": [{"type": "pick_up", "user": passenger}],
                    "location": {
                        "lat": body["origin_lat"],
                        "lng": body["origin_lng"],
                        "address": {"full_address": body.get("origin_address_name", "")}
                    }
                },
                {
                    "type": "destination",
                    "actions": [{"type": "drop_off", "user": passenger}],
                    "location": {
                        "lat": body["destination_lat"],
                        "lng": body["destination_lng"],
                        "address": {"full_address": body.get("destination_address_name", "")}
                    }
                }
            ],
            "payment": {
                "payment_type": "cash"
            }
        }

        if "scheduled_at" in body and body["scheduled_at"]:
            booking_payload["scheduled_at"] = body["scheduled_at"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logger.info("====== BOOKING REQUEST START ======")
        logger.info(f"Payload: {booking_payload}")

        response = await client.post(GETT_BOOK_URL, json=booking_payload, headers=headers)

        logger.info(f"Booking Response Status: {response.status_code}")
        logger.info(f"Booking Response Body: {response.text}")
        logger.info("====== BOOKING REQUEST END ======")

        try:
            return JSONResponse(status_code=response.status_code, content=response.json())
        except Exception:
            return JSONResponse(status_code=500, content={"error": "Invalid response from Gett"})

@app.get("/order_status/{order_id}")
async def order_status(order_id: str, request: Request):
    logger.info("====== ORDER STATUS REQUEST START ======")
    logger.info(f"Incoming request to check status of order: {order_id}")

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get bearer token
            auth_response = await client.post(f"{request.base_url}auth")
            logger.info(f"Auth response status: {auth_response.status_code}")
            logger.info(f"Auth response body: {auth_response.text}")

            if auth_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to authenticate with Gett")

            access_token = auth_response.json().get("access_token")
            if not access_token:
                raise HTTPException(status_code=500, detail="Missing access token in auth response")

            # Step 2: Call Gett API for order status
            url = f"https://api.sandbox.gett.com/v1/private/orders/{order_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            logger.info(f"Sending GET request to Gett API: {url}")
            response = await client.get(url, headers=headers)
            logger.info(f"Gett API response status: {response.status_code}")
            logger.info(f"Gett API response body: {response.text}")

            response.raise_for_status()
            return JSONResponse(status_code=response.status_code, content=response.json())

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Gett API: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error during order status check: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            logger.info("====== ORDER STATUS REQUEST END ======")

