"""Armazenamento em disco das imagens geradas por `run_python_analysis`.

Por que arquivos e não base64 no resultado da ferramenta? O resultado de uma
ferramenta entra no contexto do LLM; um PNG em base64 custaria dezenas de
milhares de tokens. Então o modelo só recebe um `image_id` curto, e o
navegador busca o PNG por HTTP (rota GET /images/{id} em main.py, acessada pelo
front-end via app/api/analysis-images/[id]/route.ts).
"""

import re
import uuid
from pathlib import Path
from typing import Optional

IMAGE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "images"
_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def save_png(png_bytes: bytes) -> str:
    """Grava o PNG e devolve o id (32 caracteres hexadecimais)."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    image_id = uuid.uuid4().hex
    (IMAGE_DIR / f"{image_id}.png").write_bytes(png_bytes)
    return image_id


def image_path(image_id: str) -> Optional[Path]:
    """Caminho do PNG, ou None se o id for inválido ou não existir.

    O id é validado contra o padrão para impedir path traversal ("../...")."""
    if not _ID_PATTERN.match(image_id):
        return None
    path = IMAGE_DIR / f"{image_id}.png"
    return path if path.is_file() else None
