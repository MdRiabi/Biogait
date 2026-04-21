from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import jwt
from app.config import get_settings
from app.db.session import SessionLocal
from app.models.audit import AuditLog
import time
import asyncio

settings = get_settings()

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        path = request.url.path

        # Évite de bloquer l'UI sur les routes très fréquentes (assets/ws/health).
        if (
            path.startswith("/_nicegui")
            or path.startswith("/api/v1/recognition/ws")
            or path.startswith("/favicon")
            or path == "/health"
        ):
            return response
        
        # Extraire user si JWT présent
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        # Création log async
        log_entry = AuditLog(
            action=request.method,
            resource=str(request.url.path),
            ip_address=request.client.host if request.client else "unknown",
            status_code=response.status_code,
            details=f"duration:{time.time()-start_time:.3f}s"
        )
        
        async with SessionLocal() as session:
            session.add(log_entry)
            try:
                # Ne jamais ralentir la réponse utilisateur à cause de l'audit log.
                await asyncio.wait_for(session.commit(), timeout=0.5)
            except Exception:
                await session.rollback()
                
        return response