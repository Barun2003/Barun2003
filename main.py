import json
import os
import random
from typing import Literal, Optional
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Response
import requests
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from mangum import Mangum


class Book(BaseModel):
    name: str
    genre: Literal["fiction", "non-fiction"]
    price: float
    book_id: Optional[str] = uuid4().hex
    img_url: str


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
    for book in BOOKS:
        if book.book_id == book_id:
            return book

    raise HTTPException(404, f"Book ID {book_id} not found in database.")


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


@app.get("/get-book-image")
async def get_book_image(book_id: str):
    for book in BOOKS:
        if book.book_id == book_id:
            image_url = book.img_url
            response = requests.get(image_url)
            return Response(content=response.content, media_type="image/jpeg")

    raise HTTPException(404, f"Book ID {book_id} not found in database.")


@app.get("/download-book-image")
async def download_book_image(book_id: str):
    for book in BOOKS:
        if book.book_id == book_id:
            image_url = book.img_url
            image_name = f"{book.book_id}.jpg"
            response = requests.get(image_url)
            with open(image_name, "wb") as f:
                f.write(response.content)
            return {"message": f"Book image for ID {book_id} has been downloaded and saved as {image_name}."}

    raise HTTPException(404, f"Book ID {book_id} not found in database.")

