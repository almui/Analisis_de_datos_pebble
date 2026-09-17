import json

def generar_resumen_desde_archivo(nombre_archivo):
    total_input = 0
    total_output = 0
    total_requests = 0
    resumen_por_hora = {}

    # 1. Abrimos y leemos el archivo JSON
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            data = json.load(archivo)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{nombre_archivo}'. Asegurate de que esté en la misma carpeta.")
        return
    except json.JSONDecodeError as e:
        print(f"Error al procesar el archivo JSON: {e}")
        return

    # 2. Adaptamos a la estructura del JSON ("object": "list", "data": [...])
    if isinstance(data, dict) and "data" in data:
        lista_buckets = data["data"]
    elif isinstance(data, list):
        lista_buckets = data
    else:
        lista_buckets = [data]

    # 3. Procesamos los buckets
    for bucket in lista_buckets:
        try:
            start_time = bucket.get("start_time_iso", "").split('T')[1][:5]
            end_time = bucket.get("end_time_iso", "").split('T')[1][:5]
            time_range = f"{start_time} - {end_time}"
        except (IndexError, AttributeError):
            time_range = "Desconocido"

        bucket_requests = 0
        bucket_input = 0
        bucket_output = 0

        # Iteramos sobre "results" (si está vacío, esto no hace nada y los valores quedan en 0)
        for result in bucket.get("results", []):
            bucket_requests += result.get("num_model_requests", 0)
            bucket_input += result.get("input_tokens", 0)
            bucket_output += result.get("output_tokens", 0)
        
        # FILTRO: Si no hubo actividad en este minuto, lo saltamos para que no ensucie la tabla
        if bucket_requests == 0 and bucket_input == 0 and bucket_output == 0:
            continue
        
        # Agrupamos en el diccionario
        if time_range not in resumen_por_hora:
            resumen_por_hora[time_range] = {"requests": 0, "input": 0, "output": 0}
        
        resumen_por_hora[time_range]["requests"] += bucket_requests
        resumen_por_hora[time_range]["input"] += bucket_input
        resumen_por_hora[time_range]["output"] += bucket_output

        # Sumamos a los totales globales
        total_requests += bucket_requests
        total_input += bucket_input
        total_output += bucket_output

    # --- IMPRESIÓN DE LA TABLA ---
    if total_requests == 0:
        print("No se registraron consumos de tokens (results con datos) en este archivo.")
        return

    print("| Horario (UTC) | Peticiones | Input Tokens | Output Tokens |")
    print("| :--- | :--- | :--- | :--- |")
    
    # Ordenamos cronológicamente
    for time_range in sorted(resumen_por_hora.keys()):
        reqs = resumen_por_hora[time_range]["requests"]
        in_toks = resumen_por_hora[time_range]["input"]
        out_toks = resumen_por_hora[time_range]["output"]
        
        print(f"| {time_range} | {reqs} | {in_toks:,} | {out_toks:,} |".replace(',', '.'))

    print("\n### Resumen Total de la Conversación")
    print(f"* **Total de Input Tokens:** {total_input:,}".replace(',', '.'))
    print(f"* **Total de Output Tokens:** {total_output:,}".replace(',', '.'))
    print(f"* **Total de Mensajes (Peticiones):** {total_requests}")

# --- USO ---
#generar_resumen_desde_archivo("completions_usage_2026-09-17_2026-09-17.json")
