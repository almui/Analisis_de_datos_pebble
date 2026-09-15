from pathlib import Path
import json
import csv
from statistics import mean

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Cambiá esta ruta por la carpeta donde están tus archivos .jsonl
INPUT_FOLDER = Path(r"Archivos_output_batch")

# Archivos que va a generar
DETAIL_CSV = Path("analisis_requests.csv")
SUMMARY_TXT = Path("resumen_tokens.txt")


def analizar_jsonl(folder: Path):
    if not folder.exists():
        raise FileNotFoundError(
            f"No existe la carpeta: {folder.resolve()}\n"
            "Creala o cambiá INPUT_FOLDER en el script."
        )

    files = sorted(folder.glob("*.jsonl"))

    if not files:
        raise FileNotFoundError(
            f"No encontré archivos .jsonl en: {folder.resolve()}"
        )

    rows = []

    for file_path in files:
        with file_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(
                        f"[AVISO] JSON inválido en {file_path.name}, "
                        f"línea {line_number}: {e}"
                    )
                    continue

                response = data.get("response") or {}
                body = response.get("body") or {}
                usage = body.get("usage") or {}

                if not usage:
                    # Puede haber requests con error y sin usage
                    rows.append({
                        "archivo": file_path.name,
                        "linea": line_number,
                        "batch_request_id": data.get("id", ""),
                        "custom_id": data.get("custom_id", ""),
                        "request_id": response.get("request_id", ""),
                        "modelo": body.get("model", ""),
                        "status_code": response.get("status_code", ""),
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "cached_tokens": 0,
                        "cache_write_tokens": 0,
                        "reasoning_tokens": 0,
                        "tiene_usage": False,
                    })
                    continue

                prompt_tokens = usage.get("prompt_tokens", 0) or 0
                completion_tokens = usage.get("completion_tokens", 0) or 0
                total_tokens = usage.get("total_tokens", 0) or 0

                prompt_details = usage.get("prompt_tokens_details") or {}
                completion_details = usage.get("completion_tokens_details") or {}

                rows.append({
                    "archivo": file_path.name,
                    "linea": line_number,
                    "batch_request_id": data.get("id", ""),
                    "custom_id": data.get("custom_id", ""),
                    "request_id": response.get("request_id", ""),
                    "modelo": body.get("model", ""),
                    "status_code": response.get("status_code", ""),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cached_tokens": prompt_details.get("cached_tokens", 0) or 0,
                    "cache_write_tokens": prompt_details.get("cache_write_tokens", 0) or 0,
                    "reasoning_tokens": completion_details.get("reasoning_tokens", 0) or 0,
                    "tiene_usage": True,
                })

    return rows


def generar_csv(rows, output_path: Path):
    campos = [
        "archivo",
        "linea",
        "batch_request_id",
        "custom_id",
        "request_id",
        "modelo",
        "status_code",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cached_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "tiene_usage",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(rows)


def generar_resumen(rows, output_path: Path):
    requests_totales = len(rows)
    requests_con_usage = sum(1 for r in rows if r["tiene_usage"])

    prompt_values = [r["prompt_tokens"] for r in rows if r["tiene_usage"]]
    completion_values = [r["completion_tokens"] for r in rows if r["tiene_usage"]]
    total_values = [r["total_tokens"] for r in rows if r["tiene_usage"]]
    cached_values = [r["cached_tokens"] for r in rows if r["tiene_usage"]]
    cache_write_values = [r["cache_write_tokens"] for r in rows if r["tiene_usage"]]
    reasoning_values = [r["reasoning_tokens"] for r in rows if r["tiene_usage"]]

    prompt_total = sum(prompt_values)
    completion_total = sum(completion_values)
    total_total = sum(total_values)
    cached_total = sum(cached_values)
    cache_write_total = sum(cache_write_values)
    reasoning_total = sum(reasoning_values)

    def promedio(values):
        return mean(values) if values else 0

    # Resumen por archivo
    por_archivo = {}
    for r in rows:
        info = por_archivo.setdefault(
            r["archivo"],
            {
                "requests": 0,
                "prompt": 0,
                "completion": 0,
                "total": 0,
                "cached": 0,
                "cache_write": 0,
            },
        )

        info["requests"] += 1
        info["prompt"] += r["prompt_tokens"]
        info["completion"] += r["completion_tokens"]
        info["total"] += r["total_tokens"]
        info["cached"] += r["cached_tokens"]
        info["cache_write"] += r["cache_write_tokens"]

    lines = []

    lines.append("=" * 70)
    lines.append("RESUMEN DE TOKENS - ARCHIVOS JSONL")
    lines.append("=" * 70)
    lines.append("")

    lines.append(f"Requests analizadas: {requests_totales}")
    lines.append(f"Requests con usage:   {requests_con_usage}")
    lines.append(f"Requests sin usage:   {requests_totales - requests_con_usage}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("OUTPUT")
    lines.append("-" * 70)
    lines.append(f"Tokens output totales:     {completion_total:,}")
    lines.append(f"Promedio por request:      {promedio(completion_values):,.2f}")
    lines.append(
        f"Mínimo por request:        {min(completion_values) if completion_values else 0:,}"
    )
    lines.append(
        f"Máximo por request:        {max(completion_values) if completion_values else 0:,}"
    )
    lines.append("")

    lines.append("-" * 70)
    lines.append("INPUT")
    lines.append("-" * 70)
    lines.append(f"Tokens input totales:      {prompt_total:,}")
    lines.append(f"Promedio por request:      {promedio(prompt_values):,.2f}")
    lines.append(
        f"Mínimo por request:        {min(prompt_values) if prompt_values else 0:,}"
    )
    lines.append(
        f"Máximo por request:        {max(prompt_values) if prompt_values else 0:,}"
    )
    lines.append("")

    lines.append("-" * 70)
    lines.append("TOTAL")
    lines.append("-" * 70)
    lines.append(f"Tokens totales:             {total_total:,}")
    lines.append(f"Promedio por request:       {promedio(total_values):,.2f}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("CACHE")
    lines.append("-" * 70)
    lines.append(f"Cached tokens totales:      {cached_total:,}")
    lines.append(f"Cache write tokens totales: {cache_write_total:,}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("REASONING")
    lines.append("-" * 70)
    lines.append(f"Reasoning tokens totales:   {reasoning_total:,}")
    lines.append("")

    lines.append("=" * 70)
    lines.append("DETALLE POR ARCHIVO")
    lines.append("=" * 70)

    for filename, info in sorted(por_archivo.items()):
        lines.append("")
        lines.append(f"Archivo: {filename}")
        lines.append(f"  Requests:              {info['requests']}")
        lines.append(f"  Input tokens:          {info['prompt']:,}")
        lines.append(f"  Output tokens:         {info['completion']:,}")
        lines.append(f"  Total tokens:          {info['total']:,}")
        lines.append(f"  Cached tokens:         {info['cached']:,}")
        lines.append(f"  Cache write tokens:    {info['cache_write']:,}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("DETALLE DE CADA REQUEST")
    lines.append("=" * 70)

    for i, r in enumerate(rows, start=1):
        lines.append("")
        lines.append(f"Request #{i}")
        lines.append(f"  Archivo:             {r['archivo']}")
        lines.append(f"  Línea:               {r['linea']}")
        lines.append(f"  Custom ID:           {r['custom_id']}")
        lines.append(f"  Request ID:          {r['request_id']}")
        lines.append(f"  Modelo:              {r['modelo']}")
        lines.append(f"  Status:              {r['status_code']}")
        lines.append(f"  Input tokens:        {r['prompt_tokens']:,}")
        lines.append(f"  Output tokens:       {r['completion_tokens']:,}")
        lines.append(f"  Total tokens:        {r['total_tokens']:,}")
        lines.append(f"  Cached tokens:       {r['cached_tokens']:,}")
        lines.append(f"  Cache write tokens:  {r['cache_write_tokens']:,}")
        lines.append(f"  Reasoning tokens:    {r['reasoning_tokens']:,}")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = analizar_jsonl(INPUT_FOLDER)
    generar_csv(rows, DETAIL_CSV)
    generar_resumen(rows, SUMMARY_TXT)

    print("\n" + "=" * 60)
    print("ANÁLISIS TERMINADO")
    print("=" * 60)
    print(f"Carpeta analizada: {INPUT_FOLDER.resolve()}")
    print(f"Requests encontradas: {len(rows)}")
    print(f"CSV generado: {DETAIL_CSV.resolve()}")
    print(f"Resumen generado: {SUMMARY_TXT.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
    # Este script NO hace llamadas a OpenAI.
    # Solo lee los .jsonl que ya descargaste y analiza su campo usage.
