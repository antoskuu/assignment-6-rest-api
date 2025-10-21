from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
import json


app = FastAPI()
DB_PATH = Path("db.json")
IMAGE_DIR = Path("images")



def read_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)


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
