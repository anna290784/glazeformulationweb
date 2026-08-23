# -*- coding: utf-8 -*-
"""Put the un1cum logo in the first HTML Chrome reads. Web app only."""
from __future__ import annotations

import base64
import re
import shutil
from pathlib import Path

MARKER = "ga-un1cum-brand"
ICON_VER = "un1cum-icon-v5.png"
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "static"


def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _head_snippet() -> str:
    src_192 = SRC / "icon-192-any.png"
    src_32 = SRC / "favicon-32.png"
    icon = src_192 if src_192.is_file() else src_32
    if not icon.is_file():
        return ""
    data = _data_uri(icon)
    return f"""    <link rel="shortcut icon" href="{data}" />
    <link rel="icon" type="image/png" href="{data}" />
    <link rel="apple-touch-icon" href="{data}" />
    <link rel="manifest" href="/app/static/manifest.json" />
    <meta name="theme-color" content="#141418" />
    <meta name="application-name" content="Glaze Formulation Web" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-title" content="Glaze Formulation Web" />
    <meta name="mobile-web-app-capable" content="yes" />
    <script id="ga-un1cum-brand-js">
    (function () {{
      var ICON = "{data}";
      function apply() {{
        var links = document.querySelectorAll(
          "link[rel='shortcut icon'], link[rel='icon'], link[rel='apple-touch-icon']"
        );
        for (var i = 0; i < links.length; i++) {{
          var h = String(links[i].getAttribute("href") || "");
          if (h.indexOf("data:image") === 0) continue;
          if (h.indexOf("favicon.png") !== -1 || h.indexOf("./favicon") !== -1) {{
            links[i].setAttribute("href", ICON);
          }}
        }}
      }}
      apply();
      new MutationObserver(apply).observe(document.documentElement, {{
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["href"]
      }});
    }})();
    </script>
    <!-- {MARKER} -->
"""


def install() -> None:
    try:
        from streamlit import file_util

        static_dir = Path(file_util.get_static_dir())
        if not static_dir.is_dir() or not SRC.is_dir():
            return
        _copy_icons(static_dir)
        _patch_index(static_dir / "index.html")
    except Exception:
        return


def _copy_icons(static_dir: Path) -> None:
    src_192 = SRC / "icon-192-any.png"
    if src_192.is_file():
        shutil.copy2(src_192, SRC / ICON_VER)
        shutil.copy2(src_192, static_dir / ICON_VER)
    mapping = {
        "favicon.png": SRC / "icon-192-any.png",
        "favicon.ico": SRC / "favicon.ico",
        "apple-touch-icon.png": SRC / "apple-touch-icon.png",
        "apple-touch-icon-precomposed.png": SRC / "apple-touch-icon.png",
        "icon-192-any.png": SRC / "icon-192-any.png",
        "icon-512-any.png": SRC / "icon-512-any.png",
        "manifest.json": SRC / "manifest.json",
        ICON_VER: SRC / ICON_VER,
    }
    backup = static_dir / "favicon.streamlit-orig.png"
    original = static_dir / "favicon.png"
    src_fav = mapping["favicon.png"]
    if original.is_file() and src_fav.is_file() and not backup.is_file():
        if original.stat().st_size != src_fav.stat().st_size:
            shutil.copy2(original, backup)
    for dest_name, src_path in mapping.items():
        if src_path.is_file():
            shutil.copy2(src_path, static_dir / dest_name)


def _strip_brand(html: str) -> str:
    html = re.sub(r"\s*<script id=\"ga-un1cum-brand-js\">[\s\S]*?</script>", "", html)
    html = re.sub(r"\s*<!-- ga-un1cum-brand -->", "", html)
    html = re.sub(
        r"\s*<link rel=\"shortcut icon\" href=\"(?:/app/static/[^\"]+|data:image[^\"]+)\"\s*/>",
        "",
        html,
    )
    html = re.sub(
        r"\s*<link rel=\"icon\"[^>]*href=\"(?:/app/static/[^\"]+|data:image[^\"]+)\"[^>]*>",
        "",
        html,
    )
    html = re.sub(r"\s*<link rel=\"apple-touch-icon\"[^>]*>", "", html)
    html = re.sub(
        r"\s*<link rel=\"manifest\" href=\"/app/static/manifest.json\"\s*/>",
        "",
        html,
    )
    html = re.sub(r"\s*<meta name=\"theme-color\"[^>]*>", "", html)
    html = re.sub(r"\s*<meta name=\"application-name\"[^>]*>", "", html)
    html = re.sub(r"\s*<meta name=\"apple-mobile-web-app-[^\"]*\"[^>]*>", "", html)
    html = re.sub(r"\s*<meta name=\"mobile-web-app-capable\"[^>]*>", "", html)
    html = re.sub(
        r"\s*<link rel=\"shortcut icon\" href=\"./favicon.png\"\s*/>",
        "",
        html,
    )
    return html


def _patch_index(index_path: Path) -> None:
    if not index_path.is_file():
        return
    snippet = _head_snippet()
    if not snippet:
        return
    html = _strip_brand(index_path.read_text(encoding="utf-8"))
    needle = """    <meta
      name="viewport"
      content="width=device-width, initial-scale=1, shrink-to-fit=no"
    />"""
    if needle in html:
        html = html.replace(needle, needle + "\n" + snippet, 1)
    else:
        html = html.replace("</head>", snippet + "  </head>", 1)
    index_path.write_text(html, encoding="utf-8")
