import time
import shutil
import folium

def safe_replace(src, dst, retries=5, delay=1):
    for i in range(retries):
        try:
            shutil.move(src, dst)
            return
        except PermissionError as e:
            print(f"[WARN] Intento {i+1}: no se pudo reemplazar el archivo. Reintentando en {delay}s...")
            time.sleep(delay)
    print(f"[ERROR] Fallo definitivo al mover {src} -> {dst}")


# Nueva funcion de icono_por_tipo tras cambios en mapas.py el 21-01
def icono_por_tipo(cause_type: str):
    """
    cause_type = valor de <sit:causeType>
    Ej: "roadMaintenance", "vehicleObstruction", ...
    """

    icon_map = {
        # Accidentes
        "accident": ("car-crash", "red"),

        # Meteorología / ambiente
        "poorEnvironment": ("cloud-showers-heavy", "cadetblue"),
        "environmentalObstruction": ("cloud-showers-heavy", "cadetblue"),

        # Daños / infraestructura
        "infrastructureDamageObstruction": ("triangle-exclamation", "orange"),

        # Obstáculos genéricos
        "obstruction": ("triangle-exclamation", "black"),

        # Mantenimiento / obras
        "roadMaintenance": ("tools", "gray"),

        # Gestión de carril/carretera
        "roadOrCarriagewayOrLaneManagement": ("route", "darkblue"),

        # Vehículo obstaculizando
        "vehicleObstruction": ("car-side", "darkpurple"),

        # Trafico anómalo
        "abnormalTraffic": ("car-side", "darkred"),
    }

    if not cause_type:
        return ("exclamation-triangle", "red")

    # normaliza por si llega con espacios
    key = cause_type.strip()

    return icon_map.get(key, ("exclamation-triangle", "red"))


# Funcion para generar el segmento entre los popups de tramo
def add_segment_line_js(base_map, max_km=50):
    map_var = base_map.get_name()
    js = f"""
    (function() {{
      function bindWhenReady() {{
        if (typeof {map_var} === "undefined" || !{map_var}) {{
          setTimeout(bindWhenReady, 50);
          return;
        }}
        var map = {map_var};

        window.__activeSegmentLine = window.__activeSegmentLine || null;

        function removeActiveLine() {{
          if (window.__activeSegmentLine) {{
            try {{ map.removeLayer(window.__activeSegmentLine); }} catch(e) {{}}
            window.__activeSegmentLine = null;
          }}
        }}

        function extractSegData(popupContent) {{
          var el = null;
          if (!popupContent) return null;

          if (typeof popupContent === "string") {{
            var wrapper = document.createElement("div");
            wrapper.innerHTML = popupContent;
            el = wrapper.querySelector("div[data-seg]");
          }} else if (popupContent instanceof HTMLElement) {{
            el = popupContent.querySelector("div[data-seg]") ||
                 ((popupContent.matches && popupContent.matches("div[data-seg]")) ? popupContent : null);
          }} else {{
            return null;
          }}

          if (!el) return null;

          var seg = el.dataset.seg;
          var latIni = parseFloat(el.dataset.latIni);
          var lngIni = parseFloat(el.dataset.lngIni);
          var latFin = parseFloat(el.dataset.latFin);
          var lngFin = parseFloat(el.dataset.lngFin);

          if (!seg || [latIni, lngIni, latFin, lngFin].some(x => Number.isNaN(x))) return null;

          return {{ seg: seg, latIni: latIni, lngIni: lngIni, latFin: latFin, lngFin: lngFin }};
        }}

        map.on("popupopen", function(e) {{
          var content = e.popup && e.popup.getContent ? e.popup.getContent() : null;
          var data = extractSegData(content);

          if (!data) {{
            removeActiveLine();
            return;
          }}

          removeActiveLine();

          var MAX_KM = {float(max_km)};
          var dMeters = map.distance([data.latIni, data.lngIni], [data.latFin, data.lngFin]);
          var dKm = dMeters / 1000;

          if (dKm <= MAX_KM) {{
            window.__activeSegmentLine = L.polyline(
              [[data.latIni, data.lngIni], [data.latFin, data.lngFin]]
            ).addTo(map);
          }}
        }});

        map.on("click", function() {{
          removeActiveLine();
        }});
      }}

      bindWhenReady();
    }})();
    """
    base_map.get_root().script.add_child(folium.Element(js))
