# app.py
import os
import json
import re
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read secrets/config from environment
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")  # <-- set this in Render / locally
FRONTEND_ORIGIN = os.environ.get("FRONTEND_URL")  # optional, e.g. https://your-frontend.vercel.app

if not GEMINI_KEY:
    logger.warning("GEMINI_API_KEY not set. Gemini calls will fail until you provide a key.")

# Configure Gemini (only attempt if key is provided)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

app = Flask(__name__)
# Restrict CORS in production by setting FRONTEND_URL; otherwise allow all for dev
if FRONTEND_ORIGIN:
    CORS(app, origins=[FRONTEND_ORIGIN])
else:
    CORS(app)

# -------------------------------
# Manual product dataset
# -------------------------------
products = [
    {"id": 1, "name": "iPhone 13", "price": 799, "category": "mobile"},
    {"id": 2, "name": "Samsung Galaxy S22", "price": 699, "category": "mobile"},
    {"id": 3, "name": "Google Pixel 6a", "price": 449, "category": "mobile"},
    {"id": 4, "name": "OnePlus 9", "price": 599, "category": "mobile"},
    {"id": 5, "name": "Motorola G Power", "price": 299, "category": "mobile"},
    {"id": 6, "name": "Sony WH-1000XM4 Headphones", "price": 349, "category": "electronics"},
    {"id": 7, "name": "Bose QuietComfort 35 II", "price": 299, "category": "electronics"},
    {"id": 8, "name": "Dell XPS 13 Laptop", "price": 999, "category": "laptop"},
    {"id": 9, "name": "MacBook Air M1", "price": 1099, "category": "laptop"},
    {"id": 10, "name": "Apple Watch Series 7", "price": 399, "category": "wearable"},
    {"id": 11, "name": "Fitbit Charge 5", "price": 149, "category": "wearable"},
    {"id": 12, "name": "Canon EOS M50 Camera", "price": 579, "category": "camera"},
    {"id": 13, "name": "Nikon D3500 Camera", "price": 499, "category": "camera"},
    {"id": 14, "name": "KitchenAid Stand Mixer", "price": 399, "category": "appliance"},
    {"id": 15, "name": "Instant Pot Duo", "price": 99, "category": "appliance"},
]

# -------------------------------
# Helper to extract JSON safely from Gemini
# -------------------------------
def extract_json(text):
    if not text:
        return []
    # Try direct JSON parse
    try:
        return json.loads(text)
    except Exception:
        # try to extract a JSON array from the text
        match = re.search(r"\[.*\]", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return []
    return []

# -------------------------------
# /recommend endpoint
# -------------------------------
@app.route("/recommend", methods=["POST"])
def recommend_api():
    payload = request.get_json(silent=True) or {}
    preference = (payload.get("preference") or "").strip().lower()

    # Pre-filter products by category and price
    filtered = []
    max_price = None
    price_match = re.search(r"\$(\d+)", preference)
    if price_match:
        try:
            max_price = int(price_match.group(1))
        except ValueError:
            max_price = None

    for p in products:
        if "mobile" in preference or "phone" in preference:
            if p["category"] == "mobile" and (max_price is None or p["price"] <= max_price):
                filtered.append(p)
        elif "laptop" in preference:
            if p["category"] == "laptop" and (max_price is None or p["price"] <= max_price):
                filtered.append(p)
        elif "wearable" in preference or "watch" in preference:
            if p["category"] == "wearable" and (max_price is None or p["price"] <= max_price):
                filtered.append(p)
        else:
            # fallback: include all products within price if price is mentioned
            if max_price is None or p["price"] <= max_price:
                filtered.append(p)

    if not filtered:
        return jsonify([]), 200

    # Use Gemini to rank filtered products (try/catch and graceful fallback)
    prompt = (
        f'A user says: "{preference}".\n'
        "From the following product list, rank the most relevant products.\n"
        "Respond ONLY with a JSON array of product NAMES in order of relevance.\n\n"
        f"Products:\n{json.dumps(filtered)}\n"
    )

    recommended = []
    # Only call Gemini if key present
    if GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            # best effort to pull text from response
            resp_text = getattr(response, "text", None) or str(response)
            recommended_names = extract_json(resp_text)
            # normalize and map back to product objects
            recommended_names = [name.strip().lower() for name in (recommended_names or [])]
            recommended = [p for name in recommended_names for p in filtered if p["name"].lower() == name]
            logger.info("Gemini returned %d recommendations", len(recommended))
        except Exception as e:
            logger.exception("Gemini call failed: %s", e)
            recommended = []
    else:
        logger.warning("Skipping Gemini call because GEMINI_API_KEY is not set.")
        recommended = []

    # If Gemini failed or returned nothing, fallback to a simple heuristic:
    if not recommended:
        # Fallback heuristic: if a max_price is provided, return items under that price sorted by price ascending,
        # otherwise prefer lower-priced items first (you can change heuristic as needed).
        logger.info("Using fallback ranking")
        recommended = sorted(filtered, key=lambda x: x["price"])

    return jsonify(recommended), 200


# -------------------------------
# Server entrypoint
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # debug True only if explicitly asked for development via env var
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
