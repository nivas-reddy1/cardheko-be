from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import router

load_dotenv()

app = FastAPI(title="CarDekho AI Advisor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cardheko.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)
