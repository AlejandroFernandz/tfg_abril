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

    df["snapshot_hora"] = df["snapshot_datetime"].dt.floor("h")

    actividad = (
        df.groupby("snapshot_hora", as_index=False)
        .agg(
            eventos_activos=("id", "count"),
            carreteras_afectadas=("road", "nunique"),
            provincias_afectadas=("provincia", "nunique"),
            localidades_afectadas=("locality", "nunique"),
            tipos_evento_activos=("cause_type", "nunique"),
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
    print(f"     Media carreteras afectadas/hora: {actividad['carreteras_afectadas'].mean():,.2f}")


if __name__ == "__main__":
    main()