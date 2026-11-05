"""
Genera datos sinteticos ampliados (enero-octubre 2026) para el Data Warehouse de compras de MAGHSA, S.A.

Agrega proveedores, productos y relaciones a los CSV de sample-data/ y regenera
registro_compras.csv (conservando OC0001-OC0010). Usa solo la biblioteca estandar y una
semilla fija, por lo que el resultado es reproducible.

Uso: python scripts/generar_datos_dummy.py   (desde la raiz del repositorio)
"""
import csv, random
from pathlib import Path

SD = Path(__file__).resolve().parent.parent / "sample-data"

NUEVOS = {
    "maestro_proveedores.csv": [
        ["PRV007", "Aceros del Pacifico S.A.", "Guatemala", "Escuintla", "45 dias", "vigente"],
        ["PRV008", "Lubricantes y Aditivos del Centro", "Guatemala", "Guatemala", "30 dias", "vigente"]],
    "contacto_proveedor.csv": [
        ["PRV007", "Luis Fernando Garcia", "5578-8899", "lgarcia@acerospacifico.com.gt"],
        ["PRV008", "Sofia Herrera", "5589-9900", "sherrera@lubricantescentro.com.gt"]],
    "proveedor_categoria_proveedor.csv": [["PRV007", "CATPROV02"], ["PRV008", "CATPROV04"]],
    "proveedor_categoria_producto.csv": [["PRV007", "CAT04"], ["PRV008", "CAT02"], ["PRV003", "CAT01"]],
    "maestro_productos.csv": [
        ["PROD007", "Filtro de aire de motor", "CAT01", "unidad", "Filtro de aire para motor diesel de tractores"],
        ["PROD008", "Aceite de motor 15W-40", "CAT02", "galon", "Lubricante para motores diesel"],
        ["PROD009", "Barra de acero redonda 1 pulgada", "CAT04", "unidad", "Barra para fabricacion de ejes y piezas"],
        ["PROD010", "Servicio de soldadura industrial", "CAT05", "servicio", "Soldadura de estructuras y implementos"],
        ["PROD011", "Gasolina super", "CAT06", "galon", "Combustible para vehiculos livianos"]],
    "proveedor_x_producto.csv": [
        ["PRV003", "PROD001"], ["PRV003", "PROD007"], ["PRV001", "PROD007"], ["PRV004", "PROD008"],
        ["PRV008", "PROD008"], ["PRV008", "PROD002"], ["PRV002", "PROD009"], ["PRV007", "PROD009"],
        ["PRV007", "PROD004"], ["PRV005", "PROD010"], ["PRV003", "PROD011"]],
}

BASE = """OC0001,2026-06-03,PRV001,PROD001,CAT01,UO01,20,45.50,GTQ,30 dias,5
OC0002,2026-06-10,PRV004,PROD002,CAT02,UO01,50,120.00,GTQ,30 dias,3
OC0003,2026-06-15,PRV003,PROD006,CAT06,UO03,500,28.75,GTQ,contado,1
OC0004,2026-07-02,PRV002,PROD004,CAT04,UO02,100,310.00,GTQ,60 dias,10
OC0005,2026-07-08,PRV005,PROD005,CAT05,UO02,15,850.00,GTQ,45 dias,7
OC0006,2026-07-19,PRV001,PROD003,CAT03,UO01,8,4200.00,GTQ,30 dias,15
OC0007,2026-08-01,PRV004,PROD002,CAT02,UO01,40,120.00,GTQ,30 dias,4
OC0008,2026-08-05,PRV003,PROD006,CAT06,UO03,600,29.10,GTQ,contado,1
OC0009,2026-08-12,PRV002,PROD004,CAT04,UO02,80,315.00,GTQ,60 dias,9
OC0010,2026-08-18,PRV001,PROD001,CAT01,UO01,25,46.00,GTQ,30 dias,6"""

# producto: (categoria, unidad_org, precio base, cantidad min, cantidad max)
PROD = {"PROD001": ("CAT01", "UO01", 45.5, 15, 40), "PROD002": ("CAT02", "UO01", 120, 30, 60),
        "PROD003": ("CAT03", "UO01", 4200, 4, 10), "PROD004": ("CAT04", "UO02", 310, 60, 120),
        "PROD005": ("CAT05", "UO02", 850, 8, 20), "PROD006": ("CAT06", "UO03", 28.75, 400, 700),
        "PROD007": ("CAT01", "UO01", 85, 10, 30), "PROD008": ("CAT02", "UO01", 165, 20, 50),
        "PROD009": ("CAT04", "UO02", 190, 30, 80), "PROD010": ("CAT05", "UO02", 1200, 3, 10),
        "PROD011": ("CAT06", "UO03", 33.5, 100, 250)}
OFERTA = {"PRV001": ["PROD001", "PROD003", "PROD007"], "PRV002": ["PROD004", "PROD009"],
          "PRV003": ["PROD006", "PROD011", "PROD001", "PROD007"], "PRV004": ["PROD002", "PROD008"],
          "PRV005": ["PROD005", "PROD010"], "PRV006": ["PROD003"], "PRV007": ["PROD004", "PROD009"],
          "PRV008": ["PROD002", "PROD008"]}
PAGO = {"PRV001": "30 dias", "PRV002": "60 dias", "PRV003": "contado", "PRV004": "30 dias", "PRV005": "45 dias",
        "PRV006": "30 dias", "PRV007": "45 dias", "PRV008": "30 dias"}
LT = {"PRV001": (6, 2), "PRV002": (9, 2.5), "PRV003": (2, 1), "PRV004": (4, 1.5), "PRV005": (7, 2),
      "PRV006": (8, 2), "PRV007": (6, 1.5), "PRV008": (3, 1)}
ACTIVOS = {m: ["PRV001", "PRV002", "PRV003", "PRV004", "PRV005", "PRV007", "PRV008"] for m in range(1, 11)}
for m in (1, 2, 3):
    ACTIVOS[m] = ACTIVOS[m] + ["PRV006"]          # PRV006 compra hasta marzo y luego queda inactivo
ORDENES_MES = {1: 8, 2: 8, 3: 9, 4: 9, 5: 10, 6: 7, 7: 7, 8: 8, 9: 10, 10: 11}
FACTOR_MES = {1: .9, 2: .95, 3: 1.0, 4: 1.0, 5: 1.05, 6: 1.0, 7: 1.1, 8: 1.05, 9: 1.1, 10: 1.15}

def anexar(nombre, filas):
    p = SD / nombre
    existentes = list(csv.reader(p.open(encoding="utf-8")))
    llaves = {tuple(r) for r in existentes}
    nuevas = [f for f in filas if tuple(f) not in llaves]
    if nuevas:
        with p.open("a", encoding="utf-8", newline="") as fh:
            csv.writer(fh, lineterminator="\n").writerows(nuevas)

def main():
    for n, f in NUEVOS.items():
        anexar(n, f)
    rng = random.Random(2026)
    base = [r for r in csv.reader(BASE.splitlines())]
    filas = []
    for m in range(1, 11):
        for _ in range(ORDENES_MES[m]):
            prv = rng.choice(ACTIVOS[m]); prod = rng.choice(OFERTA[prv])
            cat, uo, precio, qmin, qmax = PROD[prod]
            if prv == "PRV003" and prod in ("PROD001", "PROD007"):
                media, sd = 4, 1.5
            else:
                media, sd = LT[prv]
            lead = max(1, round(rng.gauss(media, sd)))
            p = round(precio * rng.uniform(.96, 1.05) * FACTOR_MES[m] ** .3, 2)
            q = rng.randint(qmin, qmax)
            dia = rng.randint(1, 28)
            filas.append([f"2026-{m:02d}-{dia:02d}", prv, prod, cat, uo, str(q), f"{p:.2f}", "GTQ", PAGO[prv], str(lead)])
    filas.sort(key=lambda r: r[0])
    out = [r for r in base]
    for i, r in enumerate(filas, start=11):
        out.append([f"OC{i:04d}"] + r)
    out.sort(key=lambda r: (r[1], r[0]))
    with (SD / "registro_compras.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["id_compra", "fecha", "proveedor_id", "producto_id", "categoria_id", "unidad_organizacional_id",
                    "cantidad", "precio_unitario", "moneda", "condicion_pago", "lead_time_dias"])
        w.writerows(out)
    print(len(out), "ordenes")

if __name__ == "__main__":
    main()
