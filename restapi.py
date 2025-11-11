from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json
import shutil
import os
import uuid

app = FastAPI()

DB_PATH = Path("db.json")
IMAGE_DIR = Path("images")
UPLOAD_DIR = Path("uploads")

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



@app.post("/upload_memory")
async def upload_memory(
    user_id: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    location : str = Form(...)
):
    db= read_db()
    users = db.get("users", {})
    if user_id not in users:
        users[user_id] = {"memories": []}
    
    
    
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    memory = {
        "id": str(uuid.uuid4()),
        "title": title,
        "image_filename": unique_filename,
        "image_url": f"/uploads/{unique_filename}",
        "location" : location
    }

    users[user_id]["memories"].insert(0, memory)
    db["users"] = users
    write_db(db)
    
    return {"message": "Memory created", "memory": memory}


@app.get("/memories/{user_id}")
async def get_user_memories(user_id: str):
    db = read_db()
    users = db.get("users", {})
    
    if user_id not in users:
        return []
    
    return users[user_id].get("memories", [])

@app.get("/tags/{user_id}")
async def get_user_tags(user_id: str):
    db = read_db()
    users = db.get("users", {})
    
    if user_id not in users:
        return []
    
    return users[user_id].get("tags", [])


@app.post("/tags/{user_id}")
async def upload_tags(user_id: str, tags: str = Form(...)):
    db = read_db()
    users = db.get("users", {})

    if user_id not in users:
        users[user_id] = {"cart": [], "memories": [], "tags": []}
    elif "tags" not in users[user_id]:
        users[user_id]["tags"] = []

    parsed_tags = []
    try:
        parsed = json.loads(tags)
        if isinstance(parsed, list):
            parsed_tags = [str(t).strip() for t in parsed if str(t).strip()]
        else:
            parsed_tags = [str(parsed).strip()]
    except Exception:
        parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Insert new tags at the beginning, keep uniqueness preserving newest-first
    existing = users[user_id]["tags"]
    for t in reversed(parsed_tags):  # reversed so first in parsed_tags becomes first in list
        if t not in existing:
            existing.insert(0, t)

    users[user_id]["tags"] = existing
    db["users"] = users
    write_db(db)

    return {"message": "Tags updated", "tags": users[user_id]["tags"]}



@app.get("/uploads/{filename}")
def get_uploaded_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)