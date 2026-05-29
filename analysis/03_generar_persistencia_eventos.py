import os
import pandas as pd

INPUT_CSV = "analysis/datasets_generados/00_snapshots_eventos_base_completo_espanol.csv"
OUTPUT_CSV = "analysis/datasets_generados/03_persistencia_eventos.csv"

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def main():
    usecols = [
        "snapshot_datetime",
        "id",
        "start_time_fecha",
        "start_time_hora",
        "cause_type",
        "cause_detail",
        "severity",
        "road",
        "provincia",
        "locality",
        "latitude",
        "longitude",
    ]

    df = pd.read_csv(INPUT_CSV, usecols=lambda c: c in usecols)

    required_cols = ["snapshot_datetime", "id", "start_time_fecha", "start_time_hora"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Faltan columnas necesarias: {missing}")

    df["snapshot_datetime"] = pd.to_datetime(
        df["snapshot_datetime"],
        errors="coerce",
        utc=True,
    )

    df["inicio_oficial"] = pd.to_datetime(
        df["start_time_fecha"].astype(str).str.strip()
        + " "
        + df["start_time_hora"].astype(str).str.strip(),
        format="%d-%m-%Y %H:%M:%S",
        errors="coerce",
        utc=True,
    )

    df = df.dropna(subset=["snapshot_datetime", "id"])

    agg = (
        df.groupby("id", as_index=False)
        .agg(
            primera_aparicion_xml=("snapshot_datetime", "min"),
            ultima_aparicion_xml=("snapshot_datetime", "max"),
            num_snapshots_activo=("snapshot_datetime", "count"),
            inicio_oficial=("inicio_oficial", "min"),
            cause_type=("cause_type", "first"),
            cause_detail=("cause_detail", "first"),
            severity=("severity", "first"),
            road=("road", "first"),
            provincia=("provincia", "first"),
            locality=("locality", "first"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
        )
    )

    agg["duracion_observada_horas"] = (
        agg["ultima_aparicion_xml"] - agg["primera_aparicion_xml"]
    ).dt.total_seconds() / 3600

    agg["duracion_oficial_horas"] = (
        agg["ultima_aparicion_xml"] - agg["inicio_oficial"]
    ).dt.total_seconds() / 3600

    columnas_duracion = ["duracion_observada_horas", "duracion_oficial_horas"]
    agg[columnas_duracion] = agg[columnas_duracion].round(2)

    agg.loc[agg["duracion_oficial_horas"] < 0, "duracion_oficial_horas"] = pd.NA

    agg.to_csv(OUTPUT_CSV, index=False)

    print(f"[OK] CSV generado: {OUTPUT_CSV}")
    print(f"     Eventos únicos: {len(agg):,}")
    print(f"     Duración oficial media: {agg['duracion_oficial_horas'].mean():,.2f} horas")
    print(f"     Duración observada media: {agg['duracion_observada_horas'].mean():,.2f} horas")


if __name__ == "__main__":
    main()