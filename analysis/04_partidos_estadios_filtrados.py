import os
import pandas as pd

INPUT_SP1 = "data/SP1.csv"
INPUT_SP2 = "data/SP2.csv"
OUTPUT_CSV = "analysis/datasets_generados/04_partidos_estadios_filtrados.csv"

VENTANA_INICIO = pd.Timestamp("2025-03-13 11:09:00")
VENTANA_FIN = pd.Timestamp("2025-05-22 07:01:00")

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

def clasificar_partido(row): 
    local = row["HomeTeam"] 
    visitante = row["AwayTeam"] 
    equipos_top = { "Real Madrid", "Barcelona", "Ath Madrid", "Betis", "Sevilla", "Ath Bilbao", "Sociedad" } 
    equipos = {local, visitante} 
    
    if equipos == {"Real Madrid", "Barcelona"}: return "Clasico" 
    if equipos == {"Ath Bilbao", "Sociedad"}: return "Derbi Vasco" 
    if equipos == {"Betis", "Sevilla"}: return "Derbi Andaluz" 
    if equipos == {"Real Madrid", "Ath Madrid"}: return "Derbi Madrileno" 
    if local in equipos_top and visitante in equipos_top: return "Top Match"
    if row["Div"] == "UCL": return "Champions"
    if row["Div"] == "UEL": return "Europa League"
    if row["Div"] == "Conf": return "Conference League"
    return "Normal"

def main(): 
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True) 
    cols = ["Div", "Date", "Time", "HomeTeam", "AwayTeam"] 
    
    # 1. Leer los archivos existentes de la liga
    sp1 = pd.read_csv(INPUT_SP1, usecols=cols) 
    sp2 = pd.read_csv(INPUT_SP2, usecols=cols) 
    
    # 2. Definir partidos de Champions a mano
    partidos_champions_datos = [
        {"Div": "UCL", "Date": "9/04/2025", "Time": "20:00", "HomeTeam": "Barcelona", "AwayTeam": "Borussia D"},
        {"Div": "UCL", "Date": "16/04/2025", "Time": "20:00", "HomeTeam": "Real Madrid", "AwayTeam": "Arsenal"},
        {"Div": "UCL", "Date": "06/05/2025", "Time": "20:00", "HomeTeam": "Barcelona", "AwayTeam": "Inter Milan"},

        {"Div": "UEL", "Date": "17/04/2025", "Time": "20:00", "HomeTeam": "Ath Bilbao", "AwayTeam": "Rangers"},
        {"Div": "UEL", "Date": "01/05/2025", "Time": "20:00", "HomeTeam": "Ath Bilbao", "AwayTeam": "Man United"},
        # Me mapea San Mames, estadio de la final entre los dos equipos ingleses 
        {"Div": "UEL", "Date": "21/05/2025", "Time": "20:00", "HomeTeam": "Tottenham", "AwayTeam": "Man United"},

        {"Div": "Conf", "Date": "10/04/2025", "Time": "20:00", "HomeTeam": "Betis", "AwayTeam": "Jagiellonia B"},
        {"Div": "Conf", "Date": "01/05/2025", "Time": "20:00", "HomeTeam": "Betis", "AwayTeam": "Fiorentina"},

        
    ]
    
    # Convertir la lista manual a un DataFrame de Pandas
    champions_df = pd.DataFrame(partidos_champions_datos)
    
    # Concatenar todos los datos
    partidos = pd.concat([sp1, sp2, champions_df], ignore_index=True) 

    # Convertir la columna Time a formato timedelta, sumar 1 hora y volver a formatear como HH:MM para que las horas coincidan con las de trafico
    # Los partidos no vienen en hora local española porque la fuente es extranjera
    partidos['Time'] = pd.to_timedelta(partidos['Time'] + ':00') + pd.Timedelta(hours=1)
    partidos['Time'] = partidos['Time'].dt.components.apply(lambda x: f"{x.hours:02d}:{x.minutes:02d}", axis=1)


    # Fecha y hora de los partidos

    partidos["fecha_hora_partido"] = pd.to_datetime(
        partidos["Date"].astype(str).str.strip()
        + " "
        + partidos["Time"].astype(str).str.strip(),
        format="%d/%m/%Y %H:%M",
        errors="coerce"
    )

    partidos = partidos.dropna(subset=["fecha_hora_partido"])

    # Filtro para la ventana de datos de tráfico que hay

    partidos = partidos[
        (partidos["fecha_hora_partido"] >= VENTANA_INICIO)
        &
        (partidos["fecha_hora_partido"] <= VENTANA_FIN)
    ].copy()

    # Relacion de equipos con estadios

    estadios = {

        # Primera
        "Ath Bilbao": "San Mames",
        "Betis": "Benito Villamarin",
        "Celta": "Balaidos",
        "Las Palmas": "Estadio De Gran Canaria",
        "Osasuna": "El Sadar",
        "Leganes": "Butarque",
        "Sevilla": "Sanchez Pizjuan",
        "Getafe": "Coliseum",
        "Vallecano": "Vallecas",
        "Alaves": "Mendizorroza",
        "Valencia": "Mestalla",
        "Sociedad": "Anoeta",
        "Mallorca": "Son Moix",
        "Valladolid": "Jose Zorrilla",
        "Villarreal": "Ceramica",
        "Barcelona": "Montjuic",
        "Espanol": "Rcde Stadium",
        "Real Madrid": "Santiago Bernabeu",
        "Ath Madrid": "Metropolitano",
        "Girona": "Montilivi",
        "Tottenham": "San Mames", # La final de la Europa League se jugó en San Mames (para que lo guarde se le asigna ese estadio)

        # Segunda
        "Granada": "Los Carmenes",
        "Mirandes": "Municipal De Anduva",
        "Cadiz": "Nuevo Mirandilla",
        "Eibar": "Ipurua",
        "Ferrol": "A Malata",
        "La Coruna": "Riazor",
        "Santander": "El Sardinero",
        "Sp Gijon": "El Molinon",
        "Burgos": "El Plantio",
        "Elche": "Valero",
        "Eldense": "Pepico Amat",
        "Huesca": "El Alcoraz",
        "Levante": "Ciutat De Valencia",
        "Malaga": "La Rosaleda",
        "Tenerife": "Heliodoro",
        "Albacete": "Carlos Belmonte",
        "Castellon": "Castalia",
        "Cartagena": "Cartagonova",
        "Cordoba": "Arcangel",
        "Oviedo": "Carlos Tartiere",
        "Almeria": "Power Horse",
        "Zaragoza": "La Romareda",
    }

    partidos["Estadio"] = partidos["HomeTeam"].map(estadios)

    # Coordenadas de los estadios

    estadios_coords = [
        ["San Mames",43.2643,-2.9493],
        ["Benito Villamarin",37.3568,-5.9817],
        ["Balaidos",42.2120,-8.7398],
        ["Estadio De Gran Canaria",28.1006,-15.4567],
        ["El Sadar",42.7969,-1.6372],
        ["Butarque",40.3408,-3.7608],
        ["Sanchez Pizjuan",37.3845,-5.9711],
        ["Coliseum",40.3260,-3.7151],
        ["Vallecas",40.3922,-3.6587],
        ["Mendizorroza",42.8374,-2.6883],
        ["Mestalla",39.4751,-0.3588],
        ["Anoeta",43.3017,-1.9735],
        ["Son Moix",39.5901,2.6301],
        ["Jose Zorrilla",41.6448,-4.7612],
        ["Ceramica",39.9440,-0.1031],
        ["Montjuic",41.3649,2.1557],
        ["Rcde Stadium",41.3483,2.0747],
        ["Santiago Bernabeu",40.4531,-3.6884],
        ["Metropolitano",40.4364,-3.5995],
        ["Montilivi",41.9611,2.8277],
        ["Los Carmenes",37.1530,-3.5957],
        ["Municipal De Anduva",42.6810,-2.9354],
        ["Nuevo Mirandilla",36.5027,-6.2727],
        ["Ipurua",43.1819,-2.4758],
        ["A Malata",43.4915,-8.2399],
        ["Riazor",43.3686,-8.4166],
        ["El Sardinero",43.4765,-3.7927],
        ["El Molinon",43.5365,-5.6366],
        ["El Plantio",42.3444,-3.6803],
        ["Valero",38.2674,-0.6622],
        ["Pepico Amat",38.4677,-0.7962],
        ["El Alcoraz",42.1321,-0.4247],
        ["Ciutat De Valencia",39.4947,-0.3629],
        ["La Rosaleda",36.7337,-4.4262],
        ["Heliodoro",28.4634,-16.2601],
        ["Carlos Belmonte",38.9811,-1.8528],
        ["Castalia",39.9963,-0.0383],
        ["Cartagonova",37.6099,-0.9953],
        ["Arcangel",37.8724,-4.7641],
        ["Carlos Tartiere",43.3608,-5.8691],
        ["Power Horse",36.8402,-2.4347],
        ["La Romareda",41.6366,-0.9018],
    ]

    df_estadios = pd.DataFrame(
        estadios_coords,
        columns=["Estadio", "Latitud_Estadio", "Longitud_Estadio"]
    )

    partidos = partidos.merge(
        df_estadios,
        on="Estadio",
        how="left"
    )

    # Importancia de los partidos

    partidos["Importancia"] = partidos.apply(
        clasificar_partido,
        axis=1
    )

    partidos = partidos.sort_values("fecha_hora_partido")

    partidos.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8"
    )

    print(f"[OK] CSV generado: {OUTPUT_CSV}")
    print(f"     Partidos dentro de ventana: {len(partidos):,}")
    print(f"     Estadios distintos: {partidos['Estadio'].nunique():,}")
    print(f"     Desde: {partidos['fecha_hora_partido'].min()}")
    print(f"     Hasta: {partidos['fecha_hora_partido'].max()}")


if __name__ == "__main__":
    main()