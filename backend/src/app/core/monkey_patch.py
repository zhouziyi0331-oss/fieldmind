"""
Monkey Patch: 彻底禁用 Starlette Router 的 307 重定向

这是最激进的解决方案，直接修改 Starlette 的运行时行为
"""

def disable_redirect_slashes():
    """
    运行时修改 Starlette Router，禁用所有 307 重定向
    """
    from starlette.routing import Router

    # 保存原始的 __call__ 方法
    original_call = Router.__call__

    async def patched_call(self, scope, receive, send):
        """
        修改后的 __call__ 方法

        强制设置 redirect_slashes = False
        """
        # 强制禁用重定向
        original_redirect = self.redirect_slashes
        self.redirect_slashes = False

        try:
            # 调用原始方法
            await original_call(self, scope, receive, send)
        finally:
            # 恢复原始设置
            self.redirect_slashes = original_redirect

    # 替换方法
    Router.__call__ = patched_call
    print("✅ Monkey Patch 已应用：禁用所有 Router 的 redirect_slashes")


# 在导入 FastAPI 之前应用 patch
if __name__ == "__main__":
    disable_redirect_slashes()

    # 测试
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/test")
    async def test():
        return {"message": "test"}

    print(f"app.router.redirect_slashes: {app.router.redirect_slashes}")
