# Saca el csv base con los eventos traducidos y normalizados para sacar el resto de analisis derivados
# Es un dataset raw que contiene todos los eventos de los xml
# Los datos van desde 13 marzo 2025 → 22 mayo 2025, es decir, 71 dias, descargados en intervalos de una hora
# Cada fila es un evento activo en el momento del snapshot, por lo que un mismo evento puede aparecer en varios snapshots si se mantiene activo
# El csv resultante tiene 2.654.760 filas, que se reducen a 267.038 eventos únicos por id, lo que indica que muchos eventos se mantienen activos durante varios snapshots

import os
import glob
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from analysis.parser_antiguo import parse_datex_historico_enriquecido


def normalizar_texto(valor):
    if pd.isna(valor):
        return None

    texto = (
        str(valor)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ñ", "n")
    )

    if "," in texto:
        partes = [p.strip() for p in texto.split(",")]
        texto = " ".join(reversed(partes))

    return texto.title()


def main():
    input_dir = "data/xml_descargados"
    output_dir = "analysis/datasets_generados"
    os.makedirs(output_dir, exist_ok=True)

    xml_paths = sorted(glob.glob(os.path.join(input_dir, "*.xml")))
    if not xml_paths:
        raise FileNotFoundError(f"No se encontraron XML en {input_dir}/")

    all_dfs = []

    iterator = xml_paths
    if tqdm is not None:
        iterator = tqdm(xml_paths, desc="Procesando snapshots XML")

    for path in iterator:
        try:
            df = parse_datex_historico_enriquecido(path)
            if df is None or df.empty:
                continue

            # Normalización para Power BI
            columnas_texto = [
                "provincia",
                "locality",
                "locality_ini",
                "locality_fin",
                "road",
                "type",
                "cause_type",
                "cause_detail",
            ]

            for col in columnas_texto:
                if col in df.columns:
                    df[col] = df[col].apply(normalizar_texto)

            all_dfs.append(df)

        except Exception as e:
            print(f"[WARN] Error procesando {os.path.basename(path)}: {e}")

    if not all_dfs:
        raise RuntimeError(
            "No se generó ningún dataframe. Revisa que los XML tengan situationRecords válidos."
        )

    df_base = pd.concat(all_dfs, ignore_index=True)

    # Asegurar publication_time
    if "publication_time" not in df_base.columns:
        df_base["publication_time"] = pd.NaT

    if "snapshot_datetime" in df_base.columns:
        df_base["publication_time"] = df_base["publication_time"].fillna(
            df_base["snapshot_datetime"]
        )

    df_base["publication_time"] = pd.to_datetime(
        df_base["publication_time"],
        utc=True,
        errors="coerce",
    )

    # Columnas que se exportan al csv
    keep_columns = [
        "snapshot_datetime",
        "publication_time",
        "id",
        "cause_type",
        "cause_detail",
        "probability",
        "severity",
        "road",
        "provincia",
        "locality",
        "locality_ini",
        "locality_fin",
        "latitude",
        "longitude",
        "latitude_ini",
        "longitude_ini",
        "latitude_fin",
        "longitude_fin",
        "kilometro",
        "kilometro_ini",
        "kilometro_fin",
        "sentido_kilometracion",
        "sentido_kilometracion_ini",
        "carril_usado",
        "start_time_hora",
        "start_time_fecha",
    ]

    keep_columns = [col for col in keep_columns if col in df_base.columns]
    df_base = df_base[keep_columns]

    base_path = os.path.join(
        output_dir,
        "00_snapshots_eventos_base_completo_espanol.csv",
    )

    df_base.to_csv(base_path, index=False)

    print(f"[OK] CSV base completo generado: {base_path}")
    print(f"     XML procesados: {len(xml_paths):,}")
    print(f"     Filas exportadas: {len(df_base):,}")

    if "id" in df_base.columns:
        print(f"     Eventos únicos por id: {df_base['id'].nunique():,}")


if __name__ == "__main__":
    main()