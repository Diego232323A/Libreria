import geopandas as gpd

# 2. Cargar el mapa de parroquias del Ecuador
gdf_parroquias = gpd.read_file("ecuador_parroquias.geojson")

print(gdf_parroquias.columns)
