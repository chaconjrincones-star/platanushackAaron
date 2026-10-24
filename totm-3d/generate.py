#!/usr/bin/env python3
"""Genera modelos 3D de TOTM con la API de Meshy.

Uso:
  python generate.py image refs/totm-esfera-render.png --name render-jade
  python generate.py preview --prompt forma --name esfera-v1
  python generate.py refine <preview_task_id> --texture jade --name esfera-v1-jade
  python generate.py status <task_id> [--download --name <variante>]

El token se lee de MESHY_API_KEY (variable de entorno o .env). Nunca se imprime.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://api.meshy.ai"
TEXT_TO_3D = "/openapi/v2/text-to-3d"
IMAGE_TO_3D = "/openapi/v1/image-to-3d"
BALANCE = "/openapi/v1/balance"

MAX_PROMPT = 800
POLL_SECONDS = 5
TIMEOUT_SECONDS = 15 * 60
MAX_RETRIES = 6
TARGET_FORMATS = ["glb", "stl"]


class MeshyError(Exception):
    pass


def fail(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_key():
    load_dotenv(ROOT / ".env")
    load_dotenv()  # .env del directorio actual, si existe
    key = os.getenv("MESHY_API_KEY", "").strip()
    if not key or key == "tu_token_aqui":
        fail("falta MESHY_API_KEY. Defínela en el entorno o en totm-3d/.env (ver .env.example).")
    return key


class Meshy:
    def __init__(self, key):
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {key}"

    def request(self, method, path, **kwargs):
        delay = 2
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._session.request(method, BASE_URL + path, timeout=60, **kwargs)
            except requests.RequestException as exc:
                # El mensaje de requests no incluye headers, así que es seguro mostrarlo.
                if attempt == MAX_RETRIES - 1:
                    raise MeshyError(f"red: {exc.__class__.__name__}")
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", delay))
                print(f"\n429: límite de uso, reintento en {wait}s...", file=sys.stderr)
                time.sleep(wait)
                delay *= 2
                continue
            if resp.status_code == 401:
                fail("401: token inválido. Revisa MESHY_API_KEY.")
            if resp.status_code == 402:
                fail("402: sin créditos en Meshy. Recarga la cuenta antes de seguir.")
            if resp.status_code >= 400:
                raise MeshyError(f"{resp.status_code}: {_error_message(resp)}")
            return resp.json()
        raise MeshyError("429: se agotaron los reintentos")

    def balance(self):
        try:
            return self.request("GET", BALANCE).get("balance")
        except MeshyError:
            return None


def _error_message(resp):
    try:
        return resp.json().get("message", resp.text[:300])
    except ValueError:
        return resp.text[:300]


def load_prompts():
    with open(ROOT / "prompts.json", encoding="utf-8") as f:
        return json.load(f)


def resolve_prompt(kind, value):
    """Acepta un nombre de prompts.json o un texto literal."""
    prompts = load_prompts()[kind]
    text = prompts.get(value, value)
    if value not in prompts and len(value.split()) < 4:
        fail(f"prompt '{value}' no existe en prompts.json[{kind}]. Opciones: {', '.join(prompts)}")
    if len(text) > MAX_PROMPT:
        fail(f"el prompt '{value}' tiene {len(text)} caracteres (máximo {MAX_PROMPT}).")
    return text


def image_data_uri(path):
    p = Path(path)
    if not p.is_file():
        fail(f"no existe la imagen {path}")
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    if mime not in ("image/png", "image/jpeg"):
        fail("Meshy acepta solo .png o .jpg")
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def poll(api, endpoint, task_id):
    start = time.time()
    while True:
        task = api.request("GET", f"{endpoint}/{task_id}")
        status, progress = task.get("status"), task.get("progress", 0)
        elapsed = int(time.time() - start)
        print(f"\r{task_id}  {status:<11} {progress:>3}%  {elapsed // 60:02d}:{elapsed % 60:02d}", end="", flush=True)
        if status in ("SUCCEEDED", "FAILED", "CANCELED"):
            print()
            return task
        if elapsed > TIMEOUT_SECONDS:
            print()
            fail(f"tiempo máximo agotado. Consulta luego con: python generate.py status {task_id}")
        time.sleep(POLL_SECONDS)


def download(url, dest):
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)


def save_outputs(task, name, endpoint, params, credits_before, api):
    folder = ROOT / "models" / f"{date.today().isoformat()}_{name}"
    folder.mkdir(parents=True, exist_ok=True)

    files = []
    for fmt, url in (task.get("model_urls") or {}).items():
        if url and fmt in TARGET_FORMATS:
            download(url, folder / f"model.{fmt}")
            files.append(f"model.{fmt}")
    if task.get("thumbnail_url"):
        download(task["thumbnail_url"], folder / "thumbnail.png")
        files.append("thumbnail.png")

    credits_after = api.balance()
    used = None
    if credits_before is not None and credits_after is not None:
        used = credits_before - credits_after

    record = {
        "name": name,
        "task_id": task.get("id"),
        "endpoint": endpoint,
        "params": params,
        "status": task.get("status"),
        "credits_before": credits_before,
        "credits_after": credits_after,
        "credits_used": used,
        "files": files,
        "texture_urls": task.get("texture_urls"),
        "task_error": task.get("task_error"),
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (folder / "task.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"guardado en {folder.relative_to(ROOT)}  ({', '.join(files) or 'sin archivos'})")
    if used is not None:
        print(f"créditos usados: {used}  (quedan {credits_after})")


def run_task(api, endpoint, payload, name, logged_params):
    credits_before = api.balance()
    task_id = api.request("POST", endpoint, json=payload)["result"]
    print(f"tarea creada: {task_id}")
    task = poll(api, endpoint, task_id)
    if task["status"] != "SUCCEEDED":
        err = (task.get("task_error") or {}).get("message", "")
        print(f"la tarea terminó en {task['status']}. {err}".strip(), file=sys.stderr)
    save_outputs(task, name, endpoint, logged_params, credits_before, api)
    return task


def cmd_image(api, args):
    texture = resolve_prompt("texture", args.texture)
    payload = {
        "image_url": image_data_uri(args.image),
        "ai_model": "latest",
        "topology": "quad",
        "should_remesh": True,
        "target_polycount": args.polycount,
        "should_texture": True,
        "enable_pbr": True,
        "texture_prompt": texture,
        "target_formats": TARGET_FORMATS,
    }
    logged = {**payload, "image_url": args.image, "texture_name": args.texture}
    run_task(api, IMAGE_TO_3D, payload, args.name, logged)


def cmd_preview(api, args):
    payload = {
        "mode": "preview",
        "prompt": resolve_prompt("shape", args.prompt),
        "ai_model": "latest",
        "topology": "quad",
        "should_remesh": True,
        "target_polycount": args.polycount,
        "origin_at": "bottom",
        "target_formats": TARGET_FORMATS,
    }
    run_task(api, TEXT_TO_3D, payload, args.name, {**payload, "prompt_name": args.prompt})


def cmd_refine(api, args):
    payload = {
        "mode": "refine",
        "preview_task_id": args.preview_task_id,
        "enable_pbr": True,
        "texture_resolution": "2k",
        "texture_prompt": resolve_prompt("texture", args.texture),
        "target_formats": TARGET_FORMATS,
    }
    run_task(api, TEXT_TO_3D, payload, args.name, {**payload, "texture_name": args.texture})


def cmd_status(api, args):
    task, endpoint = None, None
    for ep in (TEXT_TO_3D, IMAGE_TO_3D):
        try:
            task, endpoint = api.request("GET", f"{ep}/{args.task_id}"), ep
            break
        except MeshyError:
            continue
    if task is None:
        fail(f"no encontré la tarea {args.task_id} en text-to-3d ni en image-to-3d")

    print(json.dumps({k: task.get(k) for k in ("id", "status", "progress", "model_urls", "thumbnail_url", "task_error")},
                     indent=2, ensure_ascii=False))
    if args.download:
        if task.get("status") != "SUCCEEDED":
            fail("solo se pueden descargar tareas SUCCEEDED")
        save_outputs(task, args.name or args.task_id[:8], endpoint, {"recovered_with": "status"}, None, api)


def main():
    parser = argparse.ArgumentParser(description="Modelos 3D de TOTM con Meshy")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("image", help="image-to-3d desde una referencia")
    p.add_argument("image")
    p.add_argument("--name", required=True)
    p.add_argument("--texture", default="jade")
    p.add_argument("--polycount", type=int, default=30000)

    p = sub.add_parser("preview", help="text-to-3d, malla sin textura")
    p.add_argument("--prompt", default="forma", help="nombre en prompts.json o texto literal")
    p.add_argument("--name", required=True)
    p.add_argument("--polycount", type=int, default=30000)

    p = sub.add_parser("refine", help="textura sobre una preview SUCCEEDED")
    p.add_argument("preview_task_id")
    p.add_argument("--texture", default="jade")
    p.add_argument("--name", required=True)

    p = sub.add_parser("status", help="consulta una tarea existente")
    p.add_argument("task_id")
    p.add_argument("--download", action="store_true")
    p.add_argument("--name")

    args = parser.parse_args()
    api = Meshy(load_key())
    commands = {"image": cmd_image, "preview": cmd_preview, "refine": cmd_refine, "status": cmd_status}
    try:
        commands[args.cmd](api, args)
    except MeshyError as exc:
        fail(str(exc))
    except KeyboardInterrupt:
        print("\ninterrumpido. La tarea sigue en Meshy; recupérala con 'status <task_id> --download'.")
        sys.exit(130)


if __name__ == "__main__":
    main()
