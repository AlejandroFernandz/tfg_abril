########################################## Ver todos los valores para un detalle de evento #######################################

# import pandas as pd

# # 1. Carga tu archivo CSV (reemplaza 'datos.csv' por el nombre de tu archivo real)
# df = pd.read_csv('analysis/datasets_generados/03_persistencia_eventos.csv')

# # 2. Escribe aquí el nombre exacto de la columna que quieres explorar
# columna_deseada = 'cause_detail' 

# # 3. Extrae los valores únicos y cuenta sus repeticiones
# valores_unicos = df[columna_deseada].value_counts()

# print(f"--- Valores únicos para la columna: '{columna_deseada}' ---")
# print(valores_unicos)

######################################## ver numero de registros, maximo y media de un evento ######################################################

# import pandas as pd

# # 1. Carga tu archivo CSV
# df = pd.read_csv("analysis/datasets_generados/03_persistencia_eventos.csv")

# # 2. ESCRIBE AQUÍ el detalle de la causa que quieres analizar
# # Puedes cambiarlo por cualquier otro valor (ej. 'Carretera Cortada', 'Accidente', etc.)
# causa_elegida = "Inundacion"

# # 3. Filtrar el dataset por la causa seleccionada
# df_filtrado = df[df["cause_detail"] == causa_elegida]

# # 4. Verificar si existen datos y calcular las métricas
# if not df_filtrado.empty:
#     # Convertimos a numérico por seguridad (ignora errores de texto o celdas vacías)
#     duraciones = pd.to_numeric(
#         df_filtrado["duracion_oficial_horas"], errors="coerce"
#     )

#     maximo = duraciones.max()
#     media = duraciones.mean()

#     print(f"--- Análisis para cause_detail: '{causa_elegida}' ---")
#     print(f"Número de registros encontrados: {len(df_filtrado)}")
#     print(f"Duración máxima oficial: {maximo:.2f} horas")
#     print(f"Duración media oficial: {media:.2f} horas")
# else:
#     # Si te equivocas al escribir la causa, el script te muestra las opciones reales del CSV
#     valores_disponibles = df["cause_detail"].dropna().unique()
#     print(f"No se encontraron registros para la causa: '{causa_elegida}'.")
#     print(f"Opciones disponibles en tu CSV: {list(valores_disponibles)}")

import pandas as pd

# Cargar el archivo CSV
df = pd.read_csv('analysis/datasets_generados/02_snapshot_detallado_ligero.csv')

# Obtener filas y columnas
filas, columnas = df.shape

print(f"Filas: {filas}")
print(f"Columnas: {columnas}")
