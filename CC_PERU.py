import streamlit as st
import geopandas as gpd
import os
import glob
import plotly.express as px
import folium
from streamlit_folium import st_folium

# =========================
# CONFIG
# =========================
RESULT_DIR = "RESULTADOS"

st.set_page_config(layout="wide")
st.title("Cambio Climático en el Perú")

# =========================
# COLORES OFICIALES
# =========================
prec_colors = [
    "#663300","#7b4d1b","#916836","#a68351","#bc9d6d","#d2b888","#e7d3a3",
    "#c1f4db","#a1d4bf","#80b3a3","#609387","#40736b","#20534f","#003333"
]

temp_colors = [
    "#ffffcc","#fff7b9","#fff0a7","#ffe895","#fee983","#fed572","#fec460",
    "#feb44e","#fea446","#fd953f","#fd8038","#fc6531","#fb4b29","#f03523",
    "#e61f1d","#d7121f","#c70723","#b30026","#9a0026","#800026"
]

# =========================
# CLASIFICACIÓN COLOR
# =========================
def get_color(value, variable):
    if variable == "pr":
        bins = [-999,-90,-75,-60,-45,-30,-15,0,15,30,45,60,75,90,999]
        colors = prec_colors
    else:
        bins = [-999,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.2,
                2.4,2.6,2.8,3.0,3.2,3.4,3.6,3.8,999]
        colors = temp_colors

    for i in range(len(bins)-1):
        if bins[i] < value <= bins[i+1]:
            return colors[i]
    return "#cccccc"

# =========================
# FORMATO VALORES
# =========================
def format_val(value, variable):
    if value is None:
        return "Sin dato"
    return f"{value:.1f} %" if variable == "pr" else f"{value:.1f} °C"

# =========================
# DETECTAR ARCHIVOS
# =========================
files = glob.glob(os.path.join(RESULT_DIR, "*.geojson")) + \
        glob.glob(os.path.join(RESULT_DIR, "*.gpkg"))

data_dict = {}
for f in files:
    name = os.path.basename(f).replace(".geojson", "").replace(".gpkg", "")
    parts = name.split("_")

    nivel = parts[0]
    variable = parts[2]
    periodo = parts[3]

    if nivel not in data_dict:
        data_dict[nivel] = {}

    key = f"{variable}_{periodo}"
    data_dict[nivel][key] = f

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Configuración")

nivel = st.sidebar.selectbox("Nivel territorial", list(data_dict.keys()))
escenario = st.sidebar.selectbox("Variables", list(data_dict[nivel].keys()))

file_path = data_dict[nivel][escenario]
variable = escenario.split("_")[0]

# =========================
# CARGA DE DATOS
# =========================
@st.cache_resource
def load_data(path):
    try:
        gdf = gpd.read_file(path)
    except:
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        gdf = gpd.GeoDataFrame.from_features(data)

    gdf["geometry"] = gdf["geometry"].simplify(0.01)
    return gdf

gdf = load_data(file_path)
gdf = gdf.dropna(subset=["valor"])

# columna nombre
nombre_col = [c for c in gdf.columns if c not in ["geometry","valor"]][0]

# formato
gdf["valor_fmt"] = gdf["valor"].apply(lambda x: format_val(x, variable))

# =========================
# MAPA
# =========================
m = folium.Map(location=[-9,-75], zoom_start=5)

def style_function(feature):
    val = feature["properties"]["valor"]
    return {
        "fillColor": get_color(val, variable),
        "color": "black",
        "weight": 0.2,
        "fillOpacity": 0.8
    }

folium.GeoJson(
    gdf,
    style_function=style_function,
    smooth_factor=0.5,
    tooltip=folium.GeoJsonTooltip(
        fields=[nombre_col, "valor_fmt"],
        aliases=["Nombre:", "Valor:"]
    )
).add_to(m)

# =========================
# LEYENDAS
# =========================
legend_pr = """
<div style="
position: fixed;
bottom: 20px;
left: 20px;
width: 110px;
background-color: white;
z-index:9999;
font-size:10px;
border:0.5px solid #999;
padding: 6px;
">
<b>Δ PR (%)</b><br>
<div style="background:#663300;width:10px;height:7px;display:inline-block;"></div> <= -90<br>
<div style="background:#7b4d1b;width:10px;height:7px;display:inline-block;"></div> -90 a -75<br>
<div style="background:#916836;width:10px;height:7px;display:inline-block;"></div> -75 a -60<br>
<div style="background:#a68351;width:10px;height:7px;display:inline-block;"></div> -60 a -45<br>
<div style="background:#bc9d6d;width:10px;height:7px;display:inline-block;"></div> -45 a -30<br>
<div style="background:#d2b888;width:10px;height:7px;display:inline-block;"></div> -30 a -15<br>
<div style="background:#e7d3a3;width:10px;height:7px;display:inline-block;"></div> -15 a 0<br>
<div style="background:#c1f4db;width:10px;height:7px;display:inline-block;"></div> 0 a 15<br>
<div style="background:#a1d4bf;width:10px;height:7px;display:inline-block;"></div> 15 a 30<br>
<div style="background:#80b3a3;width:10px;height:7px;display:inline-block;"></div> 30 a 45<br>
<div style="background:#609387;width:10px;height:7px;display:inline-block;"></div> 45 a 60<br>
<div style="background:#40736b;width:10px;height:7px;display:inline-block;"></div> 60 a 75<br>
<div style="background:#20534f;width:10px;height:7px;display:inline-block;"></div> 75 a 90<br>
<div style="background:#003333;width:10px;height:7px;display:inline-block;"></div> >= 90<br>
</div>
"""

legend_temp = """
<div style="
position: fixed;
bottom: 20px;
left: 20px;
width: 110px;
background-color: white;
z-index:9999;
font-size:10px;
border:0.5px solid #999;
padding: 6px;
">
<b>Δ Temp (°C)</b><br>
<div><span style="background:#ffffcc;width:10px;height:6px;display:inline-block;"></span> <= 0.2</div>
<div><span style="background:#fff7b9;width:10px;height:6px;display:inline-block;"></span> 0.2 a 0.4</div>
<div><span style="background:#fff0a7;width:10px;height:6px;display:inline-block;"></span> 0.4 a 0.6</div>
<div><span style="background:#ffe895;width:10px;height:6px;display:inline-block;"></span> 0.6 a 0.8</div>
<div><span style="background:#fee983;width:10px;height:6px;display:inline-block;"></span> 0.8 a 1.0</div>
<div><span style="background:#fed572;width:10px;height:6px;display:inline-block;"></span> 1.0 a 1.2</div>
<div><span style="background:#fec460;width:10px;height:6px;display:inline-block;"></span> 1.2 a 1.4</div>
<div><span style="background:#feb44e;width:10px;height:6px;display:inline-block;"></span> 1.4 a 1.6</div>
<div><span style="background:#fea446;width:10px;height:6px;display:inline-block;"></span> 1.6 a 1.8</div>
<div><span style="background:#fd953f;width:10px;height:6px;display:inline-block;"></span> 1.8 a 2.0</div>
<div><span style="background:#fd8038;width:10px;height:6px;display:inline-block;"></span> 2.0 a 2.2</div>
<div><span style="background:#fc6531;width:10px;height:6px;display:inline-block;"></span> 2.2 a 2.4</div>
<div><span style="background:#fb4b29;width:10px;height:6px;display:inline-block;"></span> 2.4 a 2.6</div>
<div><span style="background:#f03523;width:10px;height:6px;display:inline-block;"></span> 2.6 a 2.8</div>
<div><span style="background:#e61f1d;width:10px;height:6px;display:inline-block;"></span> 2.8 a 3.0</div>
<div><span style="background:#d7121f;width:10px;height:6px;display:inline-block;"></span> 3.0 a 3.2</div>
<div><span style="background:#c70723;width:10px;height:6px;display:inline-block;"></span> 3.2 a 3.4</div>
<div><span style="background:#b30026;width:10px;height:6px;display:inline-block;"></span> 3.4 a 3.6</div>
<div><span style="background:#9a0026;width:10px;height:6px;display:inline-block;"></span> 3.6 a 3.8</div>
<div><span style="background:#800026;width:10px;height:6px;display:inline-block;"></span> >= 3.8</div>
</div>
"""

if variable == "pr":
    m.get_root().html.add_child(folium.Element(legend_pr))
else:
    m.get_root().html.add_child(folium.Element(legend_temp))

# =========================
# LAYOUT
# =========================
col1, col2 = st.columns([2,1])

with col1:
    st_folium(m, width=900, height=600)

with col2:
    df = gdf.sort_values("valor", ascending=False)

    st.subheader("Ranking")
    st.dataframe(df[[nombre_col,"valor"]].head(15))

    fig = px.bar(df.head(15), x="valor", y=nombre_col, orientation="h")
    st.plotly_chart(fig, use_container_width=True)

# =========================
# INDICADORES
# =========================
st.subheader("Indicadores")

st.metric("Promedio", f"{gdf['valor'].mean():.2f}")
st.metric("Máximo", f"{gdf['valor'].max():.2f}")
st.metric("Mínimo", f"{gdf['valor'].min():.2f}")

# =========================
# INSIGHT
# =========================
top = df.iloc[0][nombre_col]
st.success(f"Zona más afectada: {top}")