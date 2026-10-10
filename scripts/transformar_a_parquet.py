"""
Transforma los CSV de raw/ a Parquet (curated/ y analytics/) para el Data Warehouse
serverless de MAGHSA, S.A.

Lee desde la carpeta de trabajo del AWS API MCP Server (donde ya se copiaron los CSV
de raw/) y escribe ahi mismo curated/ y analytics/, listos para subir a S3 con
`aws s3 cp ... --recursive`.

Requiere: pandas, pyarrow
    pip install pandas pyarrow
"""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

WORKDIR = Path(r"C:\Users\david\AppData\Local\Temp\aws-api-mcp\workdir")
RAW = WORKDIR / "raw"
CURATED = WORKDIR / "curated"
ANALYTICS = WORKDIR / "analytics"

DIAS_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def to_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", compression="snappy", index=False)


def leer_catalogo_simple(nombre_carpeta: str, nombre_archivo: str) -> pd.DataFrame:
    return pd.read_csv(RAW / nombre_carpeta / nombre_archivo, dtype=str)


def main() -> None:
    # --- Maestros y catalogos ---
    proveedores = leer_catalogo_simple("proveedores", "maestro_proveedores.csv")
    productos = leer_catalogo_simple("productos", "maestro_productos.csv")
    categorias = leer_catalogo_simple("categorias", "catalogo_categorias.csv")
    categorias_proveedor = leer_catalogo_simple("categorias_proveedor", "categorias_proveedor.csv")
    unidades_organizacionales = leer_catalogo_simple(
        "unidades_organizacionales", "unidades_organizacionales.csv"
    )

    # --- Relaciones normalizadas proveedor <-> categorias <-> producto ---
    proveedor_categoria_proveedor = leer_catalogo_simple(
        "proveedor_categoria_proveedor", "proveedor_categoria_proveedor.csv"
    )
    categoria_proveedor_x_categoria_producto = leer_catalogo_simple(
        "categoria_proveedor_x_categoria_producto", "categoria_proveedor_x_categoria_producto.csv"
    )
    proveedor_categoria_producto = leer_catalogo_simple(
        "proveedor_categoria_producto", "proveedor_categoria_producto.csv"
    )
    proveedor_x_producto = leer_catalogo_simple("proveedor_x_producto", "proveedor_x_producto.csv")
    contacto_proveedor = leer_catalogo_simple("contacto_proveedor", "contacto_proveedor.csv")

    compras = pd.read_csv(RAW / "compras" / "anio=2026" / "mes=08" / "registro_compras.csv", dtype=str)

    # --- Campos derivados en compras ---
    compras["cantidad"] = compras["cantidad"].astype(float)
    compras["precio_unitario"] = compras["precio_unitario"].astype(float)
    compras["lead_time_dias"] = compras["lead_time_dias"].astype("int32")
    compras["fecha_dt"] = pd.to_datetime(compras["fecha"])
    compras["fecha_id"] = compras["fecha_dt"].dt.strftime("%Y%m%d")
    compras["monto_total"] = (compras["cantidad"] * compras["precio_unitario"]).round(2)
    compras["anio"] = compras["fecha_dt"].dt.strftime("%Y")
    compras["mes"] = compras["fecha_dt"].dt.strftime("%m")

    # --- curated/ : datos validados, aun desnormalizados ---
    to_parquet(proveedores, CURATED / "proveedores" / "proveedores.parquet")
    to_parquet(productos, CURATED / "productos" / "productos.parquet")
    to_parquet(categorias, CURATED / "categorias" / "categorias.parquet")
    to_parquet(categorias_proveedor, CURATED / "categorias_proveedor" / "categorias_proveedor.parquet")
    to_parquet(
        unidades_organizacionales,
        CURATED / "unidades_organizacionales" / "unidades_organizacionales.parquet",
    )
    to_parquet(
        proveedor_categoria_proveedor,
        CURATED / "proveedor_categoria_proveedor" / "proveedor_categoria_proveedor.parquet",
    )
    to_parquet(
        categoria_proveedor_x_categoria_producto,
        CURATED
        / "categoria_proveedor_x_categoria_producto"
        / "categoria_proveedor_x_categoria_producto.parquet",
    )
    to_parquet(
        proveedor_categoria_producto,
        CURATED / "proveedor_categoria_producto" / "proveedor_categoria_producto.parquet",
    )
    to_parquet(proveedor_x_producto, CURATED / "proveedor_x_producto" / "proveedor_x_producto.parquet")
    to_parquet(contacto_proveedor, CURATED / "contacto_proveedor" / "contacto_proveedor.parquet")
    for (anio, mes), grupo in compras.groupby(["anio", "mes"]):
        to_parquet(
            grupo.drop(columns=["fecha_dt"]),
            CURATED / "compras" / f"anio={anio}" / f"mes={mes}" / "compras.parquet",
        )

    # --- analytics/ : modelo dimensional (esquema estrella + tablas puente) ---
    to_parquet(proveedores, ANALYTICS / "dim_proveedor" / "dim_proveedor.parquet")
    to_parquet(productos, ANALYTICS / "dim_producto" / "dim_producto.parquet")
    to_parquet(categorias, ANALYTICS / "dim_categoria" / "dim_categoria.parquet")
    to_parquet(
        categorias_proveedor, ANALYTICS / "dim_categoria_proveedor" / "dim_categoria_proveedor.parquet"
    )
    to_parquet(
        unidades_organizacionales,
        ANALYTICS / "dim_unidad_organizacional" / "dim_unidad_organizacional.parquet",
    )
    to_parquet(
        contacto_proveedor, ANALYTICS / "dim_contacto_proveedor" / "dim_contacto_proveedor.parquet"
    )
    to_parquet(
        proveedor_categoria_proveedor,
        ANALYTICS / "puente_proveedor_categoria_proveedor" / "puente_proveedor_categoria_proveedor.parquet",
    )
    to_parquet(
        categoria_proveedor_x_categoria_producto,
        ANALYTICS
        / "categoria_proveedor_x_categoria_producto"
        / "categoria_proveedor_x_categoria_producto.parquet",
    )
    to_parquet(
        proveedor_categoria_producto,
        ANALYTICS / "puente_proveedor_categoria_producto" / "puente_proveedor_categoria_producto.parquet",
    )
    to_parquet(
        proveedor_x_producto, ANALYTICS / "puente_proveedor_producto" / "puente_proveedor_producto.parquet"
    )

    hechos_cols = [
        "id_compra", "fecha_id", "proveedor_id", "producto_id", "categoria_id",
        "unidad_organizacional_id", "cantidad", "precio_unitario", "monto_total",
        "moneda", "condicion_pago", "lead_time_dias",
    ]
    for (anio, mes), grupo in compras.groupby(["anio", "mes"]):
        to_parquet(
            grupo[hechos_cols],
            ANALYTICS / "hechos_compras" / f"anio={anio}" / f"mes={mes}" / "hechos_compras.parquet",
        )

    # --- dim_tiempo : generada para el rango de fechas usado (junio-agosto 2026) ---
    fechas = pd.date_range("2026-06-01", "2026-08-31", freq="D")
    dim_tiempo_table = pa.table(
        {
            "fecha_id": pa.array(fechas.strftime("%Y%m%d"), type=pa.string()),
            "fecha": pa.array(fechas.date, type=pa.date32()),
            "anio": pa.array(fechas.year, type=pa.int32()),
            "trimestre": pa.array(fechas.quarter, type=pa.int32()),
            "mes": pa.array(fechas.month, type=pa.int32()),
            "nombre_mes": pa.array([MESES_ES[m] for m in fechas.month], type=pa.string()),
            "dia": pa.array(fechas.day, type=pa.int32()),
            "dia_semana": pa.array([DIAS_ES[d] for d in fechas.dayofweek], type=pa.string()),
        }
    )
    dim_tiempo_path = ANALYTICS / "dim_tiempo" / "dim_tiempo.parquet"
    dim_tiempo_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(dim_tiempo_table, dim_tiempo_path, compression="snappy")

    print("Listo. Archivos Parquet generados en:")
    print(f" - {CURATED}")
    print(f" - {ANALYTICS}")


if __name__ == "__main__":
    main()
