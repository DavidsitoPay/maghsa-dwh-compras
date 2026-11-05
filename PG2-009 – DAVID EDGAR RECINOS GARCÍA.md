**UNIVERSIDAD MARIANO GÁLVEZ DE GUATEMALA**

**FACULTAD DE INGENIERÍA EN SISTEMAS DE**

**INFORMACIÓN**

**DESARROLLO E IMPLEMENTACIÓN DE UN DATA WAREHOUSE**   
**SERVERLESS EN AWS PARA EL ANÁLISIS DE COMPRAS MEDIANTE**   
**S3, GLUE DATA CATALOG Y ATHENA, CON DASHBOARDS DE**   
**INDICADORES Y ENFOQUE DE MANTENIMIENTO DE BAJO**   
**COSTO**  

**DAVID EDGAR RECINOS GARCÍA**

**Guatemala, noviembre de 2026.**

**UNIVERSIDAD MARIANO GÁLVEZ DE GUATEMALA**

**FACULTAD DE INGENIERÍA EN SISTEMAS DE**

**INFORMACIÓN**

**DESARROLLO E IMPLEMENTACIÓN DE UN DATA WAREHOUSE SERVERLESS EN AWS PARA EL ANÁLISIS DE COMPRAS MEDIANTE S3, GLUE DATA CATALOG Y ATHENA, CON DASHBOARDS DE INDICADORES Y ENFOQUE DE MANTENIMIENTO DE BAJO COSTO**

**TRABAJO DE GRADUACIÓN PRESENTADO**

**POR:**

**DAVID EDGAR RECINOS GARCÍA**

**PREVIO A OPTAR AL GRADO ACADÉMICO DE**

**LICENCIADO EN INGENIERÍA EN SISTEMAS DE**

**INFORMACIÓN Y CIENCIAS DE LA COMPUTACIÓN**

**Y TÍTULO PROFESIONAL DE**

**INGENIERO EN SISTEMAS DE INFORMACIÓN**

**Y CIENCIAS DE LA COMPUTACIÓN**

**Guatemala, noviembre de 2026.**

**AUTORIDADES DE LA FACULTAD Y ASESOR DEL TRABAJO**

**DE GRADUACIÓN.**

| DECANO DE LA FACULTAD: | ING. JORGE ALBERTO ARIAS TOBAR |
| :---- | :---- |
| **SECRETARIO DE LA FACULTAD:** | M.A. HUGO ADALBERTO HERNÁNDEZ SANTIZO |
| **ASESOR:** | M.A. EDDY ORLANDO HERNANDEZ CHOC |

**REGLAMENTO DE TESIS**

**Artículo 8: RESPONSABILIDAD**

Solamente el autor es responsable de los conceptos expresados en el trabajo de tesis. Su aprobación en manera alguna implica responsabilidad para la Universidad.

**Índice**

- [Introducción](#introducción)
- [Capítulo I - Marco Conceptual](#capítulo-i---marco-conceptual)
  - [1.1 Antecedentes](#11-antecedentes)
  - [1.2 Descripción del problema](#12-descripción-del-problema)
    - [1.2.1 Preguntas de investigación](#121-preguntas-de-investigación)
  - [1.3 Justificación](#13-justificación)
  - [1.4 Objetivos](#14-objetivos)
    - [1.4.1 Objetivo general](#141-objetivo-general)
    - [1.4.2 Objetivos específicos](#142-objetivos-específicos)
  - [1.5 Alcance](#15-alcance)
  - [1.6 Limitaciones](#16-limitaciones)
- [Capítulo II - Marco Teórico](#capítulo-ii---marco-teórico)
  - [2.1 Fundamentos de Data Warehouse y modelado analítico](#21-fundamentos-de-data-warehouse-y-modelado-analítico)
    - [2.1.1 Evolución de los Data Warehouses: de enfoques tradicionales a arquitecturas en la nube](#211-evolución-de-los-data-warehouses-de-enfoques-tradicionales-a-arquitecturas-en-la-nube)
    - [2.1.2 ETL vs ELT: estrategias modernas para DWH en la nube](#212-etl-vs-elt-estrategias-modernas-para-dwh-en-la-nube)
    - [2.1.3 Calidad de datos en entornos analíticos: consistencia, completitud, unicidad y trazabilidad](#213-calidad-de-datos-en-entornos-analíticos-consistencia-completitud-unicidad-y-trazabilidad)
  - [2.2 Arquitecturas serverless aplicadas a analítica](#22-arquitecturas-serverless-aplicadas-a-analítica)
    - [2.2.1 Computación serverless: principios, ventajas, limitaciones y modelos de costo](#221-computación-serverless-principios-ventajas-limitaciones-y-modelos-de-costo)
    - [2.2.2 Gobierno de datos en arquitecturas serverless: catálogo, metadatos, linaje y acceso](#222-gobierno-de-datos-en-arquitecturas-serverless-catálogo-metadatos-linaje-y-acceso)
    - [2.2.3 Diseño de zonas de datos (raw/bronze, curated/silver, analytics/gold)](#223-diseño-de-zonas-de-datos-rawbronze-curatedsilver-analyticsgold)
  - [2.3 Componentes AWS](#23-componentes-aws)
    - [2.3.1 S3 como Data Lake: organización por prefijos, particionamiento y ciclo de vida (lifecycle)](#231-s3-como-data-lake-organización-por-prefijos-particionamiento-y-ciclo-de-vida-lifecycle)
    - [2.3.2 Glue Data Catalog: esquemas, tablas, particiones y crawler](#232-glue-data-catalog-esquemas-tablas-particiones-y-crawler)
    - [2.3.3 Athena: ejecución SQL sobre S3, optimización por particiones y formatos columnares](#233-athena-ejecución-sql-sobre-s3-optimización-por-particiones-y-formatos-columnares)
    - [2.3.4 Seguridad en analítica cloud: IAM, control de acceso, cifrado at-rest/in-transit](#234-seguridad-en-analítica-cloud-iam-control-de-acceso-cifrado-at-restin-transit)
  - [2.4 Operación de compras: analítica, indicadores y gestión](#24-operación-de-compras-analítica-indicadores-y-gestión)
    - [2.4.1 Indicadores clave de compras (KPIs): costo, ahorro, cumplimiento, lead time, proveedores](#241-indicadores-clave-de-compras-kpis-costo-ahorro-cumplimiento-lead-time-proveedores)
    - [2.4.2 Evaluación de desempeño de proveedores: calidad, puntualidad, variabilidad de precio](#242-evaluación-de-desempeño-de-proveedores-calidad-puntualidad-variabilidad-de-precio)
    - [2.4.3 Gobernanza del dato de compras: maestros (proveedor, producto), reglas y consistencia](#243-gobernanza-del-dato-de-compras-maestros-proveedor-producto-reglas-y-consistencia)
  - [2.5 BI y Dashboards: Power BI y analítica](#25-bi-y-dashboards-power-bi-y-analítica)
    - [2.5.1 Dashboards para toma de decisiones: principios de visualización de KPIs y storytelling](#251-dashboards-para-toma-de-decisiones-principios-de-visualización-de-kpis-y-storytelling)
    - [2.5.2 Modelado semántico en Power BI: medidas DAX, star schema y performance](#252-modelado-semántico-en-power-bi-medidas-dax-star-schema-y-performance)
    - [2.5.3 Gobierno del reporte: refresh, dataset, control de acceso y versionado](#253-gobierno-del-reporte-refresh-dataset-control-de-acceso-y-versionado)
- [Capítulo III - Marco Metodológico](#capítulo-iii---marco-metodológico)
  - [3.1 Ruta de investigación](#31-ruta-de-investigación)
  - [3.2 Tipo de investigación](#32-tipo-de-investigación)
  - [3.3 Análisis de factibilidad](#33-análisis-de-factibilidad)
    - [3.3.1 Factibilidad económica](#331-factibilidad-económica)
    - [3.3.2 Factibilidad operativa](#332-factibilidad-operativa)
    - [3.3.3 Factibilidad tecnológica](#333-factibilidad-tecnológica)
    - [3.3.4 Factibilidad cognoscitiva](#334-factibilidad-cognoscitiva)
    - [3.3.5 Factibilidad legal y ambiental](#335-factibilidad-legal-y-ambiental)
  - [3.4 Hipótesis](#34-hipótesis)
    - [3.4.1 Variable independiente](#341-variable-independiente)
    - [3.4.2 Variable dependiente](#342-variable-dependiente)
  - [3.5 Definición de la población y tamaño de la muestra](#35-definición-de-la-población-y-tamaño-de-la-muestra)
    - [3.5.1 Tamaño de la población](#351-tamaño-de-la-población)
    - [3.5.2 Cálculo del tamaño de la muestra](#352-cálculo-del-tamaño-de-la-muestra)
    - [3.5.3 Instrumento](#353-instrumento)
    - [3.5.4 Recolección de datos](#354-recolección-de-datos)
  - [3.6 Interpretación de resultados](#36-interpretación-de-resultados)
    - [3.6.1 Gráficos y tabulares](#361-gráficos-y-tabulares)
  - [3.7 Recursos utilizados](#37-recursos-utilizados)
  - [3.8 Cronograma](#38-cronograma)
- [Capítulo IV - Análisis de la Aplicación](#capítulo-iv---análisis-de-la-aplicación)
  - [4.1 Descripción del proyecto](#41-descripción-del-proyecto)
  - [4.2 Identificación de usuarios](#42-identificación-de-usuarios)
  - [4.3 Modelado del negocio](#43-modelado-del-negocio)
    - [4.3.1 Design Science Research (DSR)](#431-design-science-research-dsr)
    - [4.3.2 Ciclo de vida](#432-ciclo-de-vida)
    - [4.3.3 Características](#433-características)
    - [4.3.4 Fases](#434-fases)
    - [4.3.5 Artefactos](#435-artefactos)
- [Capítulo V - Diseño de la Aplicación](#capítulo-v---diseño-de-la-aplicación)
  - [5.1 Diagramas UML](#51-diagramas-uml)
    - [5.1.1 Diagrama de casos de uso](#511-diagrama-de-casos-de-uso)
    - [5.1.2 Diagrama de actividades](#512-diagrama-de-actividades)
    - [5.1.3 Diagrama de secuencia](#513-diagrama-de-secuencia)
    - [5.1.4 Diagrama de componentes](#514-diagrama-de-componentes)
    - [5.1.5 Diagrama de objetos](#515-diagrama-de-objetos)
    - [5.1.6 Diagrama de clases](#516-diagrama-de-clases)
    - [5.1.7 Diagrama de entidad relación](#517-diagrama-de-entidad-relación)
  - [5.2 Entidad Relación](#52-entidad-relación)
  - [5.3 Diagramas de infraestructura](#53-diagramas-de-infraestructura)
    - [5.3.1 Arquitectura general](#531-arquitectura-general)
    - [5.3.2 Infraestructura en AWS](#532-infraestructura-en-aws)
    - [5.3.3 Integraciones](#533-integraciones)
    - [5.3.4 Correspondencia entre objetivos y diseño](#534-correspondencia-entre-objetivos-y-diseño)
- [Conclusiones](#conclusiones)
- [Recomendaciones](#recomendaciones)
- [Glosario](#glosario)
- [Bibliografía](#bibliografía)
- [Anexos](#anexos)

**Índice de figuras**

- [Figura 1 - Arquitectura de la solución del Data Warehouse serverless](#figura-1)
- [Figura 2 - Diagrama entidad-relación del modelo dimensional de compras](#figura-2)
- [Figura 3 - Diagrama de proceso de extremo a extremo](#figura-3)
- [Figura 4 - Estructura de zonas del Data Lake en Amazon S3](#figura-4)
- [Figura 5 - Tablas del esquema dimensional registradas en AWS Glue Data Catalog](#figura-5)
- [Figura 6 - Resultado de la consulta de costo total de compras por periodo en Amazon Athena](#figura-6)
- [Figura 7 - Formulario de captura de datos de compras](#figura-7)
- [Figura 8 - Diagrama de casos de uso del sistema](#figura-8)
- [Figura 9 - Diagrama de actividades del registro de una orden de compra](#figura-9)
- [Figura 10 - Diagrama de secuencia del registro de una orden de compra](#figura-10)
- [Figura 11 - Diagrama de secuencia de la consulta de indicadores](#figura-11)
- [Figura 12 - Diagrama de componentes del sistema](#figura-12)
- [Figura 13 - Diagrama de objetos de la orden de compra OC0001](#figura-13)
- [Figura 14 - Diagrama de clases del dominio de compras](#figura-14)
- [Figura 15 - Diagrama de infraestructura de la solución en AWS](#figura-15)

**Índice de tablas**

- [Tabla 1 - Resumen general de costos](#tabla-1)
- [Tabla 2 - Factibilidad técnica de software](#tabla-2)
- [Tabla 3 - Fuentes documentales del proyecto](#tabla-3)
- [Tabla 4 - Variables e indicadores del análisis de compras](#tabla-4)
- [Tabla 5 - Costo total de compras por periodo](#tabla-5)
- [Tabla 6 - Gasto por categoría](#tabla-6)
- [Tabla 7 - Gasto por proveedor](#tabla-7)
- [Tabla 8 - Lead time promedio por proveedor](#tabla-8)
- [Tabla 9 - Recursos necesarios](#tabla-9)
- [Tabla 10 - Cronograma referencial](#tabla-10)
- [Tabla 11 - Módulos y tecnologías del Data Warehouse](#tabla-11)
- [Tabla 12 - Especificación resumida de casos de uso principales](#tabla-12)
- [Tabla 13 - Interfaces entre componentes](#tabla-13)
- [Tabla 14 - Entidades del modelo de datos](#tabla-14)
- [Tabla 15 - Recursos de infraestructura y configuración](#tabla-15)
- [Tabla 16 - Correspondencia entre objetivos, procesos y elementos de diseño](#tabla-16)
# **Introducción**

La gestión y el control del proceso de compras dependen, en gran medida, de la disponibilidad de información confiable y oportuna. En la práctica, los datos relacionados con órdenes de compra, proveedores, productos, costos, condiciones de pago y tiempos de entrega suelen generarse en diferentes sistemas transaccionales y en diversos formatos, lo cual dificulta su integración, su trazabilidad y su análisis histórico. Esta dispersión provoca que, con frecuencia, el análisis de compras se realice mediante actividades manuales como extracción de datos, depuración en hojas de cálculo y elaboración de reportes estáticos, incrementando el esfuerzo operativo, el riesgo de inconsistencias y la dificultad para sostener indicadores bajo un mismo criterio.

Ante este escenario, surge la necesidad de contar con una solución que permita consolidar la información de compras en un repositorio analítico centralizado, orientado a consultas y generación de indicadores. Sin embargo, la implementación de un Data Warehouse tradicional puede implicar infraestructura dedicada, costos fijos y una carga de mantenimiento asociada a la administración de servidores, respaldos, escalamiento y operación continua. Por ello, el enfoque serverless representa una alternativa adecuada cuando se busca simplicidad operativa y control del costo, ya que permite construir capacidades de almacenamiento, catalogación y consulta analítica con servicios administrados y escalables bajo demanda.

El trabajo desarrolla la construcción de un Data Warehouse serverless en AWS para el análisis de compras, utilizando Amazon S3 como capa de almacenamiento, AWS Glue Data Catalog como repositorio de metadatos técnicos y Amazon Athena como motor de consulta SQL sobre los datos almacenados. A partir de esta base, los resultados analíticos se materializan mediante dashboards de indicadores en Power BI, de forma que la información consolidada pueda visualizarse en métricas y tendencias relevantes para la toma de decisiones. La selección de Power BI responde a un criterio de economía y experiencia previa, privilegiando una herramienta que permita producir tableros con rapidez y menor curva de aprendizaje, sin dejar de aprovechar el motor de consulta serverless de Athena.

A lo largo de los dos semestres, el desarrollo se estructura como un proceso incremental que avanza desde la definición conceptual hasta la implementación y evaluación. En una primera etapa, se delimita el problema y se establecen los fundamentos que justifican la adopción de un enfoque serverless con mantenimiento de bajo costo. Posteriormente, se define el modelo dimensional de compras (hechos y dimensiones) para soportar los indicadores seleccionados, asegurando que la solución responda a necesidades de análisis frecuentes como comparaciones por periodo, por proveedor, por categorías de gasto y por unidades organizacionales. En paralelo, se diseña una organización lógica del almacenamiento en S3 que facilite la consulta y el control del ciclo de vida de los datos.

En la fase de implementación, se construye el catálogo de metadatos en Glue Data Catalog para habilitar el descubrimiento y la consulta consistente de los datasets. Luego, se habilitan consultas analíticas en Athena para obtener métricas y agregaciones que alimenten los indicadores definidos. Con esta base, se construyen los dashboards en Power BI, conectados a Athena, orientados a la visualización de KPIs y tendencias de compras. Esta capa de presentación permite evaluar el valor práctico de la solución, al traducir los datos consolidados en información interpretable y utilizable por usuarios de negocio.

Finalmente, se contempla una validación del funcionamiento de extremo a extremo (S3 → Glue Data Catalog → Athena → Power BI), apoyada en pruebas de consultas y verificación de indicadores. Además, se incorpora un análisis orientado al objetivo de bajo costo de mantenimiento, considerando aspectos operativos y prácticas que permitan sostener la solución con mínima administración, tales como organización adecuada de datos, control de accesos, documentación del flujo y recomendaciones para un uso eficiente de consultas. De esta manera, el documento integra los elementos conceptuales, metodológicos y técnicos necesarios para demostrar la viabilidad de un Data Warehouse serverless aplicado al análisis de compras, manteniendo el enfoque en simplicidad, escalabilidad y sostenibilidad operativa, sin anticipar conclusiones sobre los resultados que se obtendrán.

# **Capítulo I - Marco Conceptual**

## **1.1 Antecedentes**

Durante las últimas décadas, las organizaciones han incrementado considerablemente la generación de datos provenientes de múltiples fuentes: sistemas transaccionales, archivos planos, bases de datos relacionales, registros de auditoría, integraciones con proveedores, servicios externos y aplicaciones corporativas, entre otras. Este crecimiento no solo se ha manifestado en volumen, sino también en diversidad y frecuencia de actualización, lo cual ha reforzado la necesidad de transformar dichos datos en información analítica útil para el control y la toma de decisiones del negocio.

En particular, en los procesos de compras se originan datos críticos relacionados con órdenes, proveedores, productos, costos, condiciones de pago, tiempos de entrega y movimientos de inventario. Sin embargo, en muchos escenarios estos datos se distribuyen en diferentes sistemas y formatos, dificultando la consolidación histórica, el análisis por dimensiones y la obtención de indicadores de gestión de manera oportuna. Como consecuencia, es común que las áreas operativas y administrativas recurran a reportes manuales y hojas de cálculo, generando esfuerzos repetitivos, inconsistencias y limitada trazabilidad del origen de los datos.

Tradicionalmente, para responder a estas necesidades analíticas se han implementado almacenes de datos y plataformas de integración que centralizan información estructurada y semiestructurada. No obstante, estos enfoques suelen implicar costos relevantes de infraestructura y licenciamiento, además de requerir tareas continuas de administración, aprovisionamiento, respaldo, actualización de componentes y soporte operativo. Dichas actividades incrementan la carga de mantenimiento y pueden convertirse en una barrera para organizaciones o proyectos que buscan soluciones analíticas escalables sin depender de infraestructura compleja.

Con la adopción creciente de computación en la nube, se han consolidado alternativas orientadas a arquitecturas administradas y de pago por uso. En este contexto, el enfoque serverless permite implementar capacidades de almacenamiento, catalogación y consulta analítica sin la necesidad de operar servidores o clústeres permanentes, reduciendo significativamente el esfuerzo de administración y permitiendo escalar el consumo conforme a la demanda real. Para escenarios de analítica de compras, esta aproximación facilita la construcción de un repositorio central en el que los datos puedan mantenerse organizados, versionados y disponibles para consultas, indicadores y tableros de visualización, priorizando la sostenibilidad y el bajo costo de mantenimiento.

De esta manera, surge la oportunidad de diseñar e implementar un Data Warehouse serverless en AWS, utilizando servicios administrados como Amazon S3 para almacenamiento, AWS Glue Data Catalog para la organización y descripción de metadatos, y Amazon Athena para la ejecución de consultas analíticas sobre los datos, complementando con dashboards que permitan visualizar indicadores clave. Este enfoque responde a la necesidad de consolidar la información de compras de forma estructurada y gobernada, habilitando analítica y reportes con una arquitectura de soporte a largo plazo, adaptable y con costos controlables.

## **1.2 Descripción del problema**

En la actualidad, muchas organizaciones dependen de información proveniente de distintos sistemas operacionales para ejecutar y controlar sus procesos de compras. Dichos datos suelen originarse en módulos transaccionales (órdenes de compra, recepciones, facturación), catálogos de proveedores y productos, archivos externos y registros históricos. Aunque estos insumos contienen información valiosa para evaluar el desempeño del proceso de abastecimiento, con frecuencia se encuentran dispersos, con formatos heterogéneos y con diferentes niveles de calidad y consistencia. Esta situación dificulta la consolidación histórica, la trazabilidad de los registros y la generación de indicadores confiables de manera oportuna.

Como consecuencia, la analítica de compras tiende a sostenerse mediante esfuerzos manuales: extracción de datos a hojas de cálculo, elaboración de reportes estáticos y depuración repetitiva de inconsistencias. Además de consumir tiempo operativo, este enfoque incrementa el riesgo de errores, reduce la reproducibilidad de los análisis y limita la disponibilidad de información para la toma de decisiones, especialmente cuando se requieren comparaciones por periodos, por proveedor, por categoría de gasto o por unidades organizacionales.

Bajo este escenario, se identifica la necesidad de contar con un repositorio analítico centralizado que permita integrar la información de compras en un modelo orientado al análisis, con estructura y gobierno de datos. No obstante, en contextos académicos o en organizaciones con presupuestos limitados, implementar un Data Warehouse tradicional puede representar un reto debido a los costos de infraestructura, licenciamiento y, principalmente, por el esfuerzo de administración y mantenimiento que implica operar servidores, bases de datos y herramientas dedicadas de forma permanente. En este sentido, las arquitecturas serverless en la nube representan una alternativa para reducir el costo total de propiedad y simplificar la operación, al basarse en servicios administrados y en un esquema de pago por uso. Sin embargo, adoptar un enfoque serverless requiere una definición clara de componentes, flujo de datos y criterios de diseño: cómo almacenar y organizar los datos de compras, cómo catalogarlos para garantizar consistencia y descubrimiento, cómo habilitar consultas eficientes y cómo exponer los resultados a tableros de control con indicadores relevantes, manteniendo el principio de bajo costo y bajo mantenimiento.

Por lo tanto, el problema central consiste en que no existe una implementación práctica consolidada, de alcance acotado y orientada a bajo costo, que demuestre cómo construir un Data Warehouse serverless en AWS para el análisis de compras, integrando almacenamiento en Amazon S3, catalogación mediante AWS Glue Data Catalog y consultas con Amazon Athena, y que a su vez permita visualizar indicadores a través de dashboards en Power BI. La ausencia de una solución de este tipo limita la posibilidad de contar con analítica de compras sostenible y escalable sin incurrir en infraestructura compleja o costos fijos elevados.

En consecuencia, se plantea como necesidad desarrollar e implementar una arquitectura que permita consolidar datos de compras en una estructura orientada a análisis, habilitar un catálogo de metadatos que facilite el gobierno y el acceso controlado, ejecutar consultas analíticas optimizadas sobre los datos, y disponibilizar indicadores de gestión mediante tableros en Power BI. Todo ello, con un enfoque explícito de mantenimiento de bajo costo, priorizando servicios administrados, facilidad operativa y escalabilidad bajo demanda.

### **1.2.1 Preguntas de investigación**

¿Qué problema se identificó y cómo se pretende dar solución? Se identificó la dificultad para consolidar y analizar datos de compras de forma consistente, debido a dispersión de fuentes, reprocesos manuales y limitada trazabilidad. La solución consiste en desarrollar e implementar un Data Warehouse serverless en AWS con S3, Glue Data Catalog y Athena, y consumir los indicadores mediante dashboards en Power BI, priorizando bajo mantenimiento y costos controlados.

¿Quiénes serán beneficiados al terminar el proyecto? Se benefician principalmente las áreas usuarias de análisis de compras, al disponer de indicadores más rápidos y consistentes. También se beneficia el área técnica o de soporte de datos, por la reducción de tareas operativas y por contar con una arquitectura más simple de administrar.

¿Se utilizará alguna metodología de desarrollo? Sí, se utilizará Design Science Research (DSR) como marco para diseñar, construir y evaluar el artefacto (DWH serverless y dashboards). En la parte práctica, se seguirá un desarrollo incremental por etapas: almacenamiento, catalogación, consultas y visualización.

¿Cuántas personas se encuentran involucradas? Participa principalmente una persona responsable del desarrollo e implementación. Adicionalmente, se considera la participación del asesor académico para revisión y retroalimentación, y eventualmente un contacto que provea o valide el dataset de compras si aplica.

¿Cuánto tiempo se necesita para terminarlo? Se estima un rango de 8 a 12 semanas para completar implementación, pruebas y dashboards, considerando un alcance acotado y un dataset de tamaño manejable. El tiempo puede variar según disponibilidad de datos, ajustes de modelado y validación de indicadores.

¿Los recursos con los que actualmente se cuentan son suficientes? En términos generales, sí, siempre que se cuente con computadora personal, conexión a internet, cuenta de AWS, un dataset de compras y Power BI Desktop. Si se requiere publicación en Power BI Service o refresh programado, podría necesitarse un componente adicional, según el alcance definido.

¿Se capacitará al personal al finalizar el proyecto? Puede contemplarse una capacitación breve de transferencia de conocimiento, enfocada en el uso de dashboards y lectura de indicadores. En caso de no existir personal asignado, la capacitación puede formalizarse como documentación técnica y guía de uso para facilitar adopción futura.

¿Qué beneficios traerá a la empresa el implementar el proyecto? Mejora la disponibilidad de indicadores de compras, reduce reprocesos manuales y facilita análisis histórico por dimensiones. Además, aporta mayor trazabilidad de datos y un esquema de consulta más flexible sin necesidad de operar infraestructura compleja.

¿Cuál es la importancia de implementar este tipo de proyecto? Permite convertir datos de compras en información accionable con una base analítica estructurada y reutilizable. Además, introduce un enfoque moderno de analítica con servicios administrados, que favorece continuidad, escalabilidad y sostenibilidad operativa con costos controlados.

¿Se considera que el proyecto pueda ser operativo para la empresa a futuro? Sí, debido a que la arquitectura se basa en servicios administrados y escalables, lo cual facilita su continuidad. Su operatividad a futuro depende de mantener actualizados los datos de compras, controlar costos de consultas y documentar el flujo para que pueda ser administrado sin alta especialización.

## **1.3 Justificación**

El análisis de compras requiere información consolidada, consistente y trazable, debido a que los datos suelen originarse en múltiples fuentes, con variaciones de formato y calidad. Esta dispersión dificulta la construcción de indicadores confiables y oportunos, incrementa el trabajo manual para depurar datos y limita la capacidad de comparar el desempeño del gasto por periodos, proveedores, categorías y unidades organizacionales. En consecuencia, resulta necesario implementar un repositorio analítico que unifique la información de compras bajo una estructura orientada a consulta y generación de indicadores.

La implementación de un Data Warehouse (DWH) serverless en AWS se justifica como alternativa viable cuando se busca disminuir el esfuerzo operativo y el costo asociado a la administración de infraestructura. A diferencia de enfoques tradicionales que requieren servidores dedicados, licenciamiento y actividades recurrentes de mantenimiento, una arquitectura basada en servicios administrados permite enfocarse en el diseño del modelo de datos, el aseguramiento de calidad y el consumo analítico, reduciendo la complejidad operativa. Este enfoque es consistente con un objetivo de mantenimiento de bajo costo, al priorizar componentes que escalan bajo demanda y se gestionan principalmente mediante configuración y buenas prácticas de organización de datos.

Bajo esta perspectiva, el uso de Amazon S3 como capa de almacenamiento se fundamenta en su capacidad para funcionar como repositorio central de datos, favoreciendo la conservación histórica y la separación por zonas lógicas, lo cual facilita el control del ciclo de vida de la información. Asimismo, AWS Glue Data Catalog aporta valor al actuar como repositorio de metadatos técnicos, permitiendo describir bases, tablas y particiones, y habilitando un punto común de descubrimiento y estandarización de esquemas. Finalmente, Amazon Athena se justifica como motor de consulta porque permite realizar análisis mediante SQL directamente sobre los datos almacenados, evitando la necesidad de aprovisionar y administrar infraestructura de cómputo para consultas. En conjunto, estos componentes conforman una base adecuada para un DWH orientado a analítica de compras con énfasis en simplicidad operativa y control de costos.

La inclusión de dashboards de indicadores se justifica por la necesidad de traducir los datos consolidados en métricas accionables para la toma de decisiones. La integración de Power BI con Athena permite consumir datasets para la elaboración de paneles, bajo modalidades acordes al escenario, manteniendo la capa analítica alineada con el enfoque serverless al consultar sobre el repositorio en AWS.

## **1.4 Objetivos**

### **1.4.1 Objetivo general**

Construir y evaluar una arquitectura de Data Warehouse serverless en AWS orientada al análisis de compras, basada en S3, Glue Data Catalog y Athena, y presentar indicadores mediante Power BI, priorizando simplicidad operativa y bajo costo de mantenimiento.

### **1.4.2 Objetivos específicos**

Definir el modelo dimensional de compras (hechos y dimensiones) para soportar indicadores clave.

Organizar el almacenamiento de datos de compras en Amazon S3 con una estructura lógica que facilite su consulta.

Catalogar los datasets de compras en AWS Glue Data Catalog para habilitar descubrimiento y consulta consistente.

Implementar un conjunto de visualizaciones en Power BI (KPIs y tendencias) a partir de consultas en Athena para apoyar la toma de decisiones.

Validar el funcionamiento del DWH mediante la ejecución de consultas y la visualización correcta de indicadores en Power BI.

## **1.5 Alcance**

El alcance de la investigación comprende el diseño, la construcción y la evaluación funcional de una arquitectura de Data Warehouse serverless orientada al análisis de compras. De manera específica, se contempla la definición del modelo dimensional de compras, la organización lógica de los datasets en Amazon S3, la catalogación de tablas y particiones en AWS Glue Data Catalog, la ejecución de consultas analíticas en Amazon Athena, la construcción de dashboards en Power BI con los indicadores de compras definidos, y la validación del flujo de extremo a extremo, desde el almacenamiento hasta la visualización.

Dado que el acceso directo a la consola de AWS no resulta viable para el personal operativo de compras, se contempla dentro del alcance un módulo mínimo de ingesta validada, que permite registrar la información de compras sin requerir credenciales de AWS, aplicando reglas básicas de validación antes de escribir el registro en la zona raw del repositorio. Este módulo constituye el mecanismo de entrada de datos hacia la arquitectura ya descrita, y no sustituye ni amplía dicha arquitectura.

Quedan fuera del alcance la implementación de un sistema transaccional completo de compras (con flujo de aprobación, gestión de órdenes o integración con proveedores), la implementación empresarial a gran escala, la integración con múltiples sistemas operacionales en tiempo real, la automatización avanzada de ingesta continua, el monitoreo productivo corporativo y el desarrollo de pipelines de transformación complejos. Estas exclusiones son deliberadas y responden al principio de acotamiento propio de una investigación académica con enfoque en la demostración funcional del artefacto diseñado (Hevner et al., 2004).

## **1.6 Limitaciones**

Toda investigación aplicada presenta limitaciones que deben reconocerse y documentarse explícitamente, dado que estas condicionan el alcance de los resultados y la validez de las conclusiones. En el contexto del Design Science Research, identificar las restricciones del artefacto forma parte del proceso de evaluación honesta de su contribución (Peffers et al., 2007).

El alcance se enfoca en una implementación funcional y académica, no en una plataforma corporativa de gran escala; en consecuencia, los resultados obtenidos son representativos del enfoque propuesto, pero no necesariamente generalizables a contextos productivos sin adaptaciones adicionales. La disponibilidad y calidad del dataset de compras condiciona, asimismo, el nivel de detalle del análisis y de los indicadores: si el dataset presenta inconsistencias significativas, el esfuerzo de preparación de datos podría afectar el tiempo disponible para otras fases del proyecto.

La solución se construye con servicios específicos de AWS, por lo cual su implementación responde a las características, restricciones y políticas de dicho proveedor; cambios en los precios, la disponibilidad o las interfaces de los servicios utilizados podrían requerir ajustes en la arquitectura. La evaluación del artefacto, por su parte, se basa en pruebas funcionales y en la validación de indicadores, no en despliegues de producción a gran escala; en consecuencia, aspectos como la latencia bajo carga alta o la estabilidad a largo plazo quedan fuera del alcance de la evaluación formal realizada. Finalmente, el proyecto prioriza un bajo costo de mantenimiento, por lo cual evita componentes que impliquen administración continua de infraestructura, decisión que puede limitar ciertas capacidades de automatización avanzada o integración en tiempo real que requerirían servicios adicionales.

# **Capítulo II - Marco Teórico**

## **2.1 Fundamentos de Data Warehouse y modelado analítico**

### **2.1.1 Evolución de los Data Warehouses: de enfoques tradicionales a arquitecturas en la nube**

La evolución de los Data Warehouses (DWH) puede describirse como la transición desde enfoques tradicionales, sustentados en infraestructura local y procesos de integración rígidos, hacia arquitecturas basadas en servicios de cómputo en la nube, más elásticas y orientadas a componentes. Este cambio no solo implica reubicar el almacenamiento, sino también redefinir cómo se integran, procesan y disponibilizan los datos para análisis, enfatizando la automatización y la escalabilidad. En ese sentido, Mayor Cebrian (2025) destaca que “… estos procesos se ejecutaban de forma manual o programada en servidores locales. Sin embargo, con la adopción generalizada de la computación en la nube y las arquitecturas Big Data, el enfoque ETL ha evolucionado hacia soluciones automatizadas, escalables y modulares…” (pp. 20–21).

Comprender esta evolución es clave en proyectos analíticos porque explica por qué muchas organizaciones migran de soluciones tradicionales (con costos fijos, operación intensiva y escalabilidad limitada) hacia modelos en nube que favorecen el crecimiento por demanda y la reducción de carga operativa. En la práctica, esta transformación habilita plataformas más flexibles para integrar datos heterogéneos, conservar históricos y acelerar la generación de indicadores para toma de decisiones. 

### **2.1.2 ETL vs ELT: estrategias modernas para DWH en la nube**

En la integración de datos para analítica, ETL (Extract, Transform, Load) y ELT (Extract, Load, Transform) representan dos estrategias para mover datos desde fuentes operacionales hacia repositorios analíticos. En ETL, los datos se transforman antes de cargarse al destino analítico; en ELT, se cargan primero (generalmente en un repositorio escalable como un Data Lake o almacén analítico) y luego se transforman en el propio entorno de análisis o consumo. En arquitecturas modernas en la nube, esta distinción se vuelve más relevante porque los repositorios de almacenamiento y los motores de consulta/transformación suelen estar desacoplados, permitiendo flujos más flexibles y escalables. 

Diferenciar ETL y ELT es importante porque influye directamente en la calidad y consistencia de la información que llega a los modelos analíticos; la agilidad para incorporar nuevas fuentes o redefinir reglas de transformación: el costo y rendimiento, especialmente cuando el motor de consulta cobra por procesamiento o por datos escaneados; y la gobernanza, ya que define dónde se aplican controles, validaciones y estandarización. En palabras de Palan Murillo (2025), “el procesamiento de los datos en bruto constituye una fase importante dentro de la arquitectura de gobernanza del dato, ya que garantiza que la información almacenada en el Data Lake sea consistente, fiable y lista para su consumo posterior” (pp. 41–42).

### **2.1.3 Calidad de datos en entornos analíticos: consistencia, completitud, unicidad y trazabilidad**

La calidad de datos en entornos analíticos se refiere al grado en que los datos son aptos para su uso en análisis, reportes e indicadores. En un Data Warehouse o un Data Lake orientado al análisis, la calidad no es un “extra”, sino un requisito para garantizar que las conclusiones y métricas representen la realidad del negocio. En ese sentido, Alfredo (2025) enfatiza que “la calidad de los datos es un prerrequisito para la analítica avanzada. Modelos de predicción, segmentación de clientes o evaluación de riesgo crediticio dependen de datos limpios, completos y actualizados” (p. 18).

La calidad de datos es crítica porque condiciona la confiabilidad de todo lo que se construye encima: indicadores, tendencias, segmentaciones y comparaciones históricas. Si los datos llegan incompletos, duplicados o inconsistentes, el sistema analítico puede producir conclusiones equivocadas. Para esto es clave los distintos indicadores de calidad de datos, como lo es la consistencia, que se refiere a que los datos no se contradicen entre sí a través de tablas, fuentes o periodos; la completitud, indica el grado en que los datos contienen todos los campos necesarios para soportar indicadores; la unicidad, evalúa que los registros no estén duplicados cuando deben ser únicos; y la trazabilidad, que es la capacidad de rastrear el origen del dato y sus transformaciones.

## **2.2 Arquitecturas serverless aplicadas a analítica**

### **2.2.1 Computación serverless: principios, ventajas, limitaciones y modelos de costo**

La computación serverless (o “sin servidor”) se refiere a un paradigma de computación en la nube en el que el usuario no administra servidores de forma directa (aprovisionamiento, escalado, parches, capacidad fija), sino que consume capacidades de ejecución y servicios administrados bajo demanda. Para entender dónde encaja este enfoque, resulta útil considerar que los servicios de nube suelen organizarse como una pila (stack) de servicios construidos unos sobre otros, desde capas más cercanas a infraestructura hasta capas más cercanas a aplicaciones. En esa línea, Kamlofsky (2022) indica que “el modelo de Servicios de la computación en nube a menudo se describe como una pila, como respuesta a la amplia gama de servicios construidos uno encima del otro bajo el nombre 'Nube'” (p. 5).

Este concepto es especialmente relevante en proyectos analíticos porque entre sus ventajas permite reducir carga operativa (administración de servidores), habilitar escalabilidad automática y alinear el consumo de recursos a la demanda real. En escenarios de analítica, donde el uso puede ser intermitente, serverless evita pagar capacidad de cómputo “ociosa” y favorece arquitecturas más simples de operar. No obstante, hay factores limitantes que no se pueden ignorar, como lo es la dependencia con el proveedor del servicio, ya que las decisiones quedan atadas a dichas especificaciones o cambios; la observabilidad y depuración, esta puede ser más compleja al momento de rastrear fallos entre componentes utilizados; y los costos impredecibles si no existe un control correcto, las consultas mal diseñadas o consumo sin límites pueden elevar considerablemente los gastos. 

### **2.2.2 Gobierno de datos en arquitecturas serverless: catálogo, metadatos, linaje y acceso**

El gobierno de datos en arquitecturas serverless se entiende como el conjunto de prácticas, controles y mecanismos que permiten asegurar que los datos sean descubribles, confiables, seguros y trazables, desde su ingestión hasta su consumo analítico. En entornos cloud modernos, donde el almacenamiento, el catálogo y la consulta suelen estar desacoplados, el gobierno de datos se apoya fuertemente en metadatos, catálogos, control de acceso, auditoría y mejora continua. En ese contexto, el uso de marcos de referencia para evaluar decisiones técnicas es clave, así como nos guían Marceliano Alcantara & Villarreal Tello (2025), indicando un servicio útil para esto, es “el marco AWS Well-Architected actúa como una guía de referencia para mantener la calidad técnica y la gobernanza del sistema, permitiendo auditorías periódicas y una mejora continua de la arquitectura” (p. 29).

En una solución analítica serverless, el gobierno de datos es esencial porque reduce inconsistencias y ambigüedades, facilita el descubrimiento de datasets y su reutilización sin depender de conocimiento tribal, incrementa la confiabilidad de indicadores y dashboards, y refuerza seguridad y cumplimiento al asegurar que cada usuario/rol solo acceda a lo que le corresponde. Bajo este contexto, un catálogo centraliza la descripción de los datasets analíticos y sirve como punto de “descubrimiento” para usuarios técnicos y analíticos; los metadatos son los “datos sobre los datos”, es decir, esquemas, tipos, particiones, fechas de actualización, propietarios, definiciones y reglas de uso; el linaje permite corroborar de dónde vino un dato, qué transformaciones sufrió, y cuándo cambió; y cabe recalcar que el gobierno de datos exige un control claro de quién puede ver qué, con principios como mínimo privilegio, separación por roles y auditoría de actividades.

### **2.2.3 Diseño de zonas de datos (raw/bronze, curated/silver, analytics/gold)**

El diseño de zonas de datos (también conocido como arquitectura por capas o patrón multicapa) consiste en organizar el repositorio analítico en capas lógicas que representan distintos niveles de madurez del dato, desde su estado original hasta su forma lista para consumo analítico. Este enfoque se conoce ampliamente como arquitectura Medallion, donde las capas Bronze (bronce o raw), Silver (plata o curated) y Gold (oro o analytics) describen la calidad y preparación del dato en cada etapa del flujo. Su propósito central es refinar el dato de forma gradual mediante validaciones y transformaciones hasta obtener información confiable para inteligencia de negocios. 

En concordancia con esto, Berbel Carballal (2025) afirma que “su objetivo es mejorar de forma incremental y progresiva la estructura y calidad de los datos a medida que fluyen por cada capa de la arquitectura” (p. 32). Esta idea es consistente con la definición técnica del patrón Medallion, donde la mejora progresiva ocurre conforme los datos avanzan de Bronze (datos brutos), Silver (datos validados y depurados), y Gold (datos listos para consumo). El valor práctico de separar los datos por zonas/capas es que con esto evitamos que los repositorios tengan datos mezclados, sin calidad ni trazabilidad; se permite asignar garantías distintas de calidad según la capa; se facilita la auditoría y el reproceso, ya que es más sencillo de rastrear si un indicador termina mal; y mejora el rendimiento y el costo, esto gracias a que la capa de consumo debe estar optimizada para consultas y dashboards, esto reduciendo reprocesos. 

## **2.3 Componentes AWS**

### **2.3.1 S3 como Data Lake: organización por prefijos, particionamiento y ciclo de vida (lifecycle)**

Un Data Lake en Amazon S3 es un enfoque de almacenamiento analítico donde los datos se conservan en un repositorio central basado en almacenamiento de objetos, permitiendo alojar datos de diferentes fuentes y formatos y habilitar su consumo posterior mediante motores de consulta y procesamiento. En arquitecturas serverless, S3 suele funcionar como la capa base de almacenamiento por su desacoplamiento natural respecto al cómputo, facilitando que el análisis se ejecute bajo demanda con otros servicios. En esa línea, López Saldarriaga (2025) sostiene que “Amazon S3 suele ser pieza central de los data lake serverless. Estudios sobre lagos de datos corporativos muestran reducciones de costos > 60 % al migrar almacenamiento primario a S3, gracias a su separación de cómputo…” (p. 51).

Diseñar S3 como Data Lake tiene valor directo en analítica porque reduce dependencia de infraestructura fija; facilita almacenar histórico a bajo costo y escalar almacenamiento sin “planificación de capacidad”; permite controlar costos mediante políticas de ciclo de vida; y mejora eficiencia de consultas cuando la organización por prefijos y particiones está alineada a patrones de consulta (especialmente para motores como Athena).

### **2.3.2 Glue Data Catalog: esquemas, tablas, particiones y crawler**

El AWS Glue Data Catalog es un repositorio centralizado de metadatos que almacena información técnica sobre los conjuntos de datos de una organización, como ubicación, esquema, propiedades y estructura; y organiza dichos metadatos en bases de datos y tablas (similar a un catálogo relacional). AWS describe que los metadatos se almacenan en tablas de metadatos, donde cada tabla representa un almacén/dataset específico, y que el catálogo se integra con servicios analíticos como Amazon Athena. 

Bajo este contexto, David & Zapata (2025) añaden que es un “… componente de gobernanza que mantiene automáticamente el inventario actualizado de todos los conjuntos de datos almacenados en las diferentes capas de la arquitectura medallón, siendo poblado continuamente por los Glue Crawlers que descubren y catalogan nuevos datos…” (p. 46). El catálogo se organiza en bases de datos y tablas, cada tabla incluye información como esquema y ubicación, habilitando que servicios de análisis consulten de forma uniforme. Las particiones forman parte del diseño de tablas y permiten segmentar datasets para mejorar consultas y administración. Un crawler escanea orígenes y extrae metadatos automáticamente (formato, esquema, particiones, etc.), manteniendo el catálogo actualizado y reduciendo la intervención manual.

### **2.3.3 Athena: ejecución SQL sobre S3, optimización por particiones y formatos columnares**

Amazon Athena es un servicio de consultas interactivo y serverless que permite analizar datos almacenados en Amazon S3 utilizando SQL estándar, sin necesidad de aprovisionar o administrar servidores; además, su modelo de cobro se basa en el consumo de consultas. En concordancia con esto, Landa Felices & Lujan Canicela (2024) señalan que "Amazon Athena permite realizar análisis potentes directamente en el almacenamiento de Amazon S3, eliminando la necesidad de una infraestructura de consultas independiente. Facilita la toma de decisiones proporcionando resultados en tiempo real y es compatible con SQL estándar…" (p. 36).

Athena es especialmente útil en analítica moderna porque reduce carga operativa, al ser serverless, elimina tareas típicas de operar un motor de consultas, permitiendo enfocarse en el modelado y el análisis; acelera exploración y consumo, ya que habilita consultas interactivas sobre datos ya almacenados en S3, ideal para escenarios donde los análisis se hacen “a demanda”; y por el control de costo por diseño, como el costo y el rendimiento están muy ligados a cómo se organizan los datos y qué formato se utiliza, Athena obliga a aplicar buenas prácticas de ingeniería (particiones, Parquet/ORC, compresión) para mantener la eficiencia.

### **2.3.4 Seguridad en analítica cloud: IAM, control de acceso, cifrado at-rest/in-transit**

La seguridad en entornos de analítica en la nube constituye un componente esencial para garantizar la confidencialidad, integridad y disponibilidad de los datos. En arquitecturas orientadas al almacenamiento y consulta analítica, como las implementadas sobre AWS, la protección de la información no depende únicamente del resguardo del repositorio de datos, sino también del control riguroso sobre quién puede acceder a los recursos, qué acciones puede ejecutar y bajo qué condiciones se permite dicho acceso. En este contexto, la gestión de identidades y permisos adquiere un papel central, especialmente cuando diferentes servicios interactúan entre sí dentro de una misma solución analítica.

Uno de los mecanismos fundamentales para este propósito es AWS Identity and Access Management (IAM), servicio que permite definir políticas y roles para controlar el acceso a los recursos de la nube. En este sentido, Merchán y Azúa (2018) explican que "un rol de IAM en AWS, permite que un usuario, un grupo o una aplicación ejecutada en EC2 o en un dispositivo móvil asuma los permisos definidos por el rol, es decir que las credenciales transitorias se crean y se aplican a la entidad que asume el rol" (p. 10). Esta característica resulta especialmente relevante en arquitecturas serverless, ya que favorece un modelo de acceso más seguro y flexible, evitando el uso de credenciales permanentes y facilitando la asignación de permisos bajo el principio de mínimo privilegio.

## **2.4 Operación de compras: analítica, indicadores y gestión**

### **2.4.1 Indicadores clave de compras (KPIs): costo, ahorro, cumplimiento, lead time, proveedores**

Los indicadores clave de desempeño (Key Performance Indicators, KPIs) en el proceso de compras constituyen herramientas fundamentales para evaluar la eficiencia, eficacia y comportamiento general de la función de abastecimiento dentro de una organización. Su utilidad radica en que permiten traducir grandes volúmenes de datos operativos en métricas concretas que facilitan el monitoreo del desempeño, la identificación de desviaciones y la toma de decisiones basada en evidencia. En el contexto de la analítica de compras, los KPIs cumplen un papel central, ya que permiten analizar el gasto, medir oportunidades de optimización y evaluar el comportamiento de proveedores y procesos asociados.

Uno de los indicadores más relevantes es el costo de compras, entendido como el valor monetario total asociado a la adquisición de bienes o servicios en un periodo determinado. Este KPI permite identificar patrones de gasto, concentración presupuestaria y evolución histórica de las adquisiciones. Su análisis puede realizarse de forma agregada o segmentada por proveedor, categoría, unidad organizacional o periodo, lo que aporta una visión más detallada sobre cómo se distribuyen los recursos destinados al abastecimiento. Desde una perspectiva analítica, este indicador constituye una base para la elaboración de comparativos temporales, participación por categorías y evaluación del comportamiento del gasto frente a presupuestos o metas establecidas.

### **2.4.2 Evaluación de desempeño de proveedores: calidad, puntualidad, variabilidad de precio**

La evaluación del desempeño de proveedores constituye una práctica esencial dentro de la gestión de compras, debido a que permite medir el grado en que los actores externos cumplen con las condiciones esperadas por la organización en términos de calidad, oportunidad y estabilidad comercial. Más allá de la simple relación transaccional, los proveedores representan un componente estratégico dentro de la cadena de abastecimiento, ya que su desempeño impacta directamente en la continuidad operativa, en los costos del proceso y en la capacidad de respuesta de la organización frente a sus propias necesidades internas. Por esta razón, el análisis sistemático del comportamiento de los proveedores se convierte en un elemento fundamental para la toma de decisiones en compras.

Uno de los criterios más relevantes en esta evaluación es la calidad de los bienes o servicios suministrados. Este aspecto puede interpretarse como el nivel de conformidad entre lo recibido y lo requerido por la organización, considerando especificaciones técnicas, condiciones pactadas y ausencia de defectos o incumplimientos funcionales. En términos analíticos, la calidad del proveedor puede medirse mediante indicadores relacionados con rechazos, devoluciones, incidencias recurrentes, cumplimiento de especificaciones o nivel de aceptación de entregas. La importancia de este criterio radica en que una baja calidad no solo afecta el resultado inmediato de la compra, sino que también puede generar costos adicionales por reposiciones, interrupciones operativas, reprocesos o insatisfacción en áreas usuarias.

### **2.4.3 Gobernanza del dato de compras: maestros (proveedor, producto), reglas y consistencia**

La gobernanza del dato en el proceso de compras se refiere al conjunto de lineamientos, reglas y mecanismos orientados a asegurar que la información utilizada en el análisis sea confiable, consistente y reutilizable a lo largo del tiempo. En un entorno analítico, la gobernanza no solo implica resguardar los datos, sino también definir cómo deben estructurarse, validarse, actualizarse y consumirse dentro de la organización. Esta dimensión adquiere especial relevancia en compras, debido a que la información suele provenir de múltiples fuentes y procesos operativos, lo que incrementa el riesgo de inconsistencias, duplicidades y ambigüedades si no existe una gestión adecuada de los datos fundamentales.

Dentro de este contexto, los datos maestros representan un componente esencial para sostener la calidad del análisis. En particular, entidades como proveedor y producto cumplen una función central, ya que actúan como referencias comunes sobre las cuales se articulan las transacciones de compras. El maestro de proveedores permite identificar de forma única a cada entidad con la que la organización mantiene relación comercial, integrando atributos como nombre, código, categoría, condiciones de pago, localización o estado de vigencia. De forma similar, el maestro de productos organiza la información asociada a los bienes o servicios adquiridos, incluyendo descripciones, clasificaciones, unidades de medida y vínculos con categorías o familias de gasto. La correcta administración de estos maestros resulta fundamental porque evita que un mismo proveedor o producto sea representado de maneras distintas en el sistema, situación que dificultaría la consolidación analítica y afectaría la precisión de los indicadores.

## **2.5 BI y Dashboards: Power BI y analítica**

### **2.5.1 Dashboards para toma de decisiones: principios de visualización de KPIs y storytelling**

Los dashboards constituyen una herramienta central dentro de los sistemas de Business Intelligence, ya que permiten representar información clave del negocio de forma visual, resumida e interpretable. Su propósito no se limita a mostrar datos, sino a facilitar la comprensión de comportamientos, tendencias y desviaciones relevantes para la toma de decisiones. En este sentido, un dashboard efectivo transforma resultados analíticos en información accionable, reduciendo la complejidad del análisis y permitiendo que los usuarios identifiquen rápidamente situaciones que requieren atención, seguimiento o intervención.

En el contexto organizacional, los dashboards resultan especialmente valiosos cuando se utilizan para visualizar indicadores clave de desempeño (KPIs), debido a que estos sintetizan el comportamiento de procesos, áreas o resultados estratégicos en métricas concretas. La visualización adecuada de KPIs permite evaluar el estado actual de una operación, comparar resultados entre periodos, detectar variaciones significativas y monitorear el cumplimiento de objetivos previamente definidos. Por ello, la utilidad de un dashboard depende en gran medida de la calidad de los datos subyacentes, pero también de la forma en que dichos datos se presentan visualmente al usuario.

### **2.5.2 Modelado semántico en Power BI: medidas DAX, star schema y performance**

El modelado semántico en Power BI constituye una etapa fundamental dentro de la construcción de soluciones de inteligencia de negocios, ya que permite transformar los datos provenientes del repositorio analítico en una estructura comprensible, reutilizable y eficiente para el análisis. Mientras que el Data Warehouse organiza y consolida la información desde una perspectiva física y lógica orientada al almacenamiento y consulta, el modelo semántico define la forma en que los usuarios interactúan con dichos datos en la herramienta de visualización. En este sentido, el modelado semántico no solo establece relaciones entre tablas, sino que también organiza métricas, jerarquías, atributos y reglas de cálculo que permiten interpretar correctamente los indicadores expuestos en los dashboards.

Uno de los componentes más relevantes dentro de este modelo son las medidas DAX (Data Analysis Expressions), las cuales permiten construir cálculos dinámicos sobre los datos cargados en Power BI. A diferencia de las columnas calculadas, que generan valores fila por fila y quedan almacenadas dentro del modelo, las medidas se evalúan en tiempo de consulta según el contexto de filtros aplicado por el usuario. Esta característica las convierte en un recurso especialmente útil para el análisis de KPIs, ya que posibilitan calcular agregaciones, variaciones, acumulados, porcentajes, comparativos temporales y otras métricas que responden de forma flexible a la interacción con los reportes. En términos prácticos, las medidas DAX permiten que un mismo indicador pueda visualizarse por proveedor, período, categoría o unidad organizacional sin necesidad de replicar lógica de cálculo en múltiples tablas o visualizaciones.

### **2.5.3 Gobierno del reporte: refresh, dataset, control de acceso y versionado**

El gobierno del reporte constituye una dimensión fundamental dentro de las soluciones de Business Intelligence, ya que permite asegurar que la información visualizada en dashboards y reportes mantenga condiciones adecuadas de disponibilidad, consistencia, seguridad y trazabilidad. En términos generales, no basta con construir visualizaciones atractivas o modelos analíticos técnicamente correctos; también es necesario establecer mecanismos que regulen la actualización de los datos, la administración de los datasets, el acceso de los usuarios y el control de versiones de los artefactos analíticos. Estos elementos son especialmente relevantes cuando los reportes se convierten en instrumentos recurrentes para la toma de decisiones, ya que cualquier inconsistencia o descontrol en su administración puede afectar directamente la confiabilidad del análisis.

Uno de los componentes centrales dentro del gobierno del reporte es el refresh o actualización de datos. Este proceso se refiere a la forma en que la información consumida por el dashboard se sincroniza con las fuentes analíticas subyacentes, asegurando que los resultados visualizados reflejen el estado más reciente disponible según la periodicidad definida. La gestión del refresh resulta importante porque influye tanto en la oportunidad de la información como en la eficiencia operativa de la solución. Una actualización excesivamente frecuente puede generar consumo innecesario de recursos y afectar el desempeño, mientras que una actualización insuficiente puede hacer que los indicadores pierdan vigencia para el usuario final. Por ello, el gobierno del reporte debe definir criterios claros sobre periodicidad, horario, dependencia de la fuente y validación posterior a cada actualización, considerando el uso real de los tableros y el propósito analítico de la solución.

# **Capítulo III - Marco Metodológico**

## **3.1 Ruta de investigación**

La investigación siguió una ruta secuencial derivada del modelo de proceso propuesto para Design Science Research por Peffers et al. (2007). El trabajo inició con la identificación del problema de dispersión y baja trazabilidad en los datos de compras de Máquinas Agroindustriales MAGHSA, S.A., seguido de la definición de los objetivos de la solución planteados en el Capítulo I. A partir de estos objetivos se diseñó la arquitectura del artefacto, se construyó el modelo dimensional y el flujo de datos correspondiente, y finalmente se evaluó su funcionamiento mediante la ejecución del flujo completo contra una cuenta real de AWS y la interpretación de los indicadores obtenidos. Esta secuencia, de carácter iterativo, permitió validar avances parciales antes de continuar con la siguiente fase, en lugar de seguir un esquema lineal rígido.

## **3.2 Tipo de investigación**

Conforme al paradigma Design Science Research adoptado, el tipo de investigación no se ajusta plenamente a la clasificación tradicional de enfoque cuantitativo o cualitativo aplicada a estudios con sujetos humanos, dado que el objeto de evaluación es un artefacto tecnológico y no una población de personas. No obstante, para efectos de clasificación metodológica, el estudio combina un componente cualitativo, orientado al diseño y evaluación del artefacto mediante criterios de observación técnica y documental, con un componente cuantitativo, expresado en la medición de los indicadores definidos en la Tabla 4 y en los resultados de la validación funcional (apartado 3.9.8). El diseño es no experimental y transeccional, dado que los datos se recolectan y evalúan en un único periodo (junio a agosto de 2026), sin manipulación de variables ni comparación entre grupos de control.

## **3.3 Análisis de factibilidad**

### **3.3.1 Factibilidad económica**

La propuesta prioriza el bajo costo de mantenimiento como un principio de diseño explícito. Al emplear servicios serverless, el costo se alinea al uso real del almacenamiento y de las consultas, evitando el pago de capacidad ociosa característico de soluciones tradicionales. López Saldarriaga (2025) documenta reducciones de costos superiores al 60% al migrar almacenamiento analítico a Amazon S3 en comparación con infraestructura local, lo cual respalda la viabilidad económica de este enfoque. Para un contexto académico, la solución puede ejecutarse con volúmenes controlados y herramientas de acceso gratuito o de bajo costo, manteniendo el gasto total dentro de márgenes manejables.

##### **Tabla 1**

###### *Resumen general de costos*

| Tipo de costo | Descripción | Valor estimado |
| ----- | ----- | ----- |
| Personal | Desarrollo del proyecto por el estudiante | Sin costo adicional |
| Software | Uso de herramientas académicas y servicios en nube bajo consumo controlado | Bajo / controlado |
| Hardware | Computadora personal e internet | Ya disponible |
| Total | Implementación académica del proyecto | Bajo costo |

*Nota. Elaboración propia (2026).*

### **3.3.2 Factibilidad operativa**

La solución es operativamente viable porque se basa en servicios administrados, lo cual reduce la necesidad de mantenimiento continuo y elimina tareas operativas de alto esfuerzo como la administración de parches, respaldos manuales o escalamiento de servidores. Además, los dashboards en Power BI facilitan la interpretación de la información por parte de usuarios no técnicos, ampliando el alcance de la solución más allá del equipo de datos. La operación cotidiana se reduce a mantener actualizados los datasets en S3, asegurar que las tablas de Glue Data Catalog estén correctamente registradas, y ejecutar el refresh del dataset en Power BI según la periodicidad definida.

### **3.3.3 Factibilidad tecnológica**

La implementación es tecnológicamente factible porque utiliza servicios administrados y herramientas disponibles para el desarrollo académico: AWS (con capa gratuita disponible para nuevas cuentas), Power BI Desktop (disponible sin costo), equipo de cómputo personal e internet. Asimismo, no se requiere aprovisionamiento de servidores propios ni configuración de redes complejas, lo cual reduce significativamente la barrera técnica de implementación. La madurez y documentación disponible para cada uno de los servicios seleccionados respalda la viabilidad tecnológica de la solución (Landa Felices & Lujan Canicela, 2024).

##### **Tabla 2**

###### *Factibilidad técnica de software*

| Descripción | Motivo |
| ----- | ----- |
| Amazon S3 | Almacenamiento de datasets analíticos |
| AWS Glue Data Catalog | Gestión de metadatos y tablas |
| Amazon Athena | Consultas SQL serverless |
| Power BI Desktop | Diseño de dashboards e indicadores |
| Editor / IDE | Apoyo para scripts, consultas y documentación |
| Formatos CSV / Parquet | Intercambio y almacenamiento de datos |

*Nota. Elaboración propia (2026).*

### **3.3.4 Factibilidad cognoscitiva**

El desarrollo de la solución requiere conocimientos en modelado dimensional, arquitectura de servicios en la nube, lenguaje SQL y herramientas de visualización de datos. El estudiante cuenta con experiencia profesional previa en ingeniería de datos sobre AWS, lo cual respalda la factibilidad cognoscitiva del proyecto. Los aspectos que exceden ese conocimiento previo, particularmente el diseño específico del modelo dimensional de compras y la configuración de AWS Glue Data Catalog y Amazon Athena para este caso de estudio, se desarrollaron mediante consulta de documentación oficial de AWS y de la literatura especializada citada en el Capítulo II.

### **3.3.5 Factibilidad legal y ambiental**

En el plano legal, la implementación debe cumplir con los licenciamientos de software aplicables y con el uso adecuado de los datos empleados para fines académicos. Si el dataset contiene información sensible de personas naturales o jurídicas, se recomienda aplicar técnicas de anonimización o pseudonimización sobre los campos identificables antes de su carga en el repositorio. Asimismo, deben respetarse la licencia y las condiciones de uso de AWS y Power BI, especialmente en lo relativo al almacenamiento de datos de terceros en servicios de nube y a la publicación de reportes en entornos compartidos. En el contexto del control de acceso, la configuración de roles de IAM debe seguir el principio de mínimo privilegio (Merchán y Azúa, 2018), garantizando que solo las entidades autorizadas puedan acceder a los recursos analíticos de la solución.

En el plano ambiental, la arquitectura diseñada favorece una operación predominantemente digital, reduciendo la dependencia de reportes impresos y promoviendo la consulta electrónica de indicadores a través de dashboards accesibles desde cualquier dispositivo, lo cual contribuye indirectamente a disminuir el uso de papel y los recursos asociados a la impresión y distribución física de informes. Adicionalmente, al utilizarse infraestructura compartida en la nube bajo un modelo de consumo bajo demanda, se evita el aprovisionamiento de hardware dedicado, lo cual también reduce la huella energética asociada a la operación de servidores propios. Desde esta perspectiva, la adopción de servicios serverless no solo tiene implicaciones económicas y operativas, sino que también se alinea con principios de eficiencia en el consumo de recursos computacionales (Kamlofsky, 2022).

## **3.4 Hipótesis**

¿Desarrollar e implementar un Data Warehouse serverless en AWS para el análisis de compras mediante S3, Glue Data Catalog y Athena, con dashboards en Power BI, ayudará a reducir el esfuerzo de mantenimiento y operación, manteniendo un costo de soporte bajo?

### **3.4.1 Variable independiente**

X: implementación del Data Warehouse serverless en AWS para el análisis de compras.

### **3.4.2 Variable dependiente**

Y: esfuerzo de mantenimiento y costo de soporte de la solución.

La variable X se valida mediante la construcción funcional del artefacto y la ejecución de las consultas de validación (apartado 3.9.8), mientras que la variable Y se evalúa de forma documental y cualitativa a través del análisis de factibilidad operativa y económica (apartados 3.3.1 y 3.3.2), dado que una medición cuantitativa formal del esfuerzo de mantenimiento requeriría un periodo de operación sostenido que excede el alcance temporal de este trabajo. Esta situación se reconoce como una limitación metodológica del presente estudio.

## **3.5 Definición de la población y tamaño de la muestra**

### **3.5.1 Tamaño de la población**

En el marco de una investigación desarrollada bajo Design Science Research, la noción clásica de población y muestra, propia de estudios cuantitativos o cualitativos con sujetos humanos, se adapta al objeto de análisis del artefacto construido. En este caso, la población de referencia corresponde al conjunto de registros transaccionales generados por el proceso de compras de Máquinas Agroindustriales MAGHSA, S.A., específicamente las órdenes de compra, el maestro de proveedores, el maestro de productos y el catálogo de categorías. La calidad y completitud de estas fuentes tiene un impacto directo en la confiabilidad de los indicadores que se generan posteriormente; como señala Muñoz Ramírez (2025), la detección temprana de inconsistencias en las fuentes de datos es fundamental para garantizar resultados analíticos válidos.

##### **Tabla 3**

###### *Fuentes documentales del proyecto*

| Tipo de referencia | Referencia | Descripción |
| ----- | ----- | ----- |
| Hoja de cálculo / CSV | Registro de compras | Contiene información de órdenes o transacciones de compra, montos, fechas y proveedores |
| Hoja de cálculo / CSV | Maestro de proveedores | Incluye identificadores y atributos descriptivos de los proveedores |
| Hoja de cálculo / CSV | Maestro de productos | Incluye códigos, nombres, categorías y atributos asociados a los productos o servicios adquiridos |
| Hoja de cálculo / CSV | Catálogo de categorías | Permite clasificar el gasto por tipo de producto, familia o segmento de compra |
| Hoja de cálculo / CSV | Catálogo de categorías de proveedor | Clasifica a los proveedores por tipo de suministro (repuestos, materia prima, servicios, insumos, combustibles) |
| Hoja de cálculo / CSV | Catálogo de unidades organizacionales | Cataloga las unidades organizacionales que originan las compras |
| Hoja de cálculo / CSV | Relación proveedor–categoría de proveedor | Vincula cada proveedor con la(s) categoría(s) de proveedor a la(s) que pertenece |
| Hoja de cálculo / CSV | Regla de compatibilidad categoría de proveedor–categoría de producto | Define qué categorías de producto son válidas para cada categoría de proveedor |
| Hoja de cálculo / CSV | Relación proveedor–categoría de producto | Vincula cada proveedor con las categorías de producto que suministra |
| Hoja de cálculo / CSV | Relación proveedor–producto | Vincula cada proveedor con los productos específicos que suministra |
| Hoja de cálculo / CSV | Directorio de contacto de proveedores | Contiene nombre, teléfono(s) y correo(s) de contacto por proveedor |
| Documento técnico | Definición de KPIs | Documento de apoyo para especificar los indicadores analíticos que serán visualizados en Power BI |

*Nota. Elaboración propia (2026).*

### **3.5.2 Cálculo del tamaño de la muestra**

Debido a que el alcance del proyecto es académico y no contempla el acceso a la totalidad de los registros históricos de la organización, se define una muestra de trabajo conformada por un conjunto de datos sintéticos que reproduce la estructura, los campos y las relaciones del proceso real de compras. Esta muestra contempla seis proveedores, seis productos, seis categorías y diez órdenes de compra, distribuidas en un periodo de referencia comprendido entre junio y agosto de 2026. El diseño del modelo dimensional y de la organización en S3 permite sustituir esta muestra por el volumen real de datos de la organización sin requerir cambios estructurales en la arquitectura.

### **3.5.3 Instrumento**

La recolección y validación de la información se apoya en instrumentos propios de la arquitectura serverless implementada, en lugar de instrumentos tradicionales de encuesta o entrevista, dado que el objeto de estudio es un artefacto tecnológico. En primer lugar, se emplean archivos fuente en formato CSV correspondientes al registro de compras y a los maestros de proveedores, productos y categorías, utilizados como insumo de carga hacia la zona raw del repositorio en Amazon S3. En segundo lugar, se utilizan sentencias SQL de definición de datos, empleadas para crear las tablas externas de la tabla de hechos y de las dimensiones en AWS Glue Data Catalog. En tercer lugar, se ejecutan consultas SQL de validación en Amazon Athena, orientadas a verificar la correcta relación entre la tabla de hechos y las dimensiones, y a calcular los indicadores definidos en la Tabla 4. Como cuarto instrumento, se toman capturas de pantalla de la consola de AWS (S3, Glue Data Catalog y Athena), utilizadas como evidencia documental del funcionamiento del flujo de extremo a extremo. Finalmente, se aplica un guión de verificación funcional, a manera de lista de cotejo, para confirmar que cada capa de la arquitectura se ejecuta correctamente antes de considerarse validada.

Adicionalmente, se incorpora un módulo propio de ingesta validada como instrumento de recolección, el cual permite registrar nuevas compras sin exponer el acceso directo a la consola de AWS, aplicando reglas de validación antes de escribir el dato en la zona raw del repositorio.

### **3.5.4 Recolección de datos**

La recolección de datos se ejecutó en un único momento, siguiendo la secuencia definida en el diagrama de proceso (apartado 3.9.6): los archivos fuente descritos en la Tabla 3 se cargaron en la zona raw del repositorio en Amazon S3, se transformaron y calcularon los campos derivados requeridos por el modelo dimensional, se convirtieron a formato Parquet en las zonas curated y analytics, y finalmente se registraron en AWS Glue Data Catalog para su consulta mediante Amazon Athena. Este procedimiento se documenta con mayor detalle en el apartado 3.9.8, correspondiente a la validación funcional del flujo.

La carga de nuevos registros de compras se realiza a través del módulo de ingesta validada descrito en el apartado 3.5.3, en sustitución de la carga manual utilizada durante la validación inicial del flujo.

## **3.6 Interpretación de resultados**

Con el propósito de evaluar el valor analítico del artefacto más allá de su funcionamiento técnico, se interpretan a continuación los cuatro indicadores definidos en la Tabla 4.

##### **Tabla 4**

###### *Variables e indicadores del análisis de compras*

| Variable/Indicador | Definición operativa | Fuente (modelo dimensional) |
| ----- | ----- | ----- |
| Costo total de compras por periodo | Suma del monto total de las órdenes de compra, agrupada por año y mes | hechos_compras.monto_total, dim_tiempo |
| Gasto por categoría | Suma del monto total agrupada por categoría y familia de gasto, expresada también como porcentaje del total | hechos_compras.monto_total, dim_categoria |
| Gasto por proveedor | Suma del monto total y cantidad de órdenes agrupadas por proveedor | hechos_compras.monto_total, dim_proveedor |
| Lead time promedio por proveedor | Promedio de días entre la emisión de la orden y la recepción del bien o servicio, agrupado por proveedor | hechos_compras.lead_time_dias, dim_proveedor |

*Nota. Elaboración propia (2026).*

### **3.6.1 Gráficos y tabulares**

##### **Tabla 5**

###### *Costo total de compras por periodo*

| Año | Mes | Costo total (GTQ) |
| ----- | ----- | ----- |
| 2026 | Junio | 21,285.00 |
| 2026 | Julio | 77,350.00 |
| 2026 | Agosto | 48,610.00 |

*Nota. Elaboración propia (2026).*

##### **Tabla 6**

###### *Gasto por categoría*

| Categoría | Familia de gasto | Gasto total (GTQ) | % del total |
| ----- | ----- | ----- | ----- |
| Materia prima metálica | Producción | 56,200.00 | 38.17% |
| Neumáticos agrícolas | Mantenimiento | 33,600.00 | 22.82% |
| Combustibles | Operación | 31,835.00 | 21.62% |
| Servicios de maquinado | Producción | 12,750.00 | 8.66% |
| Aceites y lubricantes | Mantenimiento | 10,800.00 | 7.33% |
| Repuestos de motor | Mantenimiento | 2,060.00 | 1.40% |

*Nota. Elaboración propia (2026).*

##### **Tabla 7**

###### *Gasto por proveedor*

| Proveedor | Categoría | Órdenes | Gasto total (GTQ) |
| ----- | ----- | ----- | ----- |
| Aceros y Maquinaria S.A. | Materia Prima | 2 | 56,200.00 |
| Repuestos Agroindustriales del Norte | Repuestos | 3 | 35,660.00 |
| Importadora Diesel Centroamericana | Repuestos | 2 | 31,835.00 |
| Servicios Metalmecánicos del Sur | Servicios | 1 | 12,750.00 |
| Lubricantes Industriales GT | Insumos | 2 | 10,800.00 |

*Nota. Elaboración propia (2026).*

##### **Tabla 8**

###### *Lead time promedio por proveedor*

| Proveedor | Órdenes evaluadas | Lead time promedio (días) |
| ----- | ----- | ----- |
| Importadora Diesel Centroamericana | 2 | 1.0 |
| Lubricantes Industriales GT | 2 | 3.5 |
| Servicios Metalmecánicos del Sur | 1 | 7.0 |
| Repuestos Agroindustriales del Norte | 3 | 8.7 |
| Aceros y Maquinaria S.A. | 2 | 9.5 |

*Nota. Elaboración propia (2026).*

En cuanto al costo por periodo (Tabla 5), se observa una variación considerable entre los tres meses evaluados: el gasto de julio (GTQ 77,350.00) casi cuadruplica al de junio (GTQ 21,285.00), para luego disminuir en agosto (GTQ 48,610.00). Esta variabilidad mensual es consistente con un patrón de compras concentradas en periodos puntuales, más que con un gasto distribuido de forma uniforme, lo cual respalda la utilidad de contar con un indicador histórico para anticipar picos de gasto.

Respecto al gasto por categoría (Tabla 6), se identifica una concentración marcada: las tres categorías principales (materia prima metálica, neumáticos agrícolas y combustibles) representan en conjunto el 82.61% del gasto total, mientras que las tres restantes no superan, de forma individual, el 9% cada una. Este resultado evidencia una dependencia significativa de un número reducido de categorías de gasto, información relevante para priorizar esfuerzos de negociación o de búsqueda de proveedores alternativos.

El análisis por proveedor (Tabla 7) refuerza este hallazgo: Aceros y Maquinaria S.A. concentra el 38.17% del gasto total con apenas dos órdenes de compra, lo cual representa una dependencia notable de un solo proveedor para la categoría de mayor peso económico. Al contrastar este resultado con el indicador de lead time (Tabla 8), se observa que dicho proveedor presenta, además, el tiempo de entrega promedio más alto de los cinco evaluados (9.5 días), mientras que el proveedor con mejor desempeño de entrega (Importadora Diesel Centroamericana, 1.0 día) participa con un gasto considerablemente menor. Esta combinación, alta concentración de gasto junto con bajo desempeño de entrega, constituye un riesgo operativo que, sin un repositorio analítico centralizado, sería difícil de identificar de forma oportuna mediante los reportes manuales descritos en el planteamiento del problema (apartado 1.1.2).

En conjunto, estos resultados muestran que el Data Warehouse serverless no solo valida el funcionamiento técnico de la arquitectura propuesta, sino que también genera información interpretable y accionable para la gestión de compras de MAGHSA, S.A., cumpliendo con el objetivo general planteado en el apartado 1.3.1.

## **3.7 Recursos utilizados**

Para el desarrollo de la investigación se requieren los recursos mínimos detallados en la Tabla 9. La selección de estos responde al criterio de bajo costo y disponibilidad académica; todos los componentes de software son accesibles de forma gratuita o con costo controlado, y los recursos de hardware se encuentran disponibles como equipo personal del desarrollador.

##### **Tabla 9**

###### *Recursos necesarios*

| Recurso | Descripción |
| ----- | ----- |
| Computadora personal | Equipo para modelado, consultas y dashboards |
| Conexión a internet | Acceso a AWS y herramientas en línea |
| Cuenta de AWS | Uso de S3, Glue Data Catalog y Athena |
| Power BI Desktop | Construcción de dashboards |
| Dataset de compras | Fuente principal para alimentar la solución |
| Documentación técnica | Apoyo para modelado, configuración y validación |

*Nota. Elaboración propia (2026).*

## **3.8 Cronograma**

El cronograma se organiza en fases semanales que reflejan la secuencia lógica de las actividades definidas en el diseño general. La estructura temporal responde al enfoque incremental adoptado, en el cual cada etapa genera insumos para la siguiente y permite validar avances parciales antes de continuar. Las semanas indicadas son referenciales y pueden ajustarse según la disponibilidad del dataset, el resultado de las pruebas intermedias y los ajustes derivados del proceso iterativo del DSR (Peffers et al., 2007).

##### **Tabla 10**

###### *Cronograma referencial*

| Actividad | Semanas |
| ----- | ----- |
| Revisión bibliográfica y definición metodológica | 1 – 2 |
| Diseño de arquitectura y modelo dimensional  | 3 – 4 |
| Preparación y organización de datos en S3 | 5 |
| Catalogación en Glue Data Catalog | 6 |
| Desarrollo de consultas en Athena | 7 – 8 |
| Construcción de dashboards en Power BI  | 9 – 10 |
| Validación funcional y pruebas | 11 |
| Ajustes finales y documentación  | 12 |

*Nota. Elaboración propia (2026).*

# **Capítulo IV - Análisis de la Aplicación**

## **4.1 Descripción del proyecto**

El proyecto consiste en el desarrollo e implementación de un Data Warehouse serverless en Amazon Web Services para el análisis de compras de MAGHSA, S.A. Responde a la ausencia de un repositorio centralizado y consultable de información de compras, actualmente dispersa en archivos independientes sin una estructura analítica común (véase 1.2).

La solución se organiza en tres capas sobre Amazon S3: raw, curated y analytics. Un Glue Data Catalog registra el esquema de las tablas sin recurrir a un motor de base de datos administrado. Amazon Athena ejecuta las consultas SQL sobre los archivos Parquet de la capa analítica. La Figura 1 presenta la arquitectura completa.

A esta base se incorporó un módulo de captura y mantenimiento de datos, compuesto por una función Lambda y un formulario web. El módulo permite registrar y actualizar información sin acceso a la consola de AWS, y valida las reglas de negocio antes de escribir cualquier dato (véase 1.5). El resultado es un flujo continuo: desde la captura validada de un registro de compra hasta su disponibilidad para consulta analítica, sin intervención manual entre ambas etapas.

## **4.2 Identificación de usuarios**

El personal de compras registra y consulta proveedores, productos, categorías y órdenes de compra a través del formulario web. No requiere conocimiento técnico de AWS ni acceso a credenciales de la cuenta. Este perfil motivó el diseño del módulo de captura (4.3.5). La Figura 7 muestra la interfaz que utiliza.

El personal analítico utiliza los resultados de las consultas de Athena para obtener los indicadores definidos en 3.6: costo por periodo, gasto por categoría, gasto por proveedor y lead time promedio. Este perfil no interactúa con el formulario de captura ni necesita conocer la estructura interna del Data Warehouse.

Ambos perfiles comparten el mismo origen de datos. Acceden a él por rutas distintas: uno escribe a través de una interfaz validada; el otro solo lee, a través de consultas ya preparadas.

## **4.3 Modelado del negocio**

### **4.3.1 Design Science Research (DSR)**

El proyecto aplica Design Science Research como marco de trabajo. DSR estructura la investigación en cuatro fases: identificación del problema, diseño de la solución, construcción del artefacto y evaluación (véase 3.1). El artefacto central de este proyecto es el propio Data Warehouse, junto con el módulo de captura que lo alimenta.

### **4.3.2 Ciclo de vida**

El desarrollo siguió un ciclo mayormente secuencial. Cada componente se evaluó de inmediato después de construirse. Las consultas de Athena se validaron contra datos reales al terminar cada una (véase 3.6). El módulo de captura se probó de forma funcional sobre la Lambda ya desplegada.

### **4.3.3 Características**

La solución es serverless: no administra servidores ni instancias, solo servicios gestionados por AWS. Su modelo de costo es de pago por uso; durante la fase de pruebas el costo verificado fue de $0.00, dentro de la capa gratuita (véase 3.3.1). La escritura validada de datos, realizada a través de la Lambda, está separada de la lectura analítica, realizada a través de Athena. Ningún usuario final requiere permisos amplios sobre el bucket de datos.

El modelo de datos sigue un esquema estrella normalizado, con tablas puente para las relaciones de múltiples valores. Este diseño permite consultas de negocio directas, como identificar qué proveedores vigentes suministran una categoría de producto determinada, sin recorrer manualmente el historial de compras.

### **4.3.4 Fases**

El desarrollo se ejecutó en cinco fases. Primero, la carga de los archivos fuente a la zona raw de S3. Segundo, la transformación y el almacenamiento en formato Parquet en las zonas curated y analytics. Tercero, la catalogación de las tablas resultantes en Glue Data Catalog. Cuarto, la construcción y validación de las consultas SQL de los indicadores en Athena. Quinto, el diseño e implementación del módulo de captura con validación de reglas de negocio. La Figura 3 muestra el flujo de datos entre estas fases, desde el origen hasta la disponibilidad para consulta.

### **4.3.5 Artefactos**

La Tabla 11 resume los artefactos producidos y la tecnología que los soporta.

##### **Tabla 11**

###### *Módulos y tecnologías del Data Warehouse*

| Módulo | Tecnología | Artefacto producido |
| ----- | ----- | ----- |
| Almacenamiento por capas | Amazon S3 (raw / curated / analytics) | Estructura de bucket (Figura 4) |
| Transformación de datos | Python (pandas, pyarrow) | Script transformar_a_parquet.py |
| Catalogación de esquema | AWS Glue Data Catalog | 14 tablas registradas (Figura 5) |
| Consulta analítica | Amazon Athena | 6 consultas SQL, resultado de ejemplo en Figura 6 |
| Captura y mantenimiento validado | AWS Lambda + Function URL | Función maghsa-captura-compras |
| Interfaz de captura | Sitio estático en S3 | Formulario (Figura 7) |
| Modelo relacional de referencia | SQLite | Archivo de apoyo, complementario a la Figura 2 |

*Nota. Elaboración propia (2026).*

# **Capítulo V - Diseño de la Aplicación**

## **5.1 Diagramas UML**

Los diagramas UML describen el comportamiento y la estructura del módulo de captura, de la cadena de transformación y consulta, y de la relación entre ambos. Se presentan los diagramas que aportan información al diseño. El diagrama de estados se omite, porque las entidades del sistema no tienen ciclos de vida con transiciones relevantes, más allá del campo estado del proveedor (vigente o inactivo).

### **5.1.1 Diagrama de casos de uso**

La Figura 8 presenta los casos de uso del sistema. Intervienen los dos perfiles definidos en 4.2. El personal de compras ejecuta los casos de captura y mantenimiento (CU-01 a CU-06), a través del formulario de la Figura 7. El personal analítico ejecuta los casos de consulta y visualización (CU-08 y CU-09).

Las relaciones de inclusión expresan dependencias obligatorias. Todo registro de compra incluye la autenticación (CU-01) y la validación de reglas de negocio (CU-07). La gestión de proveedores (CU-03) también incluye CU-07, porque las categorías de producto y los productos asociados deben ser compatibles con las categorías del proveedor. La visualización del dashboard (CU-09) incluye la consulta de indicadores (CU-08), porque Power BI obtiene los datos mediante Athena.

La Tabla 12 describe los casos de uso de mayor impacto en el diseño.

##### **Tabla 12**

###### *Especificación resumida de casos de uso principales*

| Caso de uso | Actor | Precondición | Flujo principal | Flujo alterno |
| ----- | ----- | ----- | ----- | ----- |
| CU-02 Registrar orden de compra | Personal de compras | Acceso validado | Selecciona proveedor, producto y unidad organizacional; ingresa fecha, cantidad y precio; el sistema valida y registra la orden con un identificador correlativo | El sistema rechaza la solicitud con una lista de errores (proveedor sin el producto, cantidad o precio no positivos, fecha futura) |
| CU-03 Gestionar proveedores y asociaciones | Personal de compras | Acceso validado | Registra o actualiza el proveedor, sus categorías, productos y contacto | El sistema rechaza categorías o productos incompatibles con las categorías de proveedor marcadas |
| CU-08 Consultar indicadores en Athena | Personal analítico | Tablas catalogadas en Glue | Ejecuta una de las consultas definidas y obtiene el resultado agregado | La consulta no devuelve filas si el periodo no tiene datos |

*Nota. Elaboración propia (2026).*

### **5.1.2 Diagrama de actividades**

La Figura 9 describe las actividades del caso CU-02, que concentra la lógica de validación del sistema. El flujo inicia con el ingreso del código de acceso y termina con la confirmación visible para el usuario.

El diagrama contiene dos decisiones. La primera verifica el código de acceso; un código inválido produce una respuesta 403. La segunda verifica las reglas de negocio contra los maestros leídos desde S3; un incumplimiento produce una respuesta 400 con la lista de errores. En ambos casos, el flujo retorna a la captura de datos para su corrección. Si se superan las dos verificaciones, la función asigna el identificador, reescribe el archivo CSV de la zona raw y devuelve la confirmación. El flujo completo, desde la carga de los archivos fuente hasta la disponibilidad para consulta, se presenta en la Figura 3.

### **5.1.3 Diagrama de secuencia**

La Figura 10 muestra la interacción entre los componentes durante el registro de una orden de compra. El formulario envía una solicitud POST en formato JSON a la Function URL. La función Lambda verifica el código de acceso, lee los maestros necesarios desde S3, ejecuta la validación y, solo si esta es satisfactoria, escribe el registro nuevo. La lectura previa de los maestros asegura que la validación se aplique sobre el estado vigente de los datos. La escritura se realiza una sola vez por solicitud y reemplaza el archivo completo, lo que evita estados intermedios parcialmente escritos.

La Figura 11 muestra la interacción de consulta. Power BI envía una consulta SQL a Athena mediante el conector correspondiente. Athena obtiene del Glue Data Catalog el esquema, la ubicación y las particiones de las tablas, lee solo los archivos Parquet de las particiones requeridas y escribe el resultado en la ubicación athena-results/. Esta secuencia es la misma para cualquiera de las consultas de indicadores. La Figura 6 presenta el resultado de una de ellas.

### **5.1.4 Diagrama de componentes**

La Figura 12 presenta los componentes de software y sus interfaces. Los módulos y tecnologías se resumen en la Tabla 11. El módulo de captura se compone de cuatro componentes internos: el enrutador de solicitudes (lambda_handler), el control de acceso, el validador de reglas de negocio y el repositorio CSV sobre S3. El enrutador recibe la solicitud, delega la autenticación y la validación, y utiliza el repositorio para leer y escribir.

La Tabla 13 define las interfaces entre componentes. La interfaz principal es el contrato JSON de la Function URL, que desacopla el formulario de la lógica de validación: cualquier cliente que respete el contrato puede sustituir al formulario sin modificar la función.

##### **Tabla 13**

###### *Interfaces entre componentes*

| Interfaz | Origen → Destino | Protocolo y formato | Contenido |
| ----- | ----- | ----- | ----- |
| Solicitud de captura | Formulario → Lambda | HTTPS, POST, JSON | codigo_acceso, entidad, accion (listar, crear, actualizar, eliminar), datos |
| Respuesta de captura | Lambda → Formulario | HTTPS, JSON | Código 200 o 201 con mensaje y registro; código 400, 403 o 404 con lista errores |
| Persistencia raw | Lambda → S3 | API de S3 (GetObject, PutObject, ListBucket) | Archivos CSV por entidad, restringidos al prefijo raw/ |
| Transformación | Script → S3 | Lectura de CSV, escritura de Parquet | Zonas curated y analytics, particionadas por año y mes |
| Catalogación | Glue → S3 | Definición de tablas sobre prefijos | Esquema de 12 tablas en la base compras_dwh |
| Consulta analítica | Power BI → Athena | Conector de Athena, SQL | Consultas de indicadores y resultado tabular |

*Nota. Elaboración propia (2026).*

### **5.1.5 Diagrama de objetos**

La Figura 13 muestra una instancia concreta del modelo: la orden de compra OC0001 del conjunto de datos de prueba y los objetos con los que se relaciona. La orden registra 20 unidades del producto PROD001 al proveedor PRV001, para la unidad organizacional Mantenimiento. El producto pertenece a la categoría CAT01 y el proveedor pertenece a la categoría de proveedor Repuestos. La instancia ilustra la regla de integridad aplicada en el registro: el par PRV001–PROD001 existe en la asociación proveedor–producto, por lo que la orden es válida.

### **5.1.6 Diagrama de clases**

La Figura 14 presenta las clases del dominio de compras, con sus atributos, multiplicidades y relaciones. La clase OrdenCompra se asocia con exactamente un proveedor, un producto y una unidad organizacional. El método monto_total() representa el cálculo del campo derivado (cantidad por precio unitario), que el script de transformación incorpora a la tabla de hechos.

Las relaciones de múltiples valores reflejan las reglas del negocio. Un proveedor se clasifica en una o más categorías de proveedor. Cada categoría de proveedor permite una o más categorías de producto. Un proveedor suministra categorías de producto y ofrece productos específicos, y cada producto pertenece a una sola categoría. Estas relaciones se resuelven en el modelo físico mediante tablas puente (5.2). El módulo de captura se implementa con funciones y no con orientación a objetos; por ello, el diagrama modela el dominio y no la estructura del código.

### **5.1.7 Diagrama de entidad relación**

El diagrama entidad relación del modelo de datos corresponde a la Figura 2 y se describe en 5.2.

## **5.2 Entidad Relación**

El modelo de datos sigue un esquema estrella con una tabla de hechos y dimensiones, complementado con tablas puente para las relaciones de muchos a muchos y con una tabla de reglas de negocio. La Figura 2 presenta el diagrama completo, con 12 tablas y sus relaciones, y la Figura 5 muestra su registro en AWS Glue Data Catalog. La Tabla 14 resume las entidades según su función.

##### **Tabla 14**

###### *Entidades del modelo de datos*

| Tipo | Tabla | Clave | Descripción |
| ----- | ----- | ----- | ----- |
| Hechos | hechos_compras | id_compra | Una fila por línea de orden de compra; contiene medidas (cantidad, precio unitario, monto total, lead time) y claves de las dimensiones |
| Dimensión | dim_proveedor | proveedor_id | Datos del proveedor y su estado |
| Dimensión | dim_producto | producto_id | Producto, unidad de medida y categoría |
| Dimensión | dim_categoria | categoria_id | Categoría de producto y familia de gasto |
| Dimensión | dim_unidad_organizacional | unidad_organizacional_id | Unidad solicitante (Mantenimiento, Producción, Operación) |
| Dimensión | dim_tiempo | fecha_id | Atributos de calendario para el análisis por periodo |
| Dimensión | dim_categoria_proveedor | categoria_proveedor_id | Clasificación del proveedor |
| Dimensión | dim_contacto_proveedor | proveedor_id | Persona de contacto, teléfonos y correos |
| Puente | puente_proveedor_categoria_proveedor | (proveedor_id, categoria_proveedor_id) | Clasificación múltiple del proveedor |
| Puente | puente_proveedor_categoria_producto | (proveedor_id, categoria_id) | Categorías de producto que suministra el proveedor |
| Puente | puente_proveedor_producto | (proveedor_id, producto_id) | Productos que ofrece el proveedor |
| Regla de negocio | categoria_proveedor_x_categoria_producto | (categoria_proveedor_id, categoria_id) | Combinaciones permitidas; valida la captura y no se une a los hechos |

*Nota. Elaboración propia (2026).*

Los hechos se relacionan con las dimensiones de proveedor, producto, categoría, unidad organizacional y tiempo mediante relaciones de uno a muchos. Esta estructura permite consultas por periodo, proveedor, categoría de gasto y unidad organizacional. Las tablas puente se excluyen de las uniones directas con los hechos, porque duplicarían filas y distorsionarían las sumas; las consultas que necesitan atributos de una relación múltiple los agregan previamente en una subconsulta.

La tabla puente_proveedor_producto no almacena la categoría del producto, que se obtiene de la tabla de productos y evita así la redundancia. La coherencia entre las categorías marcadas para el proveedor y sus productos se verifica en la función Lambda durante la captura. La tabla de hechos conserva el campo categoria_id para analizar el gasto por categoría sin uniones adicionales.

## **5.3 Diagramas de infraestructura**

### **5.3.1 Arquitectura general**

La arquitectura de la solución, presentada en la Figura 1, se organiza en capas desacopladas. Cada capa utiliza un servicio administrado de AWS, y las capas se comunican mediante las interfaces de la Tabla 13. Tres decisiones de diseño sustentan esta organización. Primero, la escritura y la lectura se separan: el personal de compras escribe solo a través de la función Lambda, y el personal analítico lee solo a través de Athena. Segundo, el almacenamiento y el cómputo se desacoplan, de modo que el costo de consulta depende del volumen escaneado y no de infraestructura permanente. Tercero, los datos se conservan en formatos abiertos (CSV y Parquet), lo que permite sustituir el motor de consulta sin migrar los datos. La organización por zonas del almacenamiento se muestra en la Figura 4.

### **5.3.2 Infraestructura en AWS**

La Figura 15 presenta los recursos desplegados en la región us-east-1, agrupados en captura, data lake, y catálogo y consulta. El personal de compras accede al formulario alojado en un sitio estático de S3. El formulario invoca la Function URL de la función Lambda, que opera con un rol IAM limitado y registra su ejecución en CloudWatch Logs. La función escribe en la zona raw del data lake. El script de transformación, ejecutado de forma local, lee la zona raw y escribe las zonas curated y analytics. Glue Data Catalog registra las tablas de la zona analytics, y Athena las consulta y almacena sus resultados en un prefijo dedicado. Power BI se conecta a Athena.

La Tabla 15 identifica los recursos y su configuración relevante.

##### **Tabla 15**

###### *Recursos de infraestructura y configuración*

| Recurso | Identificación | Configuración relevante |
| ----- | ----- | ----- |
| Bucket del data lake | maghsa-dwh-compras-070366844944 | Prefijos raw/, curated/, analytics/ y athena-results/; particiones por año y mes |
| Bucket del formulario | maghsa-captura-web-070366844944 | Alojamiento de sitio web estático |
| Función Lambda | maghsa-captura-compras | Python 3.12; Function URL con CORS; variables de entorno BUCKET_NAME y ACCESS_CODE |
| Rol IAM | maghsa-captura-lambda-role | Política acceso-raw-bucket: lectura y escritura sobre raw/\*; listado condicionado al prefijo raw/\* |
| Base de datos de catálogo | compras_dwh | 12 tablas registradas en Glue Data Catalog |
| Motor de consulta | Amazon Athena | Resultados en athena-results/; consultas sobre formato Parquet |

*Nota. Elaboración propia (2026).*

### **5.3.3 Integraciones**

Las integraciones del sistema se limitan a servicios de AWS y a un conector de Power BI. El formulario se comunica con la función mediante HTTPS y JSON. La función accede al data lake mediante el SDK de AWS, con permisos restringidos al prefijo raw/. Power BI accede a Athena mediante su conector. Ningún componente requiere servidores dedicados. El control de acceso del formulario es un código compartido, previsto para la fase de pruebas y sustituible por un servicio de autenticación en un entorno empresarial.

### **5.3.4 Correspondencia entre objetivos y diseño**

La Tabla 16 relaciona los objetivos específicos del apartado 1.4.2, el módulo de ingesta validada del apartado 1.5 y el principio de bajo costo del objetivo general con los elementos de diseño que los atienden.

##### **Tabla 16**

###### *Correspondencia entre objetivos, procesos y elementos de diseño*

| Requerimiento | Proceso | Elementos de diseño |
| ----- | ----- | ----- |
| Objetivo específico 1: definir el modelo dimensional de compras | Modelado de datos | Figuras 2, 13 y 14; Tabla 14 |
| Objetivo específico 2: organizar el almacenamiento en Amazon S3 | Transformación y almacenamiento por zonas | Figuras 3 y 4; Tabla 15 |
| Objetivo específico 3: catalogar los datasets en Glue Data Catalog | Catalogación | Figuras 5 y 15; Tabla 13 |
| Objetivo específico 4: implementar visualizaciones en Power BI a partir de Athena | CU-08 y CU-09 | Figuras 8, 11 y 12 |
| Objetivo específico 5: validar el funcionamiento del DWH | CU-08 | Figuras 6 y 11 |
| Módulo de ingesta validada (1.5) | CU-01, CU-02, CU-03 y CU-07 | Figuras 7, 9, 10 y 12; Tablas 12 y 13 |
| Objetivo general: simplicidad operativa y bajo costo de mantenimiento | Toda la solución | Servicios administrados de la Tabla 11; Figuras 1 y 15 |

*Nota. Elaboración propia (2026).*

El diseño cubre los cinco objetivos específicos y el módulo de ingesta validada: cada uno cuenta con al menos un proceso y un elemento de diseño asociado.

# **Conclusiones**

[PENDIENTE: contenido no incluido en el documento fuente]

# **Recomendaciones**

[PENDIENTE: contenido no incluido en el documento fuente]

# **Glosario**

**Amazon Athena.** Servicio de consultas interactivo y serverless de AWS que permite analizar datos almacenados en Amazon S3 mediante SQL estándar, sin necesidad de aprovisionar ni administrar servidores. Su modelo de facturación se basa en la cantidad de datos procesados por consulta.

**Amazon S3 (Simple Storage Service).** Servicio de almacenamiento de objetos de AWS diseñado para ofrecer escalabilidad, disponibilidad y durabilidad. En arquitecturas analíticas, actúa como capa de almacenamiento central del Data Lake, organizando los datos en prefijos lógicos y zonas por nivel de madurez.

**API (Application Programming Interface).** Interfaz de programación que permite la comunicación entre sistemas de software mediante un conjunto de definiciones y protocolos estandarizados.

**Arquitectura Medallion.** Patrón de diseño para repositorios analíticos que organiza los datos en tres capas progresivas de calidad: Bronze (datos brutos), Silver (datos validados y depurados) y Gold (datos listos para consumo analítico). Su objetivo es mejorar de forma incremental la estructura y confiabilidad del dato a medida que avanza por cada capa.

**AWS (Amazon Web Services).** Plataforma de servicios de computación en la nube de Amazon que ofrece infraestructura, plataforma y software como servicio. Incluye servicios de almacenamiento, cómputo, bases de datos, analítica, seguridad e inteligencia artificial, entre otros.

**AWS Glue Data Catalog.** Repositorio centralizado de metadatos de AWS que almacena información técnica sobre los conjuntos de datos de una organización, incluyendo ubicación, esquema, particiones y propiedades. Se integra de forma nativa con Amazon Athena y otros servicios analíticos.

**AWS IAM (Identity and Access Management).** Servicio de AWS que permite gestionar de forma segura el acceso a los recursos de la nube mediante la definición de usuarios, grupos, roles y políticas de permisos, siguiendo el principio de mínimo privilegio.

**Bucket (S3).** Contenedor lógico de nivel superior en Amazon S3 utilizado para almacenar objetos. Cada bucket posee un nombre único a nivel global dentro de la nube de AWS y funciona como la unidad base de organización, permisos y facturación del almacenamiento.

**Business Intelligence (BI).** Conjunto de estrategias, procesos, tecnologías y herramientas que permiten recopilar, transformar y analizar datos con el fin de apoyar la toma de decisiones organizacionales mediante reportes, dashboards e indicadores.

**Catálogo de datos.** Repositorio centralizado que almacena metadatos sobre los activos de datos de una organización, facilitando su descubrimiento, comprensión y gobierno. Incluye información sobre esquemas, propietarios, linaje y reglas de uso.

**Cifrado at-rest / in-transit.** Mecanismos de seguridad que protegen los datos mientras se encuentran almacenados (at-rest) o mientras se transmiten entre sistemas (in-transit), asegurando su confidencialidad e integridad mediante algoritmos criptográficos.

**Completitud.** Dimensión de calidad de datos que indica el grado en que los campos requeridos de un registro contienen valores válidos y no nulos, indispensable para garantizar que los indicadores analíticos sean representativos.

**Computación serverless.** Paradigma de computación en la nube en el que el proveedor administra de forma automática la infraestructura de cómputo (aprovisionamiento, escalado, parches, capacidad), permitiendo que el usuario se enfoque en la lógica de la solución y pague únicamente por el consumo real de recursos.

**Consistencia.** Dimensión de calidad de datos que indica que los valores almacenados no se contradicen entre sí a través de tablas, fuentes o periodos de tiempo distintos.

**Crawler.** Componente de AWS Glue que escanea automáticamente orígenes de datos para extraer y actualizar metadatos en el Data Catalog, incluyendo esquemas, tipos de datos y particiones, sin requerir intervención manual.

**Dashboard.** Panel de control interactivo que presenta indicadores clave de desempeño (KPIs) y métricas relevantes de forma visual y resumida, con el propósito de facilitar el monitoreo de procesos y la toma de decisiones.

**Data Lake.** Repositorio centralizado que permite almacenar datos estructurados, semiestructurados y no estructurados a escala, conservando el dato en su formato original. En el contexto del presente trabajo, Amazon S3 cumple esta función.

**Data Warehouse (DWH).** Sistema de almacenamiento analítico orientado a consultas e informes, que integra datos de múltiples fuentes bajo un modelo estructurado y optimizado para el análisis histórico y la generación de indicadores de negocio.

**DAX (Data Analysis Expressions).** Lenguaje de fórmulas utilizado en Power BI para crear medidas y columnas calculadas de forma dinámica. Permite construir cálculos como agregaciones, variaciones temporales, acumulados y porcentajes en función del contexto de filtro aplicado por el usuario.

**Design Science Research (DSR).** Paradigma de investigación en Sistemas de Información orientado a la creación y evaluación de artefactos tecnológicos que resuelven problemas organizacionales identificados. Contempla ciclos iterativos de diseño, demostración y evaluación del artefacto.

**Dimensión (modelo dimensional).** Tabla en un esquema estrella que contiene atributos descriptivos mediante los cuales se segmenta y contextualiza el análisis. Ejemplos: dimensión tiempo, dimensión proveedor, dimensión producto.

**ELT (Extract, Load, Transform).** Estrategia de integración de datos en la que los datos se extraen de las fuentes, se cargan en el repositorio analítico y se transforman posteriormente en el propio entorno de destino. Es el enfoque predominante en arquitecturas modernas en la nube.

**Esquema estrella (star schema).** Véase Modelo dimensional.

**ETL (Extract, Transform, Load).** Estrategia de integración de datos en la que los datos se extraen de las fuentes, se transforman antes de ser cargados y finalmente se almacenan en el repositorio analítico de destino.

**Formato Parquet.** Formato de archivo columnar de código abierto optimizado para consultas analíticas, ya que permite leer únicamente las columnas necesarias y aplica compresión eficiente. Su uso en S3 mejora el rendimiento y reduce el costo de las consultas en Athena.

**Gobernanza del dato.** Conjunto de políticas, procesos y mecanismos que aseguran que los datos sean confiables, seguros, descubribles y trazables desde su origen hasta su consumo analítico. Incluye la gestión de metadatos, control de acceso, linaje y calidad.

**Hechos (tabla de hechos).** Tabla central en un esquema estrella que almacena las métricas o eventos cuantificables del negocio, como montos de compra, cantidades y fechas, junto con las claves foráneas que la vinculan con las tablas de dimensiones.

**Indicador clave de desempeño (KPI).** Métrica cuantificable utilizada para evaluar el nivel de desempeño de un proceso, área o resultado estratégico en función de objetivos previamente definidos.

**Ingestión de datos.** Proceso de recopilación y carga de datos desde sus fuentes de origen hacia un repositorio analítico o Data Lake, ya sea de forma manual, programada o automatizada.

**Infraestructura como código (IaC).** Práctica de gestionar y aprovisionar infraestructura tecnológica mediante archivos de configuración legibles por máquina, en lugar de procesos manuales, favoreciendo la reproducibilidad y el control de versiones.

**KPI.** Véase Indicador clave de desempeño.

**Lead time.** Tiempo transcurrido entre la emisión de una orden de compra y la recepción del bien o servicio solicitado. Es un indicador de eficiencia en la gestión de proveedores y cadena de abastecimiento.

**Linaje de datos.** Capacidad de rastrear el origen de un dato, las transformaciones que ha sufrido y los sistemas por los que ha pasado, desde su creación hasta su uso en análisis o reportes.

**Maestro de datos.** Conjunto de datos de referencia que define de forma única las entidades fundamentales del negocio, como proveedores, productos o clientes, asegurando que estas entidades sean representadas de manera consistente en todos los sistemas.

**Metadatos.** Datos que describen a otros datos. En el contexto analítico, incluyen información sobre esquemas, tipos de campo, ubicaciones, fechas de actualización, propietarios y reglas de uso de los datasets.

**Modelo dimensional.** Enfoque de modelado de datos para entornos analíticos que organiza la información en tablas de hechos y dimensiones, optimizando el rendimiento de las consultas y facilitando el análisis multidimensional.

**Particionamiento.** Técnica de organización de datos en S3 que divide los datasets en subconjuntos lógicos según valores de una o más columnas (por ejemplo, año, mes, proveedor), permitiendo que Athena lea únicamente las particiones relevantes para una consulta y reduciendo el costo de procesamiento.

**Power BI.** Herramienta de Microsoft para inteligencia de negocios que permite conectar, modelar y visualizar datos provenientes de múltiples fuentes mediante dashboards interactivos y medidas DAX. En el presente trabajo, se utiliza como capa de presentación conectada a Amazon Athena.

**Trazabilidad.** Dimensión de calidad de datos que indica la capacidad de rastrear el origen y el historial de transformaciones de un dato, permitiendo reconstruir su procedencia dentro del flujo analítico.

**Unicidad.** Dimensión de calidad de datos que evalúa que los registros de un conjunto de datos no se encuentren duplicados cuando deben representar entidades únicas, evitando el doble conteo en los indicadores analíticos.

# **Bibliografía**

Mayor Cebrian, A. (2025). Sistema ETL automatizado y escalable en la nube \[Treball Final de Grau, Universitat Politècnica de Catalunya\]. UPCommons. https://hdl.handle.net/2117/431574

Palan Murillo, J. D. (2025). Gobernanza del dato en sistemas analíticos y de IA en AWS \[Trabajo Fin de Máster, Universidad Europea de Madrid\]. Repositorio TITULA. https://hdl.handle.net/20.500.12880/13602

Muñoz Ramírez, L. A. (2025). Evaluación de la calidad de datos mediante análisis exploratorio para la detección de inconsistencias en la base de datos de asociados de Promedico \[Proyecto aplicado\]. Repositorio Institucional UNAD. https://repository.unad.edu.co/handle/10596/73339

Kamlofsky, J. (2022). Computación en la nube: Fundamentos, críticas y desafíos. Revista Abierta de Informática Aplicada, 6(2), 3–30. https://doi.org/10.59471/raia20222

Marceliano Alcantara, R. & Villarreal Tello, I. A. (2025). Diseño e implementación de un prototipo de portal serverless de centralización y automatización en AWS con integración de agentes de IA y bots para la administración de más de 4000 cuentas en una organización orientada a la transformación digital \[Tesis de grado, Universidad Peruana de Ciencias Aplicadas\]. Repositorio Académico UPC. http://hdl.handle.net/10757/688167

Berbel Carballal, J. (2025). Modelo de costes para la gestión y optimización de gastos de una organización para entornos multi-cloud \[Trabajo Fin de Máster, Universidad de A Coruña\]. RUC – Repositorio Universitario da UDC. http://hdl.handle.net/2183/45882

López Saldarriaga, D. A. (2025). Implementación de analítica descriptiva y predictiva a partir de una arquitectura serverless en la nube para pymes \[Tesis de maestría, Universidad Nacional de Colombia\]. Repositorio Institucional UN. https://repositorio.unal.edu.co/handle/unal/89135

Rodríguez Serrato, J. D. & Quiñonez Zapata, M. C. (2025). Automatización del aprovisionamiento de infraestructura para lagos de datos (Data Lakes) en la nube de AWS para organizaciones data driven \[Tesis de grado, Universidad Distrital Francisco José de Caldas\]. Repositorio Institucional UD. https://repository.udistrital.edu.co/items/30a2c9d9-6708-4ce6-869f-736b5b10ad59

Landa Felices, R. A. & Lujan Canicela, O. J. (2024). Integración de servicios de AWS enfocado al uso de DevSecOps para mejorar el rendimiento y la seguridad en proyectos de Data & Analytics \[Tesis de grado, Universidad Peruana de Ciencias Aplicadas\]. Repositorio Académico UPC. http://hdl.handle.net/10757/674691 

Merchán Millán, C. & Azúa Campos, M. S. (2018). Análisis de brechas de seguridad en el acceso a datos en la nube para soluciones Big Data \[Tesis de posgrado, Universidad de Especialidades Espíritu Santo\]. Repositorio Institucional UEES. http://repositorio.uees.edu.ec/123456789/2760

Hevner, A. R., March, S. T., Park, J. & Ram, S. (2004). Design science in information systems research. MIS Quarterly, 28(1), 75–105. https://doi.org/10.2307/25148625

Peffers, K., Tuunanen, T., Rothenberger, M. A. & Chatterjee, S. (2007). A design science research methodology for information systems research. Journal of Management Information Systems, 24(3), 45–77. https://doi.org/10.2753/MIS0742-1222240302

# **Anexos**

##### **Figura 1**

###### *Arquitectura de la solución del Data Warehouse serverless*

![Figura 1 Arquitectura de la solución del Data Warehouse serverless](figuras/figura-01.png)

*Nota. Elaboración propia (2026).*

##### **Figura 2**

###### *Diagrama entidad-relación del modelo dimensional de compras*

![Figura 2 Diagrama entidad-relación del modelo dimensional de compras](figuras/figura-02.png)

*Nota. Elaboración propia (2026).*

##### **Figura 3**

###### *Diagrama de proceso de extremo a extremo*

![Figura 3 Diagrama de proceso de extremo a extremo](figuras/figura-03.png)

*Nota. Elaboración propia (2026).*

##### **Figura 4**

###### *Estructura de zonas del Data Lake en Amazon S3*

![Figura 4 Estructura de zonas del Data Lake en Amazon S3](figuras/figura-04.png)

*Nota. Elaboración propia (2026).*

##### **Figura 5**

###### *Tablas del esquema dimensional registradas en AWS Glue Data Catalog*

![Figura 5 Tablas del esquema dimensional registradas en AWS Glue Data Catalog](figuras/figura-05.png)

*Nota. Elaboración propia (2026).*

##### **Figura 6**

###### *Resultado de la consulta de costo total de compras por periodo en Amazon Athena*

![Figura 6 Resultado de la consulta de costo total de compras por periodo en Amazon Athena](figuras/figura-06.png)

*Nota. Elaboración propia (2026).*

##### **Figura 7**

###### *Formulario de captura de datos de compras*

![Figura 7 Formulario de captura de datos de compras](figuras/figura-07.png)

*Nota. Elaboración propia (2026).*

##### **Figura 8**

###### *Diagrama de casos de uso del sistema*

![Figura 8 Diagrama de casos de uso del sistema](figuras/figura-08.png)

*Nota. Elaboración propia (2026).*

##### **Figura 9**

###### *Diagrama de actividades del registro de una orden de compra*

![Figura 9 Diagrama de actividades del registro de una orden de compra](figuras/figura-09.png)

*Nota. Elaboración propia (2026).*

##### **Figura 10**

###### *Diagrama de secuencia del registro de una orden de compra*

![Figura 10 Diagrama de secuencia del registro de una orden de compra](figuras/figura-10.png)

*Nota. Elaboración propia (2026).*

##### **Figura 11**

###### *Diagrama de secuencia de la consulta de indicadores*

![Figura 11 Diagrama de secuencia de la consulta de indicadores](figuras/figura-11.png)

*Nota. Elaboración propia (2026).*

##### **Figura 12**

###### *Diagrama de componentes del sistema*

![Figura 12 Diagrama de componentes del sistema](figuras/figura-12.png)

*Nota. Elaboración propia (2026).*

##### **Figura 13**

###### *Diagrama de objetos de la orden de compra OC0001*

![Figura 13 Diagrama de objetos de la orden de compra OC0001](figuras/figura-13.png)

*Nota. Elaboración propia (2026).*

##### **Figura 14**

###### *Diagrama de clases del dominio de compras*

![Figura 14 Diagrama de clases del dominio de compras](figuras/figura-14.png)

*Nota. Elaboración propia (2026).*

##### **Figura 15**

###### *Diagrama de infraestructura de la solución en AWS*

![Figura 15 Diagrama de infraestructura de la solución en AWS](figuras/figura-15.png)

*Nota. Elaboración propia (2026).*
