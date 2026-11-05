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

- Entrada: el cuerpo es un objeto JSON de hasta 100 000 caracteres (se acepta `isBase64Encoded`); `entidad`, `accion` e identificadores son texto y `datos` es un objeto. Un cuerpo mal formado responde 400 con `errores[]`.
- Acceso: `codigo_acceso` debe ser texto y coincidir con `ACCESS_CODE` (comparacion con `hmac.compare_digest`); si no, 403 generico. Si `ACCESS_CODE` esta vacio o no definido, ningun codigo autentica (401).
- Texto de los maestros: campos obligatorios no vacios, longitud maxima por campo, sin saltos de linea ni caracteres de control, y sin iniciar con `=`, `@`, `+` o `-` (proteccion contra inyeccion de formulas en CSV). Los telefonos pueden iniciar con `+`.
- Unicidad de nombre, sin distinguir mayusculas, en categorias, categorias de proveedor y unidades organizacionales.
- Referencias: la categoria de un producto existe; en una compra existen el proveedor, el producto (asociado a ese proveedor en `proveedor_x_producto`), la categoria y la unidad organizacional.
- Valores cerrados: `estado` de proveedor `vigente` o `inactivo`; `moneda` `GTQ`.
- Condicion de pago: `contado` o `N dias` (1 a 3 digitos); se guarda normalizada (`30 días` queda `30 dias`).
- Cantidad y precio unitario: decimales mayores a cero, sin notacion cientifica. Lead time (`lead_time_dias`): obligatorio, entero de 0 a 9999.
- Fecha: fecha real `AAAA-MM-DD`, no futura según la fecha actual de Guatemala (UTC-6); cualquier fecha pasada es válida. Se guarda normalizada (`2026-1-5` queda `2026-01-05`).
- Al actualizar, los campos no enviados conservan su valor y el registro resultante se valida con las mismas reglas.
- Proveedores: al crear debe marcarse al menos una categoria de proveedor; las categorias de producto y los productos marcados existen, son compatibles con las categorias de proveedor (`categoria_proveedor_x_categoria_producto`) y los productos pertenecen a categorias marcadas.

Si algo falla, no se escribe nada en S3 y se devuelve el detalle del error.

## Respuestas

- `200` / `201`: operacion aplicada (`201` al crear).
- `400`: validacion o entrada invalida, con `errores[]`. No se escribe nada.
- `401`: `ACCESS_CODE` no configurado en la Lambda; ningun codigo autentica.
- `403`: codigo de acceso invalido o ausente; mensaje generico.
- `404`: el identificador no existe.
- `409`: eliminar un registro en uso, con `errores[]`. Proveedor o unidad con compras; producto con compras o relaciones proveedor-producto; categoria con productos, compras, categorias de producto de proveedores o reglas; categoria de proveedor con proveedores o reglas. No se borra nada.
- `500`: `{"errores": ["Error interno del servidor."]}`, sin detalle; el detalle queda solo en el log de CloudWatch.

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

Las compras nuevas capturadas desde el formulario se acumulan en un archivo propio (`raw/compras_web/registro_compras_web.csv`, fuera de la jerarquia `anio=/mes=`) con identificador `OCW` + 4 digitos (`OCW0001`), separado del historico `OC0001..OC0097`, para no mezclarlos ni sobrescribirlos.

## Seguridad de esta fase (cuenta personal / pruebas)

- **Codigo de acceso compartido**: una sola clave, validada dentro de la propia
  Lambda (variable de entorno `ACCESS_CODE`). No hay usuarios, sesiones ni roles.
  Es intencionalmente minimo: el objetivo es evitar que alguien con el enlace
  borre o modifique datos por accidente, no sustituir un sistema de autenticacion.
- El rol de IAM de la Lambda (`maghsa-captura-lambda-role`) tiene permisos
  minimos: `s3:GetObject` y `s3:PutObject` sobre `raw/*` del bucket de datos, y
  `s3:ListBucket` limitado al prefijo `raw/*` (para comprobar referencias al eliminar).
  No puede tocar `curated/`, `analytics/` ni ningun otro recurso.
- El bucket del formulario (`maghsa-captura-web-070366844944`) es publico
  **unicamente para lectura** del archivo estatico; el bucket de datos sigue
  privado.
- **Limitaciones conocidas:** no hay limite de intentos del codigo de acceso (la Function URL no lo ofrece; WAF agregaria costo y complejidad); escrituras simultaneas sobre el mismo CSV pueden perder una.

## Pruebas

Tests locales con pytest y un stub de boto3 en memoria (sin AWS ni red):

```bash
python -m pip install pytest
python -m pytest lambda-captura/tests -q
```

El zip de despliegue incluye solo `lambda_function.py`, no `tests/`.

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
