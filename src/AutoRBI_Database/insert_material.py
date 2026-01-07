from AutoRBI_Database.session import SessionLocal
from AutoRBI_Database.crud.material_crud import create_material

db = SessionLocal()

materials = [
    ("SA-240", "Stainless Steel"),
    ("SA-312", "Stainless Steel"),
    ("SA-213", "Stainless Steel"),
    ("SA-516", "Carbon Steel"),
    ("SA-283", "Carbon Steel"),
    ("SA-403", "Stainless Steel"),
    ("A-240", "Stainless Steel"),
]

for spec, type_ in materials:
    create_material(db, spec, type_)

print("Material table successfully populated.")
db.close()
