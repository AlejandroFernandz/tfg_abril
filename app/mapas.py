# Generar los mapas y sus funcionalidades
import os
from datetime import datetime, timezone

import folium
import pandas as pd
from folium.plugins import MarkerCluster

from app.utilidades import icono_por_tipo, add_segment_line_js
from app.descarga import download_trafico, download_radares
from app.parsing import parse_datex, parse_radares


# Guarda el html cuando acabe por si está recargdando
def save_atomic(m, output_file):
    tmp = output_file + ".tmp"
    m.save(tmp)
    os.replace(tmp, output_file)


# Mete el mapa al html padre para poder hazer los zooms
def expose_leaflet_map(base_map):
    map_var = base_map.get_name()
    js = f"""
    (function() {{
        function bind() {{
            if (typeof {map_var} !== "undefined" && {map_var}) {{
                window.map = {map_var};
            }} else {{
                setTimeout(bind, 50);
            }}
        }}
        bind();
    }})();
    """
    base_map.get_root().script.add_child(folium.Element(js))


def crear_popup_evento_puntual(event, provincia, lat, lon):
    return f"""
    <div data-provincia="{provincia}" data-lat="{lat}" data-lng="{lon}">
    <div style="font-size:14px; line-height:1.25;">
        <div style="font-weight:700; font-size:15px;">{event.get('type','Evento')}</div>
        <div style="font-weight:600;">{event.get('cause_type','')}</div>
        <div style="font-style:italic; color:#444;">{event.get('cause_detail','')}</div>

        <hr style="margin:8px 0;">

        <div>📍 <b>{event.get('road','')}</b> · Km <b>{event.get('kilometro','')}</b></div>
        <div>🏙️ {event.get('locality','Desconocido')} ({event.get('provincia','Desconocida')})</div>
        <div>➡️ Sentido de circulación: {event.get('sentido_kilometracion','Sentido desconocido')}</div>
        <div>🛣️ Carril afectado: {event.get('carril_usado','')}</div>

        <hr style="margin:8px 0;">

        <div>⚠️ Severidad: <b>{event.get('severity','desconocida')}</b> · Prob.: <b>{event.get('probability','desconocida')}</b></div>
        <div>🕒 Inicio: {event.get('start_time','Fecha desconocida')}</div>

        <div style="margin-top:6px; font-size:12px; color:#666;">ID: {event.get('id','')}</div>
    </div>
    </div>
    """


def crear_popup_evento_tramo(event, provincia, seg_id, lat, lon, lat_ini, lon_ini, lat_fin, lon_fin):
    return f"""
    <div data-seg="{seg_id}"
        data-lat-ini="{lat_ini}" data-lng-ini="{lon_ini}"
        data-lat-fin="{lat_fin}" data-lng-fin="{lon_fin}"
        data-provincia="{provincia}" data-lat="{lat}" data-lng="{lon}">
    <div style="font-size:14px; line-height:1.25;">
        <div style="font-weight:700; font-size:15px;">{event.get('type','Evento')}</div>
        <div style="font-weight:600;">{event.get('cause_type','')}</div>
        <div style="font-style:italic; color:#444;">{event.get('cause_detail','')}</div>

        <hr style="margin:8px 0;">

        <div>🛣️ <b>{event.get('road','')}</b> ({event.get('provincia','Desconocida')})</div>
        <div>▶️ <b>TRAMO</b>:
        Km <b>{event.get('kilometro_ini','')}</b> — {event.get('locality_ini','Desconocido')}
        → Km <b>{event.get('kilometro_fin','')}</b> — {event.get('locality_fin','Desconocido')}
        </div>
        <div>➡️ Sentido de circulación: {event.get('sentido_kilometracion','Sentido desconocido')}</div>
        <div>🛣️ Carril afectado: {event.get('carril_usado','')}</div>

        <hr style="margin:8px 0;">

        <div>⚠️ Severidad: <b>{event.get('severity','desconocida')}</b> · Prob.: <b>{event.get('probability','desconocida')}</b></div>
        <div>🕒 Inicio: {event.get('start_time','Fecha desconocida')}</div>

        <div style="margin-top:6px; font-size:12px; color:#666;">ID: {event.get('id','')}</div>
    </div>
    </div>
    """


def crear_popup_radar_cabina(radar, provincia, lugar):
    return f"""
    <div data-provincia="{provincia}">
    <div style="font-size:14px; line-height:1.25;">
        <div style="font-weight:700; font-size:15px;">Radar fijo (cabina)</div>
        <div style="font-weight:600;">Control de velocidad</div>

        <hr style="margin:8px 0;">

        <div>📍 <b>{radar.get('road','')}</b> · Km <b>{radar.get('kilometro','')}</b></div>
        <div>🏙️ {lugar} ({radar.get('provincia','Desconocida')})</div>
        <div>➡️ Sentido de circulación: {radar.get('sentido_kilometracion','Desconocido')}</div>

        <hr style="margin:8px 0;">

        <div style="margin-top:6px; font-size:12px; color:#666;">ID: {radar.get('radar_id_fijo','')}</div>
    </div>
    </div>
    """


def crear_popup_radar_tramo(radar, provincia, lugar, label, seg_id, lat, lon, lat_ini_r, lon_ini_r, lat_fin_r, lon_fin_r):
    if label == "INI":
        km_mostrado = radar.get("kilometro_ini", "")
        id_punto = radar.get("radar_id_ini", "")
        titulo_punto = "Inicio del tramo"
    else:
        km_mostrado = radar.get("kilometro_fin", "")
        id_punto = radar.get("radar_id_fin", "")
        titulo_punto = "Final del tramo"

    return f"""
    <div data-seg="{seg_id}"
        data-lat-ini="{lat_ini_r}" data-lng-ini="{lon_ini_r}"
        data-lat-fin="{lat_fin_r}" data-lng-fin="{lon_fin_r}"
        data-provincia="{provincia}" data-lat="{lat}" data-lng="{lon}">
    <div style="font-size:14px; line-height:1.25;">
        <div style="font-weight:700; font-size:15px;">Radar de tramo — {label}</div>
        <div style="font-weight:600;">{titulo_punto}</div>
        <div style="font-style:italic; color:#444;">Control de velocidad media</div>

        <hr style="margin:8px 0;">

        <div>📍 <b>{radar.get('road','')}</b> · Km <b>{km_mostrado}</b></div>
        <div>🏙️ {lugar} ({radar.get('provincia','Desconocida')})</div>
        <div>➡️ Sentido de circulación: {radar.get('sentido_kilometracion','Desconocido')}</div>

        <hr style="margin:8px 0;">

        <div style="font-size:12px; color:#666;">
        ID INI: {radar.get('radar_id_ini','')}<br>
        ID FIN: {radar.get('radar_id_fin','')}
        </div>
    </div>
    </div>
    """


# Crear el mapa combinado entre incidencias y radares
def create_actuales_map(eventos_df, radares_df, output_file="mapa_actuales.html"):
    OFFSET = 0.0001
    added_locations = set()
    added_radar_locations = set()
    # Se inicia el mapa vacio centrado en España
    base_map = folium.Map(location=[40.4168, -3.7038], zoom_start=6, tiles = None)

    # Para usar el opnestreet map pero que no aparezca l aopcion de cmabiar entre apas porque solo hay una
    folium.TileLayer("OpenStreetMap", control=False).add_to(base_map)
    
    # Crear las casillas seleccionables de incidencias y radares
    cluster_eventos = MarkerCluster(
        name="Incidencias agrupadas",
        maxClusterRadius=50,
        disableClusteringAtZoom=15
    ).add_to(base_map)

    cluster_radares = MarkerCluster(
        name="Radares agrupados",
        maxClusterRadius=50,
        disableClusteringAtZoom=15
    ).add_to(base_map)

    def añadir_eventos(df):
        for _, event in df.iterrows():
            icon_name, icon_color = icono_por_tipo(event.get("cause_type_raw") or "unknown")
            provincia = event["provincia"]

            # Eventos con una única coordenada
            if pd.notna(event.get("latitude")) and pd.notna(event.get("longitude")):
                lat, lon = event["latitude"], event["longitude"]

                while (lat, lon) in added_locations:
                    lat += OFFSET
                    lon += OFFSET

                added_locations.add((lat, lon))

                html_popup = crear_popup_evento_puntual(event, provincia, lat, lon)

                folium.Marker(
                    location=[lat, lon],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_popup, max_width=300),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                ).add_to(cluster_eventos)

            # Eventos de tramo (coordendas iniciales y finales de la incidencia)
            if pd.notna(event.get("latitude_ini")) and pd.notna(event.get("longitude_ini")):
                lat_ini, lon_ini = event["latitude_ini"], event["longitude_ini"]
                lat_fin, lon_fin = event["latitude_fin"], event["longitude_fin"]

                while (lat_ini, lon_ini) in added_locations:
                    lat_ini += OFFSET
                    lon_ini += OFFSET
                added_locations.add((lat_ini, lon_ini))

                while (lat_fin, lon_fin) in added_locations:
                    lat_fin += OFFSET
                    lon_fin += OFFSET
                added_locations.add((lat_fin, lon_fin))

                seg_id = f"event_{event['id']}"

                html_ini = crear_popup_evento_tramo(
                    event, provincia, seg_id,
                    lat_ini, lon_ini,
                    lat_ini, lon_ini,
                    lat_fin, lon_fin
                )

                html_fin = crear_popup_evento_tramo(
                    event, provincia, seg_id,
                    lat_fin, lon_fin,
                    lat_ini, lon_ini,
                    lat_fin, lon_fin
                )

                folium.Marker(
                    location=[lat_ini, lon_ini],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_ini, max_width=300),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                ).add_to(cluster_eventos)

                folium.Marker(
                    location=[lat_fin, lon_fin],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_fin, max_width=300),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                ).add_to(cluster_eventos)

    añadir_eventos(eventos_df)

    for _, radar in radares_df.iterrows():
        provincia = radar["provincia"]
        lugar = radar.get("location_name") or radar.get("provincia", "Desconocida")

        # Radar fijo
        if radar["type"] == "Cabina":
            lat, lon = radar["latitude"], radar["longitude"]

            if (lat, lon) not in added_radar_locations:
                html = crear_popup_radar_cabina(radar, provincia, lugar)

                folium.Marker(
                    location=[lat, lon],
                    tooltip=f"{radar['type']}<br>{provincia}",
                    popup=folium.Popup(html, max_width=300),
                    icon=folium.Icon(color="red", icon="tachometer-alt", prefix="fa")
                ).add_to(cluster_radares)

                added_radar_locations.add((lat, lon))

        # Radar de tramo
        else:
            seg_id = f"radar_{radar['radar_id_ini']}_{radar['radar_id_fin']}"
            lat_ini_r, lon_ini_r = radar.get("latitude_ini"), radar.get("longitude_ini")
            lat_fin_r, lon_fin_r = radar.get("latitude_fin"), radar.get("longitude_fin")

            coords = [
                ("INI", lat_ini_r, lon_ini_r, radar["radar_id_ini"]),
                ("FIN", lat_fin_r, lon_fin_r, radar["radar_id_fin"])
            ]

            for label, lat, lon, radar_id in coords:
                if pd.notna(lat) and pd.notna(lon) and (lat, lon) not in added_radar_locations:
                    html = crear_popup_radar_tramo(
                        radar, provincia, lugar, label, seg_id,
                        lat, lon,
                        lat_ini_r, lon_ini_r,
                        lat_fin_r, lon_fin_r
                    )

                    folium.Marker(
                        location=[lat, lon],
                        tooltip=f"{radar['type']}<br>{provincia}",
                        popup=folium.Popup(html, max_width=300),
                        icon=folium.Icon(
                            color="orange",
                            icon="arrow-right" if label == "FIN" else "arrow-left",
                            prefix="fa"
                        )
                    ).add_to(cluster_radares)

                    added_radar_locations.add((lat, lon))

    folium.LayerControl(collapsed=False).add_to(base_map)

    expose_leaflet_map(base_map)
    add_segment_line_js(base_map, max_km=50)

    save_atomic(base_map, output_file)


# Actualizar el mapa
def update_map():
    # Descarga de los datos fuente
    download_trafico("data/trafico.xml")
    download_radares("data/radares.xml")

    # Parseo de los datos
    eventos_df = parse_datex("data/trafico.xml")
    radares_df = parse_radares("data/radares.xml")

    # Provincias para meter en el zoom del desplegable
    provincias_coords = {
        "A Coruña": [43.3623, -8.4115],
        "Albacete": [38.9943, -1.8585],
        "Alicante": [38.3452, -0.4810],
        "Almería": [36.8381, -2.4597],
        "Ávila": [40.6565, -4.6818],
        "Badajoz": [38.8786, -6.9703],
        "Baleares": [39.5696, 2.6502],
        "Barcelona": [41.3888, 2.1590],
        "Bilbao": [43.2630, -2.9350],
        "Burgos": [42.3440, -3.6969],
        "Cáceres": [39.4765, -6.3722],
        "Cádiz": [36.5160, -6.2994],
        "Castellón": [39.9864, -0.0513],
        "Ciudad Real": [38.9861, -3.9271],
        "Córdoba": [37.8882, -4.7794],
        "Cuenca": [40.0704, -2.1374],
        "Girona": [41.9794, 2.8214],
        "Granada": [37.1773, -3.5986],
        "Guadalajara": [40.6330, -3.1669],
        "Huelva": [37.2614, -6.9447],
        "Huesca": [42.1401, -0.4089],
        "Jaén": [37.7796, -3.7849],
        "La Rioja": [42.4650, -2.4480],
        "Las Palmas": [28.1235, -15.4363],
        "León": [42.5987, -5.5671],
        "Lleida": [41.6176, 0.6200],
        "Lugo": [43.0097, -7.5560],
        "Madrid": [40.4168, -3.7038],
        "Málaga": [36.7213, -4.4214],
        "Murcia": [37.9834, -1.1299],
        "Navarra": [42.8125, -1.6458],
        "Ourense": [42.3360, -7.8642],
        "Oviedo": [43.3619, -5.8494],
        "Palencia": [42.0095, -4.5270],
        "Pontevedra": [42.4333, -8.6333],
        "Salamanca": [40.9701, -5.6635],
        "San Sebastián": [43.3183, -1.9812],
        "Santa Cruz de Tenerife": [28.4636, -16.2518],
        "Santander": [43.4623, -3.8099],
        "Segovia": [40.9481, -4.1184],
        "Sevilla": [37.3886, -5.9823],
        "Soria": [41.7666, -2.4689],
        "Tarragona": [41.1189, 1.2445],
        "Teruel": [40.3456, -1.1065],
        "Toledo": [39.8628, -4.0273],
        "Valencia": [39.4737, -0.3758],
        "Valladolid": [41.6520, -4.7286],
        "Vitoria": [42.8467, -2.6727],
        "Zamora": [41.5033, -5.7446],
        "Zaragoza": [41.6488, -0.8891],
    }


    opciones_provincia = "<br>".join(
        [f'<option value="{prov}">{prov}</option>' for prov in provincias_coords.keys()]
    )

    coordenadas_js = "{\n"
    for provincia, coords in provincias_coords.items():
        coordenadas_js += f'    "{provincia.upper()}": {coords},\n'
    coordenadas_js += '    "TODAS": [40.4168, -3.7038]\n}'

    # Filtrar eventos actuales
    now = datetime.now(timezone.utc)
    eventos_actuales = eventos_df[eventos_df["start_time_obj"] <= now]

    # Generar el mapa
    create_actuales_map(eventos_actuales, radares_df, "mapas_generados/mapa_actuales.html")

    # Crear el HTML principal embebiendo el iframe
    html_con_tabs = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mapa de Tráfico</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; overflow: hidden; height: 100vh; }}
        .layout {{ display: flex; height: 100vh; overflow: hidden; }}
        .sidebar {{ width: 260px; background: #f9f9f9; padding: 1em; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }}
        .main {{ flex-grow: 1; position: relative; }}
        .tab-button {{ width: 100%; padding: 0.8em 0.75em; margin-bottom: 0.5em; border: 1px solid #ccc; background: #fff; cursor: pointer; text-align: left; font-size: 0.95rem; }}
        .tab-button.active {{ background: #e6f7ff; border-color: #91d5ff; }}
        .tab-content {{ display: none; width: 100%; height: 100%; }}
        .tab-content.active {{ display: block; }}
        .sidebar-section {{ margin-top: 1em; }}
        .sidebar-note {{ font-size: 0.95rem; line-height: 1.5; color: #333; }}
    </style>
</head>
<body>

<div class="layout">
  <div class="sidebar">
    <button id="tabMapa" class="tab-button active">Mapa interactivo</button>
    <button id="tabGrafica" class="tab-button">Análisis histórico</button>

    <div id="sidebarMapOptions" class="sidebar-section">
      <label for="provinciaSelect"><b>Filtrar por provincia:</b></label><br>
      <select id="provinciaSelect" style="width: 100%; margin-top: 0.5em;">
          <option value="Todas">Todas</option>
          {opciones_provincia}
      </select>
    </div>

    <div id="sidebarReportInfo" class="sidebar-section" style="display: none;">
        <div class="sidebar-note">
            <ol>
                <li>Resumen temporal general</li>
                <li>Patrones horarios</li>
                <li>Persistencia de incidencias</li>
                <li>Impacto geográfico</li>
                <li>Incidencias y fútbol</li>
            </ol>
        </div>
    </div>
  </div>

  <div class="main">
    <div id="mapContent" class="tab-content active">
      <iframe id="iframe_actuales" style="width:100%; height:100%; border:none;"></iframe>
    </div>
    <div id="reportContent" class="tab-content">
      <iframe id="iframe_report" style="width:100%; height:100%; border:none;" title="Informe Power BI"></iframe>
    </div>
  </div>
</div>

<script>
    const iframeActuales = document.getElementById("iframe_actuales");
    const iframeReport = document.getElementById("iframe_report");
    const reportUrl = 'https://app.powerbi.com/view?r=eyJrIjoiOWVhZWUyZDQtMzgwYy00MGFiLTg2MzgtZTU0ZWQ2MGRmMmQ0IiwidCI6ImNlYTFlYTNlLTYwYjItNGY3NS1hNmMyLWE2MDIyZThmOTYxYiIsImMiOjh9&pageName=1a8004df269ae39b23d6';

    iframeActuales.src = "/mapa_actuales.html?ts=" + Date.now();
    iframeReport.src = reportUrl;

    const tabMapa = document.getElementById("tabMapa");
    const tabGrafica = document.getElementById("tabGrafica");
    const mapContent = document.getElementById("mapContent");
    const reportContent = document.getElementById("reportContent");
    const sidebarMapOptions = document.getElementById("sidebarMapOptions");
    const sidebarReportInfo = document.getElementById("sidebarReportInfo");

    const activateTab = (tab) => {{
        const isMap = tab === "map";

        tabMapa.classList.toggle("active", isMap);
        tabGrafica.classList.toggle("active", !isMap);

        mapContent.classList.toggle("active", isMap);
        reportContent.classList.toggle("active", !isMap);

        sidebarMapOptions.style.display = isMap ? "block" : "none";
        sidebarReportInfo.style.display = isMap ? "none" : "block";
    }};

    tabMapa.addEventListener("click", () => activateTab("map"));
    tabGrafica.addEventListener("click", () => activateTab("report"));

    const coordenadas_provincias = {coordenadas_js};

    document.getElementById("provinciaSelect").addEventListener("change", function () {{
        const seleccion = this.value.trim().toUpperCase();
        const coords = coordenadas_provincias[seleccion] || coordenadas_provincias["TODAS"];
        const zoom = seleccion === "TODAS" ? 6 : 9;

        const intentarZoom = () => {{
            try {{
                const mapa = iframeActuales.contentWindow.map;

                if (mapa && typeof mapa.setView === "function") {{
                    mapa.setView(coords, zoom);
                }} else {{
                    setTimeout(intentarZoom, 200);
                }}
            }} catch (e) {{
                setTimeout(intentarZoom, 200);
            }}
        }};

        intentarZoom();
    }});

    // Recarga solo el iframe del mapa, no toda la página
    setInterval(() => {{
        iframeActuales.src = "/mapa_actuales.html?ts=" + Date.now();
    }}, 120000);
</script>

</body>
</html>"""

    # Escritura atómica para evitar que se lea el HTML mientras se está generando
    temp_path = "mapas_generados/mapa_completo.tmp.html"
    final_path = "mapas_generados/mapa_completo.html"

    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(html_con_tabs)

    os.replace(temp_path, final_path)

    print("[OK] Mapa principal generado en: mapas_generados/mapa_completo.html")