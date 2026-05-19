
import os
import glob
import sys
import pandas as pd

# Añadir el directorio padre al path para poder importar app desde analysis/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# tqdm opcional: si no lo tienes, funciona igual sin barra
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from utils_analisis import parse_datex_historico_enriquecido
from app.parsing import TRAD_EVENT_TYPE, TRAD_CAUSE_TYPE, TRAD_CAUSE_DETAIL


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

            # Traducciones al español
            if "record_xsi_type" in df.columns:
                df["type"] = df["record_xsi_type"].map(TRAD_EVENT_TYPE).fillna(df["record_xsi_type"])
            if "cause_type" in df.columns:
                df["cause_type"] = df["cause_type"].map(TRAD_CAUSE_TYPE).fillna(df["cause_type"])
            if "cause_detail" in df.columns:
                df["cause_detail"] = df["cause_detail"].map(TRAD_CAUSE_DETAIL).fillna(df["cause_detail"])

            # Normalización (Power BI)
            for col in ["provincia", "locality", "locality_ini", "locality_fin",
                        "road", "type", "cause_type", "cause_detail"]:
                if col in df.columns:
                    df[col] = df[col].apply(normalizar_texto)

            all_dfs.append(df)

        except Exception as e:
            print(f"[WARN] Error procesando {os.path.basename(path)}: {e}")

    if not all_dfs:
        raise RuntimeError("No se generó ningún dataframe. Revisa que los XML tengan situationRecords válidos.")

    df_base = pd.concat(all_dfs, ignore_index=True)

    # Asegurar publication_time
    if "publication_time" not in df_base.columns:
        df_base["publication_time"] = pd.NaT

    if "snapshot_datetime" in df_base.columns:
        df_base["publication_time"] = df_base["publication_time"].fillna(df_base["snapshot_datetime"])

    df_base["publication_time"] = pd.to_datetime(df_base["publication_time"], utc=True, errors="coerce")

    base_path = os.path.join(output_dir, "00_snapshots_eventos_base.csv")
    df_base.to_csv(base_path, index=False)

    print(f"[OK] CSV base generado: {base_path}")
    print(f"     Filas: {len(df_base):,} | Eventos únicos (por id): {df_base['id'].nunique():,}")
    print("     Nota: este CSV tiene eventos repetidos por snapshot (1 fila por evento activo y hora).")


if __name__ == "__main__":
    main()