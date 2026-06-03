# Cada fila que genera este csv es un evento de trafico situado a 3 kms o menos de un estadio de futbol en el que hay un partido
import math
import os
import pandas as pd

INPUT_EVENTOS = "analysis/datasets_generados/03_persistencia_eventos.csv"
INPUT_PARTIDOS = "analysis/datasets_generados/04_partidos_estadios_filtrados.csv"
OUTPUT_CSV = "analysis/datasets_generados/05_eventos_cercanos_estadios.csv"
RADIO_KM = 1.5

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def haversine_km(lat1, lon1, lat2, lon2):
    radio_tierra_km = 6371.0
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radio_tierra_km * c


def main():
    eventos_cols = [
        "id",
        "latitude",
        "longitude",
        "latitude_ini",
        "longitude_ini",
        "cause_type",
        "cause_detail",
        "severity",
        "road",
        "provincia",
        "locality",
        "inicio_oficial",
        "ultima_aparicion_xml",
        "duracion_oficial_horas",
        "duracion_observada_horas",
        "num_snapshots_activo",
    ]

    eventos = pd.read_csv(
        INPUT_EVENTOS,
        usecols=lambda c: c in eventos_cols,
    )
    partidos = pd.read_csv(INPUT_PARTIDOS)

    # Se corrige la validación usando los nombres reales del archivo 04
    required_partidos = ["Estadio", "Latitud_Estadio", "Longitud_Estadio"]
    missing_partidos = [
        c for c in required_partidos if c not in partidos.columns
    ]
    if missing_partidos:
        raise ValueError(
            f"Faltan columnas en partidos/estadios: {missing_partidos}"
        )

    # Convertir todas las coordenadas originales a numéricas
    for col in ["latitude", "longitude", "latitude_ini", "longitude_ini"]:
        if col in eventos.columns:
            eventos[col] = pd.to_numeric(eventos[col], errors="coerce")

    partidos["Latitud_Estadio"] = pd.to_numeric(partidos["Latitud_Estadio"], errors="coerce")
    partidos["Longitud_Estadio"] = pd.to_numeric(partidos["Longitud_Estadio"], errors="coerce")

    # UNIFICACIÓN: Creamos las nuevas columnas 'latitud_evento' y 'longitud_evento'
    lat_ini = eventos["latitude_ini"] if "latitude_ini" in eventos.columns else pd.Series(dtype='float64')
    lon_ini = eventos["longitude_ini"] if "longitude_ini" in eventos.columns else pd.Series(dtype='float64')

    eventos["latitud_evento"] = eventos["latitude"].combine_first(lat_ini)
    eventos["longitud_evento"] = eventos["longitude"].combine_first(lon_ini)

    # Limpieza de filas sin las nuevas coordenadas unificadas o datos de estadios vacíos
    eventos = eventos.dropna(subset=["latitud_evento", "longitud_evento"])
    partidos = partidos.dropna(subset=["Estadio", "Latitud_Estadio", "Longitud_Estadio"])

    # Eliminamos las columnas de coordenadas antiguas de eventos para dejar el dataset limpio
    columnas_a_borrar = ["latitude", "longitude", "latitude_ini", "longitude_ini"]
    eventos = eventos.drop(columns=columnas_a_borrar, errors="ignore")

    # Estadios únicos usando las columnas corregidas
    estadios = (
        partidos[["Estadio", "Latitud_Estadio", "Longitud_Estadio"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    resultados = []
    for _, evento in eventos.iterrows():
        lat_evento = evento["latitud_evento"]
        lon_evento = evento["longitud_evento"]

        for _, estadio in estadios.iterrows():
            distancia = haversine_km(
                lat_evento,
                lon_evento,
                estadio["Latitud_Estadio"],
                estadio["Longitud_Estadio"],
            )

            if distancia <= RADIO_KM:
                fila = evento.to_dict()
                fila["Estadio"] = estadio["Estadio"]
                # Mapeo final a minúsculas en el diccionario de salida
                fila["latitud_estadio"] = estadio["Latitud_Estadio"]
                fila["longitud_estadio"] = estadio["Longitud_Estadio"]
                fila["distancia_km"] = round(distancia, 3)
                fila["radio_km"] = RADIO_KM
                resultados.append(fila)

    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"[OK] CSV generado: {OUTPUT_CSV}")
    print(f" Radio usado: {RADIO_KM} km")
    print(f" Estadios analizados: {len(estadios):,}")
    print(f" Eventos con coordenadas: {len(eventos):,}")
    print(f" Eventos cercanos encontrados: {len(df_resultado):,}")

    if not df_resultado.empty:
        print(
            f" Estadios con eventos cercanos: {df_resultado['Estadio'].nunique():,}"
        )
        print(
            f" Distancia media: {df_resultado['distancia_km'].mean():.2f} km"
        )


if __name__ == "__main__":
    main()
