# Cada fila tendrá un snapshot horario, por ejemplo 
# 2025-03-13 10:00, 2025-03-13 11:00 ...

# Convierte mi script base de 2.6M de filas en una tabla mucho mas ligera donde cada fila representa
# una hora / xml agrupado (cada xml es una hora entre la fecha inicial y final)


# servirá para mostrar en Power BI:

# Evolución de eventos activos por hora
#   Eje X: snapshot_hora
#   Valores: eventos_activos
# Picos de incidencias
#   Tarjeta: MAX(eventos_activos)
# Media de incidencias activas por hora
#   Tarjeta: AVERAGE(eventos_activos)
# Heatmap hora vs día de semana
#   Eje X: hora
#   Eje Y: dia_semana
#   Valor/color: eventos_activos
# Carreteras/provincias afectadas en el tiempo
#   Línea con carreteras_afectadas
#   Línea con provincias_afectadas

# Este es el primer CSV bueno para Power BI porque reduce muchísimo el volumen y mantiene el valor temporal del histórico.


# Salida por terminal al ejecutar el script:
# [OK] CSV generado: analysis/datasets_generados/01_actividad_horaria_snapshots.csv
#      Snapshots horarios: 1,677
#      Desde: 2025-03-13 11:00:00+00:00
#      Hasta: 2025-05-22 07:00:00+00:00
#      Media eventos activos/hora: 1,583.04
#      Pico eventos activos/hora: 2,798

# Resultados
# Van desde la semana numero 11 de 2025 es del 10 al 16 de marzo (los xml comienzan el 13)
# hasta la semana numero 21 del 2025 que es del 19 al 25 de mayo (los xml terminan el 22)
import os
import pandas as pd

INPUT_CSV = "analysis/datasets_generados/00_snapshots_eventos_base_completo_espanol.csv"
OUTPUT_CSV = "analysis/datasets_generados/01_actividad_horaria_snapshots.csv"

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def main():
    df = pd.read_csv(INPUT_CSV)

    required_cols = ["snapshot_datetime", "publication_time", "id"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Faltan columnas necesarias en el CSV base: {missing}")

    df["snapshot_datetime"] = pd.to_datetime(
        df["snapshot_datetime"],
        errors="coerce",
        utc=True,
    )

    df["publication_time"] = pd.to_datetime(
        df["publication_time"],
        errors="coerce",
        utc=True,
    )

    df = df.dropna(subset=["snapshot_datetime"])

    # Redondeamos al inicio de la hora para análisis horario
    df["snapshot_hora"] = df["snapshot_datetime"].dt.floor("h")

    actividad = (
        df.groupby("snapshot_hora", as_index=False)
        .agg(
            eventos_activos=("id", "count"),
            eventos_unicos_activos=("id", "nunique"),
            carreteras_afectadas=("road", "nunique"),
            provincias_afectadas=("provincia", "nunique"),
            localidades_afectadas=("locality", "nunique"),
            publication_time_min=("publication_time", "min"),
            publication_time_max=("publication_time", "max"),
        )
        .sort_values("snapshot_hora")
    )

    actividad["fecha"] = actividad["snapshot_hora"].dt.date
    actividad["anio"] = actividad["snapshot_hora"].dt.year
    actividad["mes"] = actividad["snapshot_hora"].dt.month
    actividad["dia"] = actividad["snapshot_hora"].dt.day
    actividad["hora"] = actividad["snapshot_hora"].dt.hour
    actividad["dia_semana_num"] = actividad["snapshot_hora"].dt.dayofweek
    actividad["dia_semana"] = actividad["snapshot_hora"].dt.day_name()
    actividad["semana_anio"] = actividad["snapshot_hora"].dt.isocalendar().week
    actividad["anio_semana"] = (
        actividad["snapshot_hora"].dt.isocalendar().year.astype(str)
        + "-W"
        + actividad["snapshot_hora"].dt.isocalendar().week.astype(str).str.zfill(2)
    )
    actividad["anio_mes"] = actividad["snapshot_hora"].dt.to_period("M").astype(str)

    actividad.to_csv(OUTPUT_CSV, index=False)

    print(f"[OK] CSV generado: {OUTPUT_CSV}")
    print(f"     Snapshots horarios: {len(actividad):,}")
    print(f"     Desde: {actividad['snapshot_hora'].min()}")
    print(f"     Hasta: {actividad['snapshot_hora'].max()}")
    print(f"     Media eventos activos/hora: {actividad['eventos_activos'].mean():,.2f}")
    print(f"     Pico eventos activos/hora: {actividad['eventos_activos'].max():,}")


if __name__ == "__main__":
    main()