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

@app.get("/images/{image_name}")
def get_image(image_name: str):
    file_path = IMAGE_DIR / image_name
    if not file_path.exists():
        return {"error": "Image not found"}
    return FileResponse(file_path)


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
    print("Received tags:", tags)
    
    # ensure user structure
    if user_id not in users:
        users[user_id] = {"memories": [], "tags": []}
    elif "tags" not in users[user_id]:
        users[user_id]["tags"] = []

    # Parse incoming tags from comma-separated string
    parsed_tags = []
    
    # Split by comma and process pairs
    items = [item.strip() for item in tags.split(',') if item.strip()]
    
    # Group items by pairs (name, color)
    for i in range(0, len(items), 2):
        if i + 1 < len(items):
            tag_name = items[i]
            tag_color = items[i + 1]
            parsed_tags.append([tag_name, tag_color])
    
    print("Parsed tags:", parsed_tags)

    if not parsed_tags:
        return {"message": "No tags provided", "tags": users[user_id]["tags"]}

    users[user_id]["tags"] = parsed_tags
    db["users"] = users
    write_db(db)

    return {"message": "Tags replaced", "tags": users[user_id]["tags"]}


@app.get("/uploads/{filename}")
def get_uploaded_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)