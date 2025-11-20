import pandas as pd
import os
import csv
import sys
import re

filename = "SRI_RUC_Sucumbios.csv"

# =============================================
#   FUNCIÓN DE LECTURA AUTOMÁTICA DEL ARCHIVO
# =============================================
def read_table_auto(path):
    if not os.path.exists(path):
        print(f"Archivo no encontrado: {path}")
        print("\nArchivos en el directorio actual:")
        for f in os.listdir("."):
            print(" -", f)
        sys.exit(1)

    sep = None
    if path.lower().endswith(".csv"):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            sample = fh.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=['|', '  '])
                sep = dialect.delimiter
            except csv.Error:
                sep = None

    try:
        if path.lower().endswith(".csv"):
            return pd.read_csv(path, encoding="utf-8", sep=sep, engine='python', low_memory=False)
        else:
            return pd.read_excel(path)
    except Exception:
        for candidate in [',',';', '\t', '|', '  ']:
            try:
                print(f"Reintentando con sep='{candidate}' ...")
                return pd.read_csv(path, encoding="utf-8", sep=candidate, engine='python')
            except:
                continue
        raise


# ==========================
#      CARGA DEL DATASET
# ==========================
df = read_table_auto(filename)

# =============================================
#        NORMALIZACIÓN DE TEXTO
# =============================================
df["ACTIVIDAD_ECONOMICA"] = (
    df["ACTIVIDAD_ECONOMICA"]
    .astype(str)
    .str.normalize("NFKD")
    .str.encode("ascii", errors="ignore")
    .str.decode("utf-8")
    .str.lower()
)


# =============================================
# PALABRAS CLAVE PARA VENTA DE LIBROS (INCLUSIÓN)
# =============================================
palabras_clave = [
    r"venta.*libro",
    r"comercializacion.*libro",
    r"libreria",
    r"libros",
    r"distribucion.*libro",
    r"edicion.*libro",
    r"suministro.*libro",
    r"tienda.*libro",
]

regex_incluir = "|".join(palabras_clave)
filtro_incluir = df["ACTIVIDAD_ECONOMICA"].str.contains(regex_incluir, na=False, flags=re.IGNORECASE)


# =============================================
# PALABRAS CLAVE PARA EXCLUSIÓN (CONTABILIDAD)
# =============================================
palabras_excluir = [
    "contabilidad",
    "contable",
    "tenedur",
    "auditori",
    "fiscal",
    "tribut",
    "impuesto",
    "nomina",
    "nómina",
    "balance",
    "financier",
    "estados financieros",
    "cuentas",
    "registro contable",
]

regex_excluir = "|".join(palabras_excluir)
filtro_excluir = df["ACTIVIDAD_ECONOMICA"].str.contains(regex_excluir, na=False, flags=re.IGNORECASE)


# =============================================
#       FILTRADO FINAL DE ACTIVIDAD ECONÓMICA
# =============================================
df_actividad = df[filtro_incluir & ~filtro_excluir]


# =============================================
# CÓDIGOS CIIU RELACIONADOS A VENTA DE LIBROS
# =============================================
codigos_ciiu_libros = [
    "G4761",
    "G476100",
    "G476101",
    "G476102",
    "5811",
    "58110",
]

filtro_ciiu = df["CODIGO_CIIU"].astype(str).str.startswith(tuple(codigos_ciiu_libros))

df_ciiu = df[filtro_ciiu]


# =============================================
# UNIÓN FINAL: ACTIVIDAD + CIIU
# =============================================
df_libros = pd.concat([df_actividad, df_ciiu]).drop_duplicates()

print(f"Número de vendedores de libros encontrados: {len(df_libros)}")


# =============================================
# FUNCIÓN SEGURA PARA GUARDAR EL EXCEL
# (NO FALLA SI EL ARCHIVO ESTÁ ABIERTO)
# =============================================
def safe_save_excel(df, filename):
    temp_filename = "_temp_output.xlsx"

    # Guardar en archivo temporal
    df.to_excel(temp_filename, index=False)

    try:
        if os.path.exists(filename):
            os.remove(filename)
    except PermissionError:
        print("\n⚠ El archivo Excel está ABIERTO. Intentando reemplazo forzado...")

    try:
        os.replace(temp_filename, filename)
        print(f"Archivo generado correctamente: {filename}")
    except PermissionError:
        print("\n❌ No se pudo reemplazar el archivo porque está ABIERTO en Excel.")
        print("➡ Por favor ciérralo y vuelve a ejecutar el script.")
        os.remove(temp_filename)


# =============================================
# GUARDAR RESULTADO
# =============================================
output_filename = "vendedores_libros_filtrados.xlsx"
safe_save_excel(df_libros, output_filename)
