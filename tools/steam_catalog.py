#!/usr/bin/env python3
"""Descubre y refresca el catálogo Steam VR cooperativo de forma reanudable.

Solo acepta las categorías oficiales de Steam 9/38/39 (cooperativo) y
53/54 (VR opcional/obligatorio). Todas las respuestas se cachean y las
peticiones se espacian para no castigar la tienda.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "steam_cache"
SEARCH_CACHE = CACHE / "search"
DETAIL_CACHE = CACHE / "details"
REVIEW_CACHE = CACHE / "reviews"
GAMES_PATH = ROOT / "src" / "data" / "games.json"
REPORT_PATH = ROOT / "data" / "steam_refresh_report.json"
CHANGE_PATH = ROOT / "data" / "steam_changes.json"
COOP_IDS = {9, 38, 39}
VR_OPTIONAL_ID = 53
VR_REQUIRED_ID = 54
USER_AGENT = "CoopQuestVR-catalog-refresh/1.0 (personal, weekly; contact via GitHub repository)"


def norm_title(value: str) -> str:
    """Misma normalización conservadora del build_dataset.py original."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    value = re.sub(r"\b(?:meta|oculus|quest|steamvr|pcvr|vr)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".part", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Client:
    def __init__(self, delay: float, max_age_days: int, offline: bool = False):
        self.delay = delay
        self.max_age = max_age_days * 86400
        self.offline = offline
        self.last_request = 0.0
        self.failures: list[dict] = []
        self.network_requests = 0

    def json(self, url: str, cache_path: Path, allow_stale_on_error: bool = True) -> tuple[dict, bool]:
        if cache_path.exists() and time.time() - cache_path.stat().st_mtime <= self.max_age:
            return json.loads(cache_path.read_text(encoding="utf-8")), True
        if self.offline:
            if cache_path.exists():
                return json.loads(cache_path.read_text(encoding="utf-8")), True
            raise RuntimeError(f"Sin caché en modo offline: {cache_path.name}")
        wait = self.delay - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                payload = json.load(response)
            self.last_request = time.monotonic()
            self.network_requests += 1
            atomic_json(cache_path, payload)
            return payload, False
        except Exception as exc:
            self.failures.append({"url": url, "error": str(exc)[:240]})
            if allow_stale_on_error and cache_path.exists():
                return json.loads(cache_path.read_text(encoding="utf-8")), True
            raise


def enumerate_candidates(client: Client) -> tuple[set[int], dict[int, dict]]:
    appids: set[int] = set()
    search_reviews: dict[int, dict] = {}
    for coop_id in sorted(COOP_IDS):
        start = 0
        while True:
            query = urllib.parse.urlencode({
                "query": "", "start": start, "count": 100, "sort_by": "_ASC",
                "category1": 998, "category2": coop_id, "vrsupport": "401,402",
                "infinite": 1, "cc": "es", "l": "spanish",
            })
            payload, _ = client.json(
                f"https://store.steampowered.com/search/results/?{query}",
                SEARCH_CACHE / f"coop_{coop_id}_{start}.json",
            )
            found = {int(x) for x in re.findall(r'data-ds-appid="(\d+)"', payload.get("results_html", ""))}
            appids.update(found)
            for block in re.findall(r'<a\s+href="[^"]+"[^>]*data-ds-appid="\d+".*?</a>', payload.get("results_html", ""), re.S):
                app = re.search(r'data-ds-appid="(\d+)"', block)
                tip = re.search(r'data-tooltip-html="([^"]+)"', block)
                if not app or not tip:
                    continue
                clean = html.unescape(tip.group(1)).replace('\xa0', ' ')
                match = re.search(r'(\d+)\s*%.*?([\d., ]+)\s+reseñas', clean, re.I | re.S)
                if match:
                    total = int(re.sub(r'\D', '', match.group(2)))
                    positive = round(total * int(match.group(1)) / 100)
                    search_reviews[int(app.group(1))] = {"total_reviews": total, "total_positive": positive}
            total = int(payload.get("total_count", 0))
            start += 100
            if not found or start >= total:
                break
    return appids, search_reviews


def details(client: Client, appid: int) -> tuple[dict | None, bool]:
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es&l=spanish"
    path = DETAIL_CACHE / f"{appid}.json"
    payload, cached = client.json(url, path)
    if cached and datetime.fromtimestamp(path.stat().st_mtime).date() == date.today():
        cached = False
    item = payload.get(str(appid), {})
    return (item.get("data") if item.get("success") else None), cached


def reviews(client: Client, appid: int) -> tuple[dict, bool]:
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all&purchase_type=all&num_per_page=0"
    path = REVIEW_CACHE / f"{appid}.json"
    payload, cached = client.json(url, path)
    if cached and datetime.fromtimestamp(path.stat().st_mtime).date() == date.today():
        cached = False
    return payload.get("query_summary", {}), cached


def parse_release(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%d %b, %Y", "%d %b %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value


def new_game(data: dict, appid: int) -> dict:
    name = data.get("name") or f"Steam App {appid}"
    return {
        "id": norm_title(name).replace(" ", "-") or f"steam-{appid}", "nombre": name,
        "estado_comercial": "proximamente" if data.get("release_date", {}).get("coming_soon") else "disponible",
        "fecha_lanzamiento_o_anuncio": parse_release(data.get("release_date", {}).get("date")),
        "tipo_fecha": "lanzamiento", "ventana_lanzamiento": None, "anos_desde_lanzamiento": None,
        "generos": [x["description"] for x in data.get("genres", [])],
        "coop": {"min_jugadores": 2, "max_jugadores": None, "segmento": "desconocido",
                 "online": "desconocido", "evidencia_limite": None, "confianza_limite": "baja"},
        "plataformas": [],
        "precio_actual": {"importe": None, "moneda": None, "fecha": None, "fuente": None,
                          "nota": "Sin precio verificable en la consulta actual."},
        "enlace_oficial_compra_ficha": None,
        "valoracion_usuarios": {"normalizada_0_10": None, "valor_original": None,
            "escala_original": None, "numero_valoraciones": None, "fuente": None, "fecha": None},
        "juego_sentado": {"valor": "desconocido", "fuente": None},
        "imprescindible": {"valor": False, "justificacion": "No marcado editorialmente como imprescindible."},
        "fuentes": [],
        "incertidumbres": ["La fuente confirma cooperativo, pero no permite fijar con seguridad el máximo de jugadores.",
                           "Compatibilidad con juego sentado no documentada en la fuente usada."],
    }


def update_game(game: dict, data: dict, review: dict, appid: int, today: str, detail_cached: bool, review_cached: bool) -> None:
    url = f"https://store.steampowered.com/app/{appid}/"
    ids = {int(x.get("id", -1)) for x in data.get("categories", [])}
    vr_mode = "obligatorio" if VR_REQUIRED_ID in ids else "opcional"
    platform = {"tipo": "SteamVR/PCVR compatible con Quest vía Link/Air Link/Steam Link",
                "modo_quest": "streaming_desde_pc", "url": url}
    game["plataformas"] = [p for p in game.get("plataformas", []) if not p.get("tipo", "").startswith("SteamVR")]
    game["plataformas"].append(platform)
    game.update(steam_appid=appid, steam_vr_modo=vr_mode, vr_modo=vr_mode,
                portada_url=data.get("header_image"), consultado_el=today)
    game["generos"] = sorted(set(game.get("generos", [])) | {x["description"] for x in data.get("genres", [])})
    game["coop_categorias_steam"] = [x["description"] for x in data.get("categories", []) if int(x.get("id", -1)) in COOP_IDS]
    game["coop"]["online"] = "si" if 38 in ids else game["coop"].get("online", "desconocido")
    price = data.get("price_overview") or {}
    if data.get("is_free"):
        amount, currency = 0.0, "EUR"
    else:
        amount = price.get("final") / 100 if price.get("final") is not None else None
        currency = price.get("currency")
    price_fresh = not detail_cached
    game["precio_actual"] = {
        "importe": amount, "moneda": currency, "fecha": today if price_fresh else game.get("precio_actual", {}).get("fecha"),
        "fuente": url,
        "nota": "Precio consultado en Steam para España." if price_fresh else "Precio procedente de caché; no se recotizó en esta ejecución.",
        "rebajado": bool(price.get("discount_percent", 0)), "descuento_porcentaje": int(price.get("discount_percent", 0)),
        "comprobado_fuente": not detail_cached, "realmente_recotizado": price_fresh,
    }
    game["incertidumbres"] = [x for x in game.get("incertidumbres", []) if "Precio no disponible" not in x]
    if amount is None and not any("precio" in x.casefold() for x in game["incertidumbres"]):
        game["incertidumbres"].append("Steam no devolvió un precio comprable para España en esta consulta.")
    total = review.get("total_reviews")
    positive = review.get("total_positive")
    rating = (positive / total * 10) if total else None
    game["valoracion_usuarios"] = {
        "normalizada_0_10": round(rating, 2) if rating is not None else None,
        "valor_original": round(positive / total * 100, 1) if total else None,
        "escala_original": "% reseñas positivas de Steam", "numero_valoraciones": total or 0,
        "fuente": url, "fecha": today if not review_cached else game.get("valoracion_usuarios", {}).get("fecha"),
    }
    game["enlace_oficial_compra_ficha"] = game.get("enlace_oficial_compra_ficha") or url
    game["fuentes"] = [s for s in game.get("fuentes", []) if "steampowered.com" not in s.get("url", "")]
    game["fuentes"].append({"tipo": "ficha_oficial_y_resenas", "url": url, "consultada_en_snapshot": today})


def classify(game: dict) -> None:
    meta = any(p.get("modo_quest", "").startswith("nativo") for p in game.get("plataformas", []))
    steam = bool(game.get("steam_appid"))
    game["clasificacion_plataforma"] = "ambos" if meta and steam else "standalone" if meta else "solo_pcvr"
    if meta and not steam:
        game["vr_modo"] = "obligatorio"
        game["dato_precio"] = "captura_meta_2026-06-06"
    elif steam:
        game["dato_precio"] = "steam_actual" if game.get("precio_actual", {}).get("realmente_recotizado") else "steam_cache"


def run(args: argparse.Namespace) -> dict:
    for folder in (SEARCH_CACHE, DETAIL_CACHE, REVIEW_CACHE):
        folder.mkdir(parents=True, exist_ok=True)
    before = json.loads(GAMES_PATH.read_text(encoding="utf-8"))
    client = Client(args.delay, args.max_age_days, args.offline)
    candidates, search_reviews = enumerate_candidates(client)
    existing = {norm_title(g["nombre"]): g for g in before["juegos"]}
    old_by_id = {g["id"]: g for g in before["juegos"]}
    passed_coop = passed_vr = 0
    refreshed: list[dict] = []
    failed_appids: list[int] = []
    for pos, appid in enumerate(sorted(candidates), 1):
        try:
            data, detail_cached = details(client, appid)
            if not data or data.get("type") != "game":
                continue
            ids = {int(x.get("id", -1)) for x in data.get("categories", [])}
            if not (ids & COOP_IDS):
                continue
            passed_coop += 1
            if not ({VR_OPTIONAL_ID, VR_REQUIRED_ID} & ids):
                continue
            passed_vr += 1
            review_path = REVIEW_CACHE / f"{appid}.json"
            if review_path.exists():
                review, review_cached = reviews(client, appid)
            elif appid in search_reviews:
                review, review_cached = search_reviews[appid], False
            else:
                review, review_cached = reviews(client, appid)
            key = norm_title(data.get("name", ""))
            game = existing.get(key) or new_game(data, appid)
            update_game(game, data, review, appid, date.today().isoformat(), detail_cached, review_cached)
            existing[key] = game
            refreshed.append(game)
        except Exception:
            failed_appids.append(appid)
        if pos % 50 == 0:
            print(json.dumps({"examined": pos, "total_candidates": len(candidates), "accepted": len(refreshed), "failed": len(failed_appids)}), flush=True)
    refreshed_ids = {g["steam_appid"] for g in refreshed}
    games = []
    for game in existing.values():
        if game.get("steam_appid") and game["steam_appid"] not in refreshed_ids:
            game["actualizacion_steam"] = "no_actualizado"
        classify(game)
        games.append(game)
    games.sort(key=lambda g: g["nombre"].casefold())
    old_ids, new_ids = set(old_by_id), {g["id"] for g in games}
    changes = {
        "generado_el": datetime.now(timezone.utc).isoformat(),
        "altas": sorted(new_ids - old_ids), "bajas": sorted(old_ids - new_ids),
        "precios": [{"id": g["id"], "antes": old_by_id[g["id"]].get("precio_actual", {}).get("importe"),
                     "despues": g.get("precio_actual", {}).get("importe")}
                    for g in games if g["id"] in old_by_id and old_by_id[g["id"]].get("precio_actual", {}).get("importe") != g.get("precio_actual", {}).get("importe")],
        "no_actualizados": failed_appids,
    }
    payload = {**before, "schema_version": "2.0.0", "generado_el": date.today().isoformat(), "total": len(games),
               "nota_actualidad": "Steam consultado para España; Meta Quest conserva la captura del 06-06-2026.", "juegos": games}
    if len(games) < max(100, int(before["total"] * 0.75)) or (failed_appids and len(failed_appids) > len(candidates) * .25):
        raise RuntimeError("Validación de seguridad: caída masiva del catálogo o errores masivos; no se publica")
    atomic_json(GAMES_PATH, payload)
    atomic_json(CHANGE_PATH, changes)
    report = {
        "consultado_el": date.today().isoformat(), "appids_examinados": len(candidates),
        "pasaron_coop": passed_coop, "pasaron_vr": passed_vr, "juegos_steam_actualizados": len(refreshed),
        "fallos": len(failed_appids), "appids_fallidos": failed_appids,
        "peticiones_red": client.network_requests, "total_final": len(games),
        "standalone": sum(g["clasificacion_plataforma"] == "standalone" for g in games),
        "solo_pcvr": sum(g["clasificacion_plataforma"] == "solo_pcvr" for g in games),
        "ambos": sum(g["clasificacion_plataforma"] == "ambos" for g in games),
        "precios_eur_recotizados": sum(g.get("precio_actual", {}).get("moneda") == "EUR" and g.get("precio_actual", {}).get("realmente_recotizado") for g in games),
        "fichas_steam_comprobadas_hoy": sum(g.get("precio_actual", {}).get("comprobado_fuente") for g in games),
        "precios_eur_disponibles": sum(g.get("precio_actual", {}).get("moneda") == "EUR" and g.get("precio_actual", {}).get("importe") is not None for g in games),
        "precios_meta_captura": sum(g.get("dato_precio") == "captura_meta_2026-06-06" for g in games),
    }
    atomic_json(REPORT_PATH, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=1.05)
    parser.add_argument("--max-age-days", type=int, default=6)
    parser.add_argument("--offline", action="store_true")
    run(parser.parse_args())
