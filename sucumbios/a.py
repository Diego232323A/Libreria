import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import folium
from folium.features import GeoJsonTooltip

# ===============================
# 1. Cargar el dataset filtrado
# ===============================
df = pd.read_excel("vendedores_libros_filtrados.xlsx")

# ===============================
# 2. Cargar mapa parroquial
# ===============================
gdf_parroquias = gpd.read_file("ecuador_parroquias.geojson")

# ===============================
# 3. Filtrar provincia Napo
# ===============================
gdf_napo = gdf_parroquias[gdf_parroquias["DPA_DESPRO"] == "SUCUMBIOS"].copy()

# Normalizar textos
gdf_napo["DPA_DESCAN"] = gdf_napo["DPA_DESCAN"].str.strip().str.upper()
gdf_napo["DPA_DESPAR"] = gdf_napo["DPA_DESPAR"].str.strip().str.upper()
df["DESCRIPCION_CANTON_EST"] = df["DESCRIPCION_CANTON_EST"].str.strip().str.upper()
df["DESCRIPCION_PARROQUIA_EST"] = df["DESCRIPCION_PARROQUIA_EST"].str.strip().str.upper()

# ===============================
# 4. Conteo por parroquia
# ===============================
conteo = df.groupby(
    ["DESCRIPCION_CANTON_EST", "DESCRIPCION_PARROQUIA_EST"]
).size().reset_index(name="vendedores")

# ===============================
# 5. Cruce mapa + datos
# ===============================
gdf_merge = gdf_napo.merge(
    conteo,
    left_on=["DPA_DESCAN", "DPA_DESPAR"],
    right_on=["DESCRIPCION_CANTON_EST", "DESCRIPCION_PARROQUIA_EST"],
    how="left"
)

gdf_merge = gpd.GeoDataFrame(gdf_merge, geometry="geometry")
gdf_merge["vendedores"] = gdf_merge["vendedores"].fillna(0)

# ===============================
# 6. Mapa estático
# ===============================
fig, ax = plt.subplots(figsize=(12, 10))
gdf_merge.plot(
    ax=ax,
    column="vendedores",
    cmap="OrRd",
    legend=True,
    edgecolor="gray",
    linewidth=0.5
)
ax.set_title("Mapa de Calor: Vendedores de Libros por Parroquia - Sucumbios", fontsize=14)
ax.axis("off")

for idx, row in gdf_merge.iterrows():
    if row["geometry"] is not None and row["geometry"].centroid.is_valid:
        plt.annotate(
            text=row["DPA_DESPAR"].title(),
            xy=(row["geometry"].centroid.x, row["geometry"].centroid.y),
            ha="center",
            fontsize=7,
            color="black"
        )

plt.tight_layout()
plt.show()

# ===============================
# 7. Mapa interactivo con Folium
# ===============================

# Reproyección
gdf_merge = gdf_merge.to_crs(epsg=4326)

# 🔧 ARREGLAR GEOMETRÍAS (PASO CRÍTICO)
gdf_merge["geometry"] = gdf_merge["geometry"].buffer(0)
gdf_merge = gdf_merge[
    gdf_merge["geometry"].notnull() &
    ~gdf_merge["geometry"].is_empty
]

# Crear mapa
m = folium.Map(location=[-0.9, -77.8], zoom_start=8)

folium.GeoJson(
    gdf_merge,
    tooltip=GeoJsonTooltip(
        fields=["DPA_DESPAR", "vendedores"],
        aliases=["Parroquia", "Vendedores"],
        localize=True
    ),
    style_function=lambda x: {
        "fillColor": "#ff6e54",
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.7,
    }
).add_to(m)

print("🔢 Total de registros (vendedores) considerados:", df.shape[0])

m.save("mapa_interactivo_sucumbios.html")
print("✅ Mapa interactivo guardado como 'mapa_interactivo_sucumbios.html'")
