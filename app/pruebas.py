import pandas as pd

# ==========================================
# CONFIGURACIÓN: Pon aquí tus datos
# ==========================================
RUTA_CSV = "analysis/datasets_generados/00_snapshots_eventos_base_completo_espanol.csv"  # Usa barras / para evitar errores en Windows
COLUMNA_A_REVISAR = "provincia"
SEPARADOR = ","  # Cambia por ";" si tu archivo usa punto y coma


def obtener_valores_unicos():
    try:
        # 1. Leer el archivo CSV
        df = pd.read_csv(RUTA_CSV, sep=SEPARADOR)

        # 2. Verificar si la columna existe
        if COLUMNA_A_REVISAR not in df.columns:
            print(
                f"❌ Error: La columna '{COLUMNA_A_REVISAR}' no existe en el archivo."
            )
            print(f"Columnas disponibles en tu CSV: {list(df.columns)}")
            return

        # 3. Extraer valores únicos, quitar espacios y limpiar vacíos (NaN)
        valores_unicos = (
            df[COLUMNA_A_REVISAR].dropna().astype(str).str.strip().unique()
        )
        valores_ordenados = sorted(valores_unicos)

        # 4. Mostrar resultados formateados listos para copiar a tu diccionario
        print(
            f"\n=== VALORES ÚNICOS EN '{COLUMNA_A_REVISAR}' ({len(valores_ordenados)}) ==="
        )
        for valor in valores_ordenados:
            print(f'    "{valor}": "",')

    except FileNotFoundError:
        print(
            f"❌ Error: No se encontró ningún archivo en la ruta: '{RUTA_CSV}'"
        )
    except Exception as e:
        print(f"❌ Ocurrió un error al leer el archivo: {e}")


if __name__ == "__main__":
    obtener_valores_unicos()
