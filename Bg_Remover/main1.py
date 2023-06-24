import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from tempfile import NamedTemporaryFile
from starlette.exceptions import HTTPException
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from typing import List, Tuple

app = FastAPI()

ALLOWED_EXTENSIONS = set(["jpg", "jpeg"])
UPLOAD_FOLDER = "uploads/"
PROCESSED_FOLDER = "processed/"
DEFAULT_RESOLUTION = (1080, 1080)


def create_folders():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def bgremove1(myimage, resolution):
    
    myimage = cv2.resize(myimage, resolution)

    
    myimage = cv2.GaussianBlur(myimage, (5, 5), 0)

    
    bins = np.array([0, 51, 102, 153, 204, 255])
    myimage[:, :, :] = np.digitize(myimage[:, :, :], bins, right=True) * 51

    
    myimage_grey = cv2.cvtColor(myimage, cv2.COLOR_BGR2GRAY)

    
    
    ret, background = cv2.threshold(
        myimage_grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    
    background = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)

    
    
    ret, foreground = cv2.threshold(
        myimage_grey, 0, 255, cv2.THRESH_TOZERO_INV + cv2.THRESH_OTSU
    )
    foreground = cv2.bitwise_and(
        myimage, myimage, mask=foreground
    )  

    
    foreground = cv2.resize(foreground, background.shape[:2][::-1])

   
    finalimage = cv2.add(background, foreground)

    return finalimage


def request_wants_json(request: Request) -> bool:
    accept_header = request.headers.get("Accept", "")
    return "application/json" in accept_header


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = {
        "detail": exc.detail,
    }

    if request_wants_json(request):
        return JSONResponse(content=response, status_code=exc.status_code)
    else:
        return HTMLResponse(content=f"<p>{exc.detail}</p>", status_code=exc.status_code)


@app.post("/")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    resolution: Tuple[int, int] = Query(
        DEFAULT_RESOLUTION,
        description="The desired resolution of the processed image in (width, height) format.",
    ),
):
    create_folders()

    if not files:
        return JSONResponse(content={"message": "No files"}, status_code=400)

    processed_files = []

    for file in files:
        if not allowed_file(file.filename):
            return JSONResponse(
                content={"message": f"Invalid file extension: {file.filename}"},
                status_code=400,
            )

        file_content = await file.read()
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        processed_file_name = os.path.join(
            PROCESSED_FOLDER, f"{os.path.splitext(file.filename)[0]}_processed.png"
        )

        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            img_path = temp_file.name

            
            img = cv2.imread(img_path)

            
            processed_image = bgremove1(img, resolution)

            
            cv2.imwrite(processed_file_name, processed_image)

        processed_files.append(
            {
                "filename": file.filename,
                "processed_filename": os.path.basename(processed_file_name),
            }
        )

    if request_wants_json(request):
        download_urls = [
            {
                "filename": file["filename"],
                "download_url": f'http://35.154.99.113/downloadfile/{file["processed_filename"]}',
            }
            for file in processed_files
        ]
        return JSONResponse(
            content={"message": "Files processed successfully", "files": download_urls}
        )
    else:
        return HTMLResponse(
            content=generate_download_links(processed_files, request.base_url)
        )


def generate_download_links(processed_files, base_url):
    links = ""
    for file in processed_files:
        download_url = f'http://35.154.99.113/downloadfile/{file["processed_filename"]}'
        links += f'<p>Image Name: {file["filename"]}</p><p><a href="{download_url}">Download {file["filename"]} Processed File</a></p>'
    return f"<html><body>{links}</body></html>"


@app.get("/downloadfile/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, media_type="image/png")
