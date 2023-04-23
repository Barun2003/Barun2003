import json
from pydantic import HttpUrl
import os
import random
from typing import Literal, Optional
from uuid import uuid4
import uuid
import requests
from fastapi import FastAPI, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from mangum import Mangum
from fastapi import UploadFile, File
import json
from pydantic import HttpUrl, BaseModel
from fastapi import UploadFile, File, FastAPI
from typing import Dict
import uuid
import requests


class Book(BaseModel):
    name: str
    genre: Literal["fiction", "non-fiction"]
    price: float
    book_id: Optional[str] = uuid4().hex
    img_url: Optional[str] = None
    download_url: Optional[str] = None


BOOKS_FILE = "books.json"
BOOKS = []

if os.path.exists(BOOKS_FILE):
    with open(BOOKS_FILE, "r") as f:
        BOOKS = json.load(f, object_hook=lambda x: Book(**x))

app = FastAPI()
handler = Mangum(app)


@app.get("/")
async def root():
    return {"message": "Welcome to my bookstore app!"}


@app.get("/random-book")
async def random_book():
    return random.choice(BOOKS)


@app.get("/list-books")
async def list_books():
    return {"books": BOOKS}


@app.get("/book_by_index/{index}")
async def book_by_index(index: int):
    if index < len(BOOKS):
        return BOOKS[index]
    else:
        raise HTTPException(404, f"Book index {index} out of range ({len(BOOKS)}).")


@app.post("/add-book")
async def add_book(book: Book):
    book.book_id = uuid4().hex
    json_book = jsonable_encoder(book)
    BOOKS.append(json_book)

    with open(BOOKS_FILE, "w") as f:
        json.dump(BOOKS, f)

    return {"book_id": book.book_id}



@app.get("/get-book")
async def get_book(book_id: str):
    
    with open('books.json', 'r') as file:
        books_data = json.load(file)

    
    for book in books_data:
        if book['book_id'] == book_id:
            
            book['download_url'] = f"http://35.154.99.113/get-book?book_id={book_id}"

            
            with open('books.json', 'w') as file:
                json.dump(books_data, file, indent=4)

            
            images_dir = os.path.join(os.getcwd(), "images")
            image_file_path = os.path.join(images_dir, f"{book_id}.jpg")

            if os.path.exists(image_file_path):
                return FileResponse(image_file_path)
            else:
                return {"error": "Book not found"}

    return {"error": "Book not found"}



@app.get("/get-books")
async def get_books(book_ids: Optional[str] = None):
    if book_ids is None:
        raise HTTPException(400, "Missing book_id parameter")
    else:
        book_ids = book_ids.split(",")
        book_ids = book_ids[:3]

        result = {}
        for book_id in book_ids:
            for book in BOOKS:
                if book.book_id == book_id:
                    result[book_id] = book
                    break
        return result


@app.post("/upload-book-image/{book_id}")
async def upload_book_image(book_id: str, image: UploadFile = File(...)):
    for book in BOOKS:
        if book.book_id == book_id:
            image_path = f"images/{book_id}.jpg"
            with open(image_path, "wb") as f:
                f.write(image.file.read())
            book.img_url = image_path
            json_books = jsonable_encoder(BOOKS)
            with open(BOOKS_FILE, "w") as f:
                json.dump(json_books, f)
            return {"message": f"Book image for ID {book_id} uploaded in books.json."}

    raise HTTPException(404, f"Book ID {book_id} not found in database.")
