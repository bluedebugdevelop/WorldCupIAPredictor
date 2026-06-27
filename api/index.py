"""Punto de entrada para Vercel (Python Serverless / ASGI).

Vercel detecta la variable ``app`` (aplicación ASGI) y la sirve. Aquí solo
añadimos el backend al path, fijamos la ruta del frontend dentro del bundle e
importamos la app FastAPI ya existente.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(_ROOT, "backend"))
os.environ.setdefault("FRONTEND_DIR", os.path.join(_ROOT, "frontend"))

from app.main import app  # noqa: E402  (debe ir tras ajustar sys.path)
