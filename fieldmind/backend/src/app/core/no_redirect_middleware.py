"""
ASGI 中间件：彻底拦截 307 重定向
"""

class NoRedirectMiddleware:
    """
    最底层的 ASGI 中间件，拦截所有 307 响应
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        original_path = scope["path"]

        # 如果路径不以斜杠结尾，直接修改为带斜杠
        if not original_path.endswith("/") and original_path != "/":
            scope["path"] = original_path + "/"
            scope["raw_path"] = (original_path + "/").encode()

        await self.app(scope, receive, send)
