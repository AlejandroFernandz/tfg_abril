# Genera un csv para usar segmentadores/filtros en pbi
# cause_type, cause_detail, probability, severity, road, provincia, hora, dia_semana

import os
import pandas as pd

INPUT_CSV = "analysis/datasets_generados/00_snapshots_eventos_base_completo_espanol.csv"
OUTPUT_CSV = "analysis/datasets_generados/02_snapshot_detallado_ligero.csv"

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def main():
    df = pd.read_csv(INPUT_CSV)

    required_cols = ["snapshot_datetime", "id"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Faltan columnas necesarias en el CSV base: {missing}")

    df["snapshot_datetime"] = pd.to_datetime(
        df["snapshot_datetime"],
        errors="coerce",
        utc=True,
    )

    df = df.dropna(subset=["snapshot_datetime", "id"])

    df["snapshot_hora"] = df["snapshot_datetime"].dt.floor("h")
    df["fecha"] = df["snapshot_hora"].dt.date
    df["anio"] = df["snapshot_hora"].dt.year
    df["mes"] = df["snapshot_hora"].dt.month
    df["dia"] = df["snapshot_hora"].dt.day
    df["hora"] = df["snapshot_hora"].dt.hour
    df["dia_semana_num"] = df["snapshot_hora"].dt.dayofweek
    df["dia_semana"] = df["snapshot_hora"].dt.day_name()
    df["semana_anio"] = df["snapshot_hora"].dt.isocalendar().week
    df["anio_semana"] = (
        df["snapshot_hora"].dt.isocalendar().year.astype(str)
        + "-W"
        + df["snapshot_hora"].dt.isocalendar().week.astype(str).str.zfill(2)
    )
    df["anio_mes"] = df["snapshot_hora"].dt.to_period("M").astype(str)

    keep_columns = [
        "snapshot_hora",
        "fecha",
        "anio",
        "mes",
        "dia",
        "hora",
        "dia_semana_num",
        "dia_semana",
        "semana_anio",
        "anio_semana",
        "anio_mes",
        "id",
        "cause_type",
        "cause_detail",
        "probability",
        "severity",
        "road",
        "provincia",
        "locality",
        "latitude",
        "longitude",
    ]

    keep_columns = [col for col in keep_columns if col in df.columns]

    df_ligero = df[keep_columns].copy()

    # Limpieza básica
    for col in ["cause_type", "cause_detail", "probability", "severity", "road", "provincia", "locality"]:
        if col in df_ligero.columns:
            df_ligero[col] = df_ligero[col].fillna("Sin dato")

    df_ligero.to_csv(OUTPUT_CSV, index=False)

    print(f"[OK] CSV generado: {OUTPUT_CSV}")
    print(f"     Filas exportadas: {len(df_ligero):,}")
    print(f"     Columnas exportadas: {len(df_ligero.columns):,}")
    print(f"     Desde: {df_ligero['snapshot_hora'].min()}")
    print(f"     Hasta: {df_ligero['snapshot_hora'].max()}")


if __name__ == "__main__":
    main()