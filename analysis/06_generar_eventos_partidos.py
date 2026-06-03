import os
import pandas as pd

INPUT_EVENTOS_CERCANOS = "analysis/datasets_generados/05_eventos_cercanos_estadios.csv"
INPUT_PARTIDOS = "analysis/datasets_generados/04_partidos_estadios_filtrados.csv"
OUTPUT_CSV = "analysis/datasets_generados/06_eventos_partidos_v2.csv"

HORAS_PRE = 3
DURACION_PARTIDO_HORAS = 2
HORAS_POST = 3

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def normalizar_datetime_sin_tz(serie):
    return pd.to_datetime(
        serie,
        errors="coerce",
        utc=True
    ).dt.tz_localize(None)


def hay_interseccion(inicio_evento, fin_evento, inicio_ventana, fin_ventana):
    return inicio_evento <= fin_ventana and fin_evento >= inicio_ventana


def main():
    eventos = pd.read_csv(INPUT_EVENTOS_CERCANOS)
    partidos = pd.read_csv(INPUT_PARTIDOS)

    required_eventos = [
        "id",
        "Estadio",
        "inicio_oficial",
        "ultima_aparicion_xml",
        "distancia_km",
    ]

    required_partidos = [
        "fecha_hora_partido",
        "Div",
        "HomeTeam",
        "AwayTeam",
        "Estadio",
        "Importancia",
    ]

    missing_eventos = [c for c in required_eventos if c not in eventos.columns]
    missing_partidos = [c for c in required_partidos if c not in partidos.columns]

    if missing_eventos:
        raise ValueError(f"Faltan columnas en eventos cercanos: {missing_eventos}")

    if missing_partidos:
        raise ValueError(f"Faltan columnas en partidos: {missing_partidos}")

    eventos["inicio_oficial"] = normalizar_datetime_sin_tz(eventos["inicio_oficial"])
    eventos["ultima_aparicion_xml"] = normalizar_datetime_sin_tz(eventos["ultima_aparicion_xml"])

    partidos["fecha_hora_partido"] = pd.to_datetime(
        partidos["fecha_hora_partido"],
        errors="coerce"
    )
    partidos["fecha_hora_partido"] = partidos["fecha_hora_partido"].dt.tz_localize(None)

    eventos = eventos.dropna(subset=["inicio_oficial", "ultima_aparicion_xml", "Estadio"])
    partidos = partidos.dropna(subset=["fecha_hora_partido", "Estadio"])

    # Se adaptan los nombres del archivo partidos (04_xxx.csv) para el cruce
    df = eventos.merge(
        partidos[
            [
                "Div",
                "fecha_hora_partido",
                "HomeTeam",
                "AwayTeam",
                "Estadio",
                "Importancia",
                "Latitud_Estadio",
                "Longitud_Estadio",
            ]
        ],
        on="Estadio",
        how="inner",
        suffixes=("_evento", "_partido"),
    )

    resultados = []

    for _, row in df.iterrows():
        inicio_evento = row["inicio_oficial"]
        fin_evento = row["ultima_aparicion_xml"]
        inicio_partido = row["fecha_hora_partido"]

        ventanas = [
            (
                "Pre-Partido",
                inicio_partido - pd.Timedelta(hours=HORAS_PRE),
                inicio_partido,
            ),
            (
                "Durante-Partido",
                inicio_partido,
                inicio_partido + pd.Timedelta(hours=DURACION_PARTIDO_HORAS),
            ),
            (
                "Post-Partido",
                inicio_partido + pd.Timedelta(hours=DURACION_PARTIDO_HORAS),
                inicio_partido + pd.Timedelta(hours=DURACION_PARTIDO_HORAS + HORAS_POST),
            ),
        ]

        for fase, inicio_ventana, fin_ventana in ventanas:
            if hay_interseccion(inicio_evento, fin_evento, inicio_ventana, fin_ventana):
                fila = row.to_dict()
                fila["fase_partido"] = fase
                fila["ventana_inicio"] = inicio_ventana
                fila["ventana_fin"] = fin_ventana
                fila["partido"] = f"{row['HomeTeam']} vs {row['AwayTeam']}"

                fila["horas_desde_inicio_partido"] = (
                    inicio_evento - inicio_partido
                ).total_seconds() / 3600

                fila["horas_pre"] = HORAS_PRE
                fila["duracion_partido_estimada_horas"] = DURACION_PARTIDO_HORAS
                fila["horas_post"] = HORAS_POST

                resultados.append(fila)

    resultado = pd.DataFrame(resultados)

    # Se actualizan las columnas geográficas finales para usar los nombres normalizados
    keep_columns = [
        "Div",
        "fecha_hora_partido",
        "partido",
        "HomeTeam",
        "AwayTeam",
        "Estadio",
        "Importancia",
        "fase_partido",
        "ventana_inicio",
        "ventana_fin",
        "id",
        "inicio_oficial",
        "ultima_aparicion_xml",
        "horas_desde_inicio_partido",
        "distancia_km",
        "cause_type",
        "cause_detail",
        "severity",
        "road",
        "provincia",
        "locality",
        "duracion_oficial_horas",
        "duracion_observada_horas",
        "num_snapshots_activo",
        "latitud_evento",      # Nueva columna unificada
        "longitud_evento",     # Nueva columna unificada
        "latitud_estadio",     # Nueva columna unificada
        "longitud_estadio",    # Nueva columna unificada
        "latitude_fin",        
        "longitude_fin",
        "horas_pre",
        "duracion_partido_estimada_horas",
        "horas_post",
    ]

    keep_columns = [c for c in keep_columns if c in resultado.columns]
    resultado = resultado[keep_columns].copy()

    if not resultado.empty:
        resultado = resultado.sort_values(
            ["fecha_hora_partido", "Estadio", "fase_partido", "distancia_km"]
        )

    resultado.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"[OK] CSV generado: {OUTPUT_CSV}")
    print(f"     Filas evento-fase asociadas: {len(resultado):,}")

    if not resultado.empty:
        print(f"     Eventos únicos asociados: {resultado['id'].nunique():,}")
        print(f"     Partidos con eventos asociados: {resultado['partido'].nunique():,}")
        print(f"     Estadios con eventos asociados: {resultado['Estadio'].nunique():,}")
        print("     Eventos por fase:")
        print(resultado["fase_partido"].value_counts().to_string())
        print(f"     Distancia media: {resultado['distancia_km'].mean():.2f} km")


if __name__ == "__main__":
    main()
