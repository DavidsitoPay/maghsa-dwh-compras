# Scripts

| Script | Para qué sirve |
|---|---|
| `generar_datos_dummy.py` | Genera y anexa datos sintéticos (órdenes de enero a octubre de 2026) a `sample-data/`; usa semilla fija y solo la biblioteca estándar |

## generar_datos_dummy.py

```bash
python scripts/generar_datos_dummy.py
```

Se ejecuta desde la raíz del repo. Conserva `OC0001`-`OC0010` y regenera `sample-data/registro_compras.csv`.

La carga a Parquet (`curated/` y `analytics/`) se hace solo con `athena/etl/`.
