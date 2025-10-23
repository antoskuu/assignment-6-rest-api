from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json


app = FastAPI()
DB_PATH = Path("db.json")
IMAGE_DIR = Path("images")



def read_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

@app.get("/categories")
def get_categories():
    db = read_db()
    return db.get("categories", [])


@app.get("/images/{image_name}")
def get_image(image_name: str):
    file_path = IMAGE_DIR / image_name
    if not file_path.exists():
        return {"error": "Image not found"}
    return FileResponse(file_path)


@app.get("/cart")
async def get_cart(user_id):
    db = read_db()
    users = db.get("users", {})
    if user_id not in users:
        users[user_id] = {"cart": []}
        db["users"] = users
        write_db(db)
    print(users[user_id].get("cart", []))
    return users[user_id].get("cart", [])


@app.post("/cart")
async def add_to_cart(id: int, title: str, user_id: str):
    db = read_db()
    users = db.get("users", {})
    if user_id not in users:
        users[user_id] = {"cart": []}
        db["users"] = users
        write_db(db)
    cart = users[user_id]["cart"]
    cart.append({"id": id, "title": title})
    db["users"] = users

    write_db(db)
    return {"message": "Item added", "cart": cart}


@app.delete("/cart")
async def remove_from_cart(id: int, user_id: str):
    db = read_db()
    users = db.get("users", {})
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    cart = users[user_id]["cart"]
    cart = [item for item in cart if not (item["id"] == id)]
    users[user_id]["cart"] = cart
    db["users"] = users
    write_db(db)
    return {"message": "Item removed", "cart": cart}