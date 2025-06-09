from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import aiosqlite
import os
import uuid
from typing import Optional
from contextlib import asynccontextmanager

# Подключение к базе данных
DATABASE = "services.db"

# Создаем папку для загрузок
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL,
            image_url TEXT
        )
        """)
        await db.commit()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/api/services/{category}")
async def get_services_by_category(category: str):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            "SELECT * FROM services WHERE category = ?",
            (category,)
        )
        services = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "category": row[1],
                "name": row[2],
                "description": row[3],
                "price": row[4],
                "image_url": row[5]
            }
            for row in services
        ]


@app.post("/api/services/{category}")
async def create_service(
        category: str,
        name: str = Form(...),
        description: str = Form(...),
        price: int = Form(...),
        image: Optional[UploadFile] = File(None)
):
    image_url = None
    if image:
        file_ext = os.path.splitext(image.filename)[1]
        image_url = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, image_url)

        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())

    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            """
            INSERT INTO services (category, name, description, price, image_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (category, name, description, price, image_url)
        )
        await db.commit()
        return JSONResponse(status_code=201, content={"message": "Service created"})


@app.put("/api/services/{category}/{id}")
async def update_service(
        category: str,
        id: int,
        name: str = Form(...),
        description: str = Form(...),
        price: int = Form(...),
        image: Optional[UploadFile] = File(None)
):
    image_url = None
    if image:
        file_ext = os.path.splitext(image.filename)[1]
        image_url = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, image_url)

        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())

    async with aiosqlite.connect(DATABASE) as db:
        # Получаем текущее изображение для удаления
        cursor = await db.execute(
            "SELECT image_url FROM services WHERE id = ?",
            (id,)
        )
        old_image = (await cursor.fetchone())[0]

        if image_url and old_image:
            try:
                os.remove(os.path.join(UPLOAD_DIR, old_image))
            except:
                pass

        if image_url:
            await db.execute(
                """
                UPDATE services 
                SET name = ?, description = ?, price = ?, image_url = ?
                WHERE id = ? AND category = ?
                """,
                (name, description, price, image_url, id, category))
        else:
            await db.execute(
                """
                UPDATE services 
                SET name = ?, description = ?, price = ?
                WHERE id = ? AND category = ?
                """,
                (name, description, price, id, category))

        await db.commit()
        return {"message": "Service updated"}


@app.delete("/api/services/{category}/{id}")
async def delete_service(category: str, id: int):
    async with aiosqlite.connect(DATABASE) as db:
        # Получаем информацию об изображении
        cursor = await db.execute(
            "SELECT image_url FROM services WHERE id = ? AND category = ?",
            (id, category)
        )
        service = await cursor.fetchone()

        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Удаляем запись из БД
        await db.execute(
            "DELETE FROM services WHERE id = ? AND category = ?",
            (id, category)
        )
        await db.commit()

        # Удаляем изображение
        if service[0]:
            try:
                os.remove(os.path.join(UPLOAD_DIR, service[0]))
            except FileNotFoundError:
                pass

        return {"message": "Service deleted"}