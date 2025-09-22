import google.generativeai as genai
import json
import re

# Configure Gemini with your API key
genai.configure(api_key="AIzaSyDIun6xCuT2Sp0w6s4L5FmL72v_TgGA-hU")  # <-- replace with your key

# Manually created product dataset (15 products)
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

# Helper function to extract JSON safely from Gemini output
def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\[.*\]", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                return []
        return []

# Recommendation function
def get_recommendations(preference):
    # Prepare prompt for Gemini
    prompt = f"""
    A user says: "{preference}".
    From the following product list, suggest the most relevant products.
    Respond ONLY with a JSON array of product NAMES.

    Products:
    {json.dumps(products)}
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    # Extract product names from Gemini's output
    recommended_names = extract_json(response.text)

    # Filter the products dataset by the recommended names
    recommended = [p for p in products if p["name"] in recommended_names]

    print("\nUser Preference:", preference)
    print("Recommended Products:")
    for r in recommended:
        print(f"- {r['name']} (${r['price']}) [{r['category']}]")

# Example usage
get_recommendations("I want mobile phones under $500")