"""Собирает прототип: встраивает CSS Leaflet и готовит версию для публикации артефактом.

python3 build.py <путь к leaflet.css> [<путь для фрагмента-артефакта>]
"""
import re, sys, pathlib
root = pathlib.Path(__file__).parent
src = (root / "src" / "index.src.html").read_text(encoding="utf-8")
css = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
full = src.replace("/*@@LEAFLET_CSS@@*/", css)
(root / "index.html").write_text(full, encoding="utf-8")
if len(sys.argv) > 2:
    head = re.search(r"<head>(.*?)</head>", full, re.S).group(1)
    head = re.sub(r'<meta charset[^>]*>\s*|<meta name="viewport"[^>]*>\s*', "", head)
    body = re.search(r"<body>(.*)</body>", full, re.S).group(1)
    # config.js с ключом Яндекса в артефакт не публикуется: там внешние скрипты запрещены, работает схема
    body = body.replace('<script src="config.js"></script>\n', "")
    pathlib.Path(sys.argv[2]).write_text(head.strip() + "\n" + body.strip() + "\n", encoding="utf-8")
print("ok")
