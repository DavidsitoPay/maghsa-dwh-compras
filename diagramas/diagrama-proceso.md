# Diagrama de proceso (equivalente a actividad UML)

Flujo del proceso de extremo a extremo, desde la carga del archivo fuente hasta el consumo del
dato en el dashboard de Power BI.

```mermaid
flowchart TD
    Start([Inicio]) --> A[Cargar archivos fuente\nCSV: compras, proveedores, productos, categorias]
    A --> B[Subir a S3 - zona raw/]
    B --> C{Datos válidos?}
    C -- No --> C1[Registrar error y notificar]
    C1 --> End1([Fin - requiere corrección])
    C -- Sí --> D[Transformar y calcular campos derivados\nfecha_id, monto_total]
    D --> E[Convertir a Parquet - zona curated/]
    E --> F[Cargar a zona analytics/\nmodelo dimensional]
    F --> G[Registrar tablas en AWS Glue Data Catalog]
    G --> H[Ejecutar crawler o DDL en Athena]
    H --> I[Consultar KPIs vía Amazon Athena]
    I --> J[Actualizar dashboard en Power BI]
    J --> End([Fin])
```

Ver la organización de zonas en S3 en [`/s3-structure/`](../s3-structure) y la definición de
tablas en [`/glue/`](../glue).
