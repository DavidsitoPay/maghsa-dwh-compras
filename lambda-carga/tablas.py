"""Mapa de tablas del DWH: vivas en Glue, etapa temporal (tmp_a_*) y curated (tmp_c_*).

Unica copia del mapa; la usan el runner y el test de contrato de athena/etl/.
"""

HECHOS = "hechos_compras"

ETAPA_DE = {
    "dim_proveedor": "tmp_a_proveedores",
    "dim_producto": "tmp_a_productos",
    "dim_contacto_proveedor": "tmp_a_contacto_proveedor",
    "puente_proveedor_categoria_proveedor": "tmp_a_proveedor_categoria_proveedor",
    "puente_proveedor_categoria_producto": "tmp_a_proveedor_categoria_producto",
    "puente_proveedor_producto": "tmp_a_proveedor_x_producto",
    "dim_categoria": "tmp_a_categorias",
    "dim_categoria_proveedor": "tmp_a_categorias_proveedor",
    "dim_unidad_organizacional": "tmp_a_unidades_organizacionales",
    "categoria_proveedor_x_categoria_producto": "tmp_a_categoria_proveedor_x_categoria_producto",
    "dim_tiempo": "tmp_a_tiempo",
    HECHOS: "tmp_a_hechos",
}

TABLAS_VIVAS = tuple(ETAPA_DE)

TMP_CURATED = (
    "tmp_c_proveedores",
    "tmp_c_productos",
    "tmp_c_contacto_proveedor",
    "tmp_c_proveedor_categoria_proveedor",
    "tmp_c_proveedor_categoria_producto",
    "tmp_c_proveedor_x_producto",
    "tmp_c_categorias",
    "tmp_c_categorias_proveedor",
    "tmp_c_unidades_organizacionales",
    "tmp_c_categoria_proveedor_x_categoria_producto",
    "tmp_c_compras",
)
