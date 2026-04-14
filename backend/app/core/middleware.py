from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import jwt
from app.config import get_settings
from app.db.session import async_session_factory
from app.models.audit import AuditLog
import time

settings = get_settings()

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        
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
        
        async with async_session_factory() as session:
            session.add(log_entry)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                
        return response