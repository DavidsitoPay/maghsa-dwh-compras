# Modulo de captura y mantenimiento de datos de compras

Modulo minimo de ingesta validada, construido para resolver un problema operativo
real: el personal de compras de MAGHSA no puede tener acceso directo a la consola
de AWS. Este modulo expone un formulario web publico que escribe (con validacion)
directamente en la zona `raw/` del Data Warehouse, sin exponer ninguna credencial
de AWS al usuario final.

Corresponde a las funcionalidades #6 (modulo de captura sin acceso a AWS) y #7
(validacion de reglas de negocio en tiempo de ingesta) del avance funcional del
proyecto.

## Arquitectura

```
Formulario (index.html, alojado como sitio estatico en S3)
        |
        | fetch() POST (JSON)
        v
AWS Lambda (lambda_function.py) -- Function URL publica --
        |
        | valida codigo de acceso + reglas de negocio
        | lee/escribe CSV directamente en S3
        v
Bucket de datos (zona raw/): proveedores, productos, categorias, compras
```

Dos buckets separados, a proposito:

- `maghsa-dwh-compras-070366844944` -- datos reales del Data Warehouse (privado).
- `maghsa-captura-web-070366844944` -- unicamente el archivo `index.html` publico
  (sitio estatico). Nunca se mezcla con el bucket de datos.

## Que valida la Lambda antes de escribir

- Que el proveedor y el producto elegidos existan en sus respectivos maestros.
- Que el producto elegido este realmente asociado a ese proveedor (`proveedor_x_producto`) al
  capturar una compra -- ya no basta con que el producto exista en el maestro.
- Que la unidad organizacional elegida exista en el catalogo `unidades_organizacionales`.
- Que la cantidad y el precio unitario sean mayores a cero.
- Que la fecha no sea futura.
- Al crear/editar un proveedor: que las categorias de producto marcadas sean compatibles con las
  categorias de proveedor marcadas (`categoria_proveedor_x_categoria_producto`), y que los
  productos marcados pertenezcan a esas categorias.

Si algo falla, no se escribe nada en S3 y se devuelve el detalle del error.

## Modelo de datos (v2 -- normalizado)

`categoria_proveedor` dejo de ser una columna de texto libre en `proveedores`: un proveedor
puede pertenecer a mas de una categoria (ejemplo real en el dataset: un mismo proveedor es
"Repuestos" y "Combustibles" a la vez). Se normalizo en tablas puente, con una tabla adicional
de regla de negocio que define que categorias de producto son validas para cada categoria de
proveedor -- es la que filtra los checkboxes del formulario en cascada. El detalle completo del
esquema esta en `/modelo-dimensional/README.md`.

## Operaciones soportadas

**CRUD completo** (`listar`, `crear`, `actualizar`, `eliminar`) sobre: `proveedores`,
`productos`, `categorias`, `categorias_proveedor`, `unidades_organizacionales`, `compras`.

Crear/actualizar un proveedor es una operacion compuesta: en una sola llamada escribe la fila
base del proveedor y reemplaza sus filas en las tres tablas puente (categorias de proveedor,
categorias de producto, productos especificos) y en el contacto, segun lo que se haya marcado en
el formulario.

**Solo lectura** (`listar` unicamente, alimentan los checkboxes/dropdowns del formulario):
`proveedor_categoria_proveedor`, `categoria_proveedor_x_categoria_producto`,
`proveedor_categoria_producto`, `proveedor_x_producto`, `contacto_proveedor`.

Las compras nuevas capturadas desde el formulario se acumulan en un archivo propio
(`raw/compras/anio=2026/mes=09/registro_compras_web.csv`), separado del historico
original usado en la validacion funcional de la entrega anterior, para no
mezclarlos ni sobrescribirlos.

## Seguridad de esta fase (cuenta personal / pruebas)

- **Codigo de acceso compartido**: una sola clave, validada dentro de la propia
  Lambda (variable de entorno `ACCESS_CODE`). No hay usuarios, sesiones ni roles.
  Es intencionalmente minimo: el objetivo es evitar que alguien con el enlace
  borre o modifique datos por accidente, no sustituir un sistema de autenticacion.
- El rol de IAM de la Lambda (`maghsa-captura-lambda-role`) tiene permisos
  minimos: solo `s3:GetObject` y `s3:PutObject`, y solo sobre `raw/*` del bucket
  de datos. No puede tocar `curated/`, `analytics/` ni ningun otro recurso.
- El bucket del formulario (`maghsa-captura-web-070366844944`) es publico
  **unicamente para lectura** del archivo estatico; el bucket de datos sigue
  privado.

## Costo (capa gratuita, verificado)

Con el volumen de pruebas de esta entrega (unas pocas invocaciones):

- Lambda: 1,000,000 de solicitudes y 400,000 GB-segundo gratis **por mes, de
  forma permanente** (no solo en el primer año). Una invocacion real de prueba
  factura ~0.1-0.2 GB-segundo -- muy por debajo del limite.
- Lambda Function URL: sin costo adicional, es parte de Lambda.
- S3 (ambos buckets): el volumen de datos es de unos pocos KB; el costo de
  almacenamiento y solicitudes es una fraccion de centavo al mes.

Costo total estimado de esta fase: **$0.00**.

## Que hay que cambiar para pasar a la cuenta empresarial

El codigo esta escrito para que el cambio de entorno sea solo configuracion,
nunca reescribir logica:

1. **Bucket de datos**: cambiar la variable de entorno `BUCKET_NAME` de la
   Lambda al bucket real de la cuenta empresarial. No hay ninguna referencia al
   nombre del bucket escrita directamente en el codigo.
2. **Codigo de acceso -> autenticacion real**: reemplazar la validacion de
   `ACCESS_CODE` por AWS Cognito (o el proveedor de identidad que use la
   empresa). El punto de cambio es una sola funcion (`lambda_handler`, la
   validacion al inicio); el resto de la logica (listar/crear/actualizar/
   eliminar) no depende de como se autentico el usuario y no se toca.
3. **Rol de IAM**: crear el mismo rol (misma politica minima) apuntando al
   bucket de datos real.
4. **Nombre e identificador de la funcion**: se puede desplegar la misma
   `lambda_function.py` con otro nombre de funcion sin cambios de codigo.
5. **CORS de la Function URL**: restringir `AllowOrigins` al dominio real donde
   quede alojado el formulario en produccion, en vez de `*`.
6. **Hosting del formulario**: si la empresa ya tiene un dominio o portal
   interno, `index.html` se puede alojar ahi directamente; solo hay que
   actualizar el valor por defecto de "URL de la funcion" dentro del archivo
   (o quitarlo y dejar que el usuario lo configure).

Ningun otro archivo ni logica de negocio (validaciones, generacion de IDs,
lectura/escritura de CSV) requiere cambios entre el entorno personal y el
empresarial.

## Recursos creados en esta fase (cuenta personal, us-east-1)

- Funcion Lambda: `maghsa-captura-compras`
- Rol de IAM: `maghsa-captura-lambda-role`
- Bucket del formulario: `maghsa-captura-web-070366844944`
- Function URL: publica, `AuthType=NONE` + codigo de acceso propio de la Lambda
