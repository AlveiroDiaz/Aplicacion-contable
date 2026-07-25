import json
import logging
import re
import time
from decimal import Decimal
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.uvt import UVTValue

logger = logging.getLogger(__name__)

SIMULATED_UVT_BY_YEAR = {
    2023: Decimal("56000"),
    2024: Decimal("60000"),
    2025: Decimal("64000"),
    2026: Decimal("69000"),
}

DEFAULT_SIMULATED_UVT = Decimal("65000")
REFRESH_INTERVAL_DAYS = 30


def normalize_uvt_string(raw: str) -> Decimal:
    raw = raw.strip()
    raw = raw.replace(" ", "")
    raw = raw.replace("$", "")
    raw = raw.replace("COP", "")
    raw = raw.replace("pesos", "")
    raw = raw.replace("%", "")
    raw = raw.strip()
    if not raw:
        raise ValueError("Valor de UVT vacío")

    numeric = re.sub(r"[^0-9,\.]+", "", raw)
    if numeric.count(",") > 1 and numeric.count(".") == 0:
        numeric = numeric.replace(".", "")
    if numeric.count(",") == 1 and numeric.count(".") > 0:
        numeric = numeric.replace(".", "")
        numeric = numeric.replace(",", ".")
    numeric = numeric.replace(",", ".")
    return Decimal(numeric)


def fetch_uvt_external(anio: int) -> Decimal:
    source = settings.UVT_SOURCE_URL
    if not source:
        raise RuntimeError("No hay fuente externa configurada para UVT")

    url = source.format(year=anio) if "{year}" in source else f"{source}?year={anio}"
    request = Request(url, headers={"User-Agent": "UVTFetcher/1.0"})

    last_error = None
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=10) as response:
                content = response.read().decode("utf-8", errors="ignore")
                try:
                    payload = json.loads(content)
                    for key in ("valor_uvt", "uvt", "valor", "UVT"):
                        if key in payload:
                            return normalize_uvt_string(str(payload[key]))
                except ValueError:
                    pass

                match = re.search(r"([0-9][0-9\.,]+)", content)
                if match:
                    return normalize_uvt_string(match.group(1))

                raise ValueError("No se pudo extraer el valor de UVT de la respuesta externa")
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            last_error = exc
            logger.warning("Intento %d de fetch UVT falló para %s: %s", attempt, url, exc)
            if attempt < 3:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"No se pudo obtener UVT desde la fuente externa: {last_error}")


def get_simulated_uvt(anio: int) -> Decimal:
    return SIMULATED_UVT_BY_YEAR.get(anio, DEFAULT_SIMULATED_UVT)


def get_uvt_row(db, anio: int):
    return db.query(UVTValue).filter(UVTValue.anio == anio).first()


def persist_uvt(db, anio: int, valor: Decimal, fuente: str, status: str, error: str | None = None):
    row = get_uvt_row(db, anio)
    if not row:
        row = UVTValue(
            anio=anio,
            valor=valor,
            fuente=fuente,
            status=status,
            error=error,
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(row)
    else:
        row.valor = valor
        row.fuente = fuente
        row.status = status
        row.error = error
        row.fetched_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def refresh_uvt(db, anio: int):
    try:
        valor = fetch_uvt_external(anio)
        return persist_uvt(db, anio, valor, fuente="EXTERNA", status="SUCCESS", error=None)
    except Exception as exc:
        error_text = str(exc)
        logger.error("Error al refrescar UVT para %d: %s", anio, error_text)
        cached = get_uvt_row(db, anio)
        if cached:
            return persist_uvt(db, anio, cached.valor, fuente="EXTERNA-FALLIDA", status="FAILED", error=error_text)
        fallback = get_simulated_uvt(anio)
        return persist_uvt(db, anio, fallback, fuente="SIMULADA", status="FAILED", error=error_text)


def refresh_uvt_background(anio: int):
    db = SessionLocal()
    try:
        refresh_uvt(db, anio)
    finally:
        db.close()


def get_uvt(db, anio: int, background_task=None):
    row = get_uvt_row(db, anio)
    if row:
        now = datetime.now(timezone.utc)
        age_days = (now - row.fetched_at).days if row.fetched_at else REFRESH_INTERVAL_DAYS + 1
        if age_days >= REFRESH_INTERVAL_DAYS and background_task is not None:
            background_task.add_task(refresh_uvt_background, anio)
        return row

    fallback = get_simulated_uvt(anio)
    row = persist_uvt(db, anio, fallback, fuente="SIMULADA", status="PENDING", error="Valor inicial simulado")
    if background_task is not None:
        background_task.add_task(refresh_uvt_background, anio)
    return row
