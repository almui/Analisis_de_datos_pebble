import json
def calcular_costo_simulacion_batch(
    total_parejas_a_simular: int,
    tokens_input_totales_por_pareja: int = 485192,
    tokens_cache_por_pareja: int = 409591,
    tokens_output_por_pareja: int = 4004,
    precio_input_batch: float = 1.00,
    precio_cache_batch: float = 0.10,
    precio_output_batch: float = 6.00
) -> dict:
    """
    Calcula el costo de correr la simulación inicial de gemelos digitales en modo Batch.
    Los valores por defecto corresponden al ciclo de 40 peticiones de 1 pareja.
    """
    
    # 1. Desglose de tokens por pareja
    tokens_uncached_por_pareja = tokens_input_totales_por_pareja - tokens_cache_por_pareja
    
    # 2. Costo de simular UNA pareja (40 mensajes)
    costo_uncached = (tokens_uncached_por_pareja / 1_000_000) * precio_input_batch
    costo_cache = (tokens_cache_por_pareja / 1_000_000) * precio_cache_batch
    costo_output = (tokens_output_por_pareja / 1_000_000) * precio_output_batch
    
    costo_por_pareja = costo_uncached + costo_cache + costo_output
    
    # 3. Costo Total del Lote (Batch)
    costo_total = total_parejas_a_simular * costo_por_pareja
    
    return {
        "metricas_unitarias": {
            "costo_por_pareja_usd": round(costo_por_pareja, 4)
        },
        "totales_simulacion": {
            "parejas_simuladas": total_parejas_a_simular,
            "costo_total_usd": round(costo_total, 2)
        }
    }
def calcular_presupuesto_llm(
    num_usuarios: int,
    msgs_por_usuario_dia: int,
    dias: int,
    precio_input_1m: float,
    precio_output_1m: float,
    avg_input_tokens: int = 11177,
    avg_output_tokens: int = 98,
    porcentaje_cache: float = 0.0,
    precio_cache_1m: float = 0.20
) -> dict:
    """
    Calcula el consumo de tokens y el costo total estimado en USD para correr un LLM.
    
    Parametros:
      - num_usuarios: Cantidad de usuarios activos (ej. 60 o 100).
      - msgs_por_usuario_dia: Promedio de mensajes enviados por usuario al dia.
      - dias: Duracion de la prueba o periodo en dias (ej. 14).
      - precio_input_1m: Precio por millon de tokens de Input en USD.
      - precio_output_1m: Precio por millon de tokens de Output en USD.
      - avg_input_tokens: Tokens de Input promedio por mensaje (default: 11177).
      - avg_output_tokens: Tokens de Output promedio por mensaje (default: 98).
      - porcentaje_cache: Float entre 0.0 y 1.0 indicando que proporcion del input entra en cache (ej. 0.80 para 80%).
      - precio_cache_1m: Precio por millon de tokens de Input en cache (default: 0.20).
    """
    # 1. Desglose de tokens por mensaje con/sin cache
    tokens_input_normales = avg_input_tokens * (1.0 - porcentaje_cache)
    tokens_input_cache = avg_input_tokens * porcentaje_cache

    # 2. Costo unitario por mensaje
    costo_input_normal = (tokens_input_normales / 1_000_000) * precio_input_1m
    costo_input_cache = (tokens_input_cache / 1_000_000) * precio_cache_1m
    costo_output = (avg_output_tokens / 1_000_000) * precio_output_1m
    
    costo_por_mensaje = costo_input_normal + costo_input_cache + costo_output

    # 3. Métricas de volumen
    mensajes_diarios = num_usuarios * msgs_por_usuario_dia
    mensajes_totales = mensajes_diarios * dias

    # 4. Totales
    total_input_tokens = mensajes_totales * avg_input_tokens
    total_output_tokens = mensajes_totales * avg_output_tokens
    costo_diario = mensajes_diarios * costo_por_mensaje
    costo_total = mensajes_totales * costo_por_mensaje

    return {
        "volumen": {
            "usuarios": num_usuarios,
            "dias": dias,
            "mensajes_diarios": mensajes_diarios,
            "mensajes_totales": mensajes_totales,
        },
        "tokens": {
            "input_totales": total_input_tokens,
            "output_totales": total_output_tokens,
            "tokens_totales": total_input_tokens + total_output_tokens,
        },
        "costos_usd": {
            "costo_por_mensaje": round(costo_por_mensaje, 5),
            "costo_diario": round(costo_diario, 2),
            "costo_total": round(costo_total, 2),
        }
    }


# ==========================================
# EJEMPLO DE USO (gpt-5.6-terra por 14 días)
# ==========================================

# Caso Standard (Sin Prompt Caching)
resultado_standard = calcular_presupuesto_llm(
    num_usuarios=60,
    msgs_por_usuario_dia=50,  # Perfil Activo
    dias=14,
    precio_input_1m=2.00,
    precio_output_1m=12.00
)
def main():
    # Si corres la matriz completa de 30 mujeres x 30 hombres (900 parejas)
    resultado_30x30 = calcular_costo_simulacion_batch(total_parejas_a_simular=900)
    print(f"Costo Simulación completa 30x30 (900 parejas): ${resultado_30x30['totales_simulacion']['costo_total_usd']} USD")

    # Si corres la matriz completa de 50 mujeres x 50 hombres (2500 parejas)
    resultado_50x50 = calcular_costo_simulacion_batch(total_parejas_a_simular=2500)
    print(f"Costo Simulación completa 50x50 (2500 parejas): ${resultado_50x50['totales_simulacion']['costo_total_usd']} USD")
    
# Caso Optimizado (Con 80% de Prompt Caching)
resultado_cache = calcular_presupuesto_llm(
    num_usuarios=100,
    msgs_por_usuario_dia=50,
    dias=14,
    precio_input_1m=2.00,
    precio_output_1m=12.00,

)

print("Costo de la simulacion (una persona con un gemelo) con 60 usuarios en 14 Días:", resultado_standard["costos_usd"]["costo_total"], "USD")
print("Costo de la simulacion (una persona con un gemelo) con 100 usuarios en 14 Días:", resultado_cache["costos_usd"]["costo_total"], "USD")


if __name__ == "__main__":
    main()
