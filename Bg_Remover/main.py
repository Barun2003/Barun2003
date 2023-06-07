import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from PIL import Image
from rembg import remove
from tempfile import NamedTemporaryFile
from starlette.exceptions import HTTPException
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import HTTPException

app = FastAPI()

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
UPLOAD_FOLDER = 'uploads/'
PROCESSED_FOLDER = 'processed/'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def request_wants_json(request: Request) -> bool:

    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json'

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = {
        "detail": exc.detail,
    }

    if request_wants_json(request):
        return JSONResponse(content=response, status_code=exc.status_code)
    else:

        return HTMLResponse(content=f"<p>{exc.detail}</p>", status_code=exc.status_code)

from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.datastructures import Headers

def request_wants_json(request: Request) -> bool:
    accept = Headers(request.headers).get("accept", "")
    return "application/json" in accept

@app.post("/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not file:
        return JSONResponse(content={'message': 'No file'}, status_code=400)
    if not allowed_file(file.filename):
        return JSONResponse(content={'message': 'Invalid file extension'}, status_code=400)

    file_content = await file.read()
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, 'wb') as f:
        f.write(file_content)

    processed_file_name = os.path.join(PROCESSED_FOLDER, f'{os.path.splitext(file.filename)[0]}_processed{os.path.splitext(file.filename)[1]}')

    with NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_content)
        temp_file.flush()
        img = Image.open(temp_file.name)
        result = remove(img)
        result = result.convert("RGB")
        result.save(processed_file_name, format='JPEG')

    if request_wants_json(request):
        return JSONResponse(content={'message': 'File processed successfully', 'url': f'/downloadfile/{os.path.basename(processed_file_name)}'})
    else:
        return HTMLResponse(content=f'<html><body><a href="/downloadfile/{os.path.basename(processed_file_name)}">Download processed file</a></body></html>')


@app.get('/downloadfile/{filename}')
async def download_file(filename: str,request: Request):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if request_wants_json(request):
        return JSONResponse(content={'message': 'Download URL for the file', 'url': f'/return-files/{filename}'})
    else:
        return HTMLResponse(content=f'<html><body><a href="/return-files/{filename}">Download {filename}</a></body></html>')

@app.get('/return-files/{filename}')
async def return_files(filename: str):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    return FileResponse(file_path, filename=filename, media_type='application/octet-stream')



