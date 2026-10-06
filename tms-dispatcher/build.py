"""Собирает прототип: встраивает CSS Leaflet и готовит версию для публикации артефактом.

python3 build.py <путь к leaflet.css> [<фрагмент-артефакт index>] [<фрагмент-артефакт lite>]

Собирает две версии: index.html (полная) и lite.html (упрощённая, «Кратко / Подробно»).
"""
import re, sys, pathlib
root = pathlib.Path(__file__).parent
import os
css = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
# Реальные маршруты bus62.ru (tools/extract_bus62.py → data/routes.json); путь можно переопределить через ROUTES
routes_path = pathlib.Path(os.environ.get("ROUTES", root / "data" / "routes.json"))

def build(name, fragment=None):
    src = (root / "src" / f"{name}.src.html").read_text(encoding="utf-8")
    full = src.replace("/*@@LEAFLET_CSS@@*/", css)
    if routes_path.exists():
        full = full.replace("/*@@ROUTES@@*/null", routes_path.read_text(encoding="utf-8").strip())
    (root / f"{name}.html").write_text(full, encoding="utf-8")
    if fragment:
        head = re.search(r"<head>(.*?)</head>", full, re.S).group(1)
        head = re.sub(r'<meta charset[^>]*>\s*|<meta name="viewport"[^>]*>\s*', "", head)
        body = re.search(r"<body>(.*)</body>", full, re.S).group(1)
        # config.js с ключом Яндекса в артефакт не публикуется: там внешние скрипты запрещены, работает схема
        body = body.replace('<script src="config.js"></script>\n', "")
        pathlib.Path(fragment).write_text(head.strip() + "\n" + body.strip() + "\n", encoding="utf-8")

build("index", sys.argv[2] if len(sys.argv) > 2 else None)
build("lite", sys.argv[3] if len(sys.argv) > 3 else None)
print("ok")
