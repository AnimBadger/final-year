from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("sessionId")
        if not session_id:
            session_id = str(uuid.uuid4())
        request.state.session_id = session_id
        response = await call_next(request)
        if "sessionId" not in request.cookies:
            response.set_cookie(key="sessionId", value=session_id)
        return response
