# -*- coding: utf-8 -*-
"""Start the web app with un1cum icons on /favicon.png and /favicon.ico."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ICON_PNG = ROOT / "static" / "un1cum-icon-v5.png"
ICON_FALLBACK = ROOT / "static" / "icon-192-any.png"
ICON_ICO = ROOT / "static" / "favicon.ico"
APPLE = ROOT / "static" / "apple-touch-icon.png"


def _patch_streamlit_routes() -> None:
    from starlette.responses import FileResponse
    from starlette.routing import Route

    from streamlit.web.server.starlette import starlette_app as sa

    orig = sa.create_streamlit_routes

    def create_streamlit_routes(runtime):
        png = ICON_PNG if ICON_PNG.is_file() else ICON_FALLBACK
        headers = {"Cache-Control": "no-store, max-age=0"}

        async def favicon_png(_request):
            return FileResponse(png, media_type="image/png", headers=headers)

        async def favicon_ico(_request):
            path = ICON_ICO if ICON_ICO.is_file() else png
            media = "image/x-icon" if path.suffix.lower() == ".ico" else "image/png"
            return FileResponse(path, media_type=media, headers=headers)

        async def apple(_request):
            path = APPLE if APPLE.is_file() else png
            return FileResponse(path, media_type="image/png", headers=headers)

        extra = [
            Route("/favicon.png", favicon_png, methods=["GET"]),
            Route("/favicon.ico", favicon_ico, methods=["GET"]),
            Route("/apple-touch-icon.png", apple, methods=["GET"]),
            Route("/apple-touch-icon-precomposed.png", apple, methods=["GET"]),
        ]
        return extra + orig(runtime)

    sa.create_streamlit_routes = create_streamlit_routes


if __name__ == "__main__":
    _patch_streamlit_routes()
    from streamlit.web import cli

    sys.argv = [
        "streamlit",
        "run",
        str(ROOT / "app.py"),
        "--server.port",
        "8502",
        "--server.headless",
        "true",
        *sys.argv[1:],
    ]
    cli.main()
