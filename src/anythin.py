
import sys,os 

# Absolute path to the folder where *this* file (app.py) lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# BASE_DIR == "C:\\Users\\user\\Desktop\\Workshop2\\AutoRBI\\src"

# Path to the AutoRBI_Database folder
DB_ROOT = os.path.join(BASE_DIR, "AutoRBI_Database")
# DB_ROOT == "C:\\Users\\user\\Desktop\\Workshop2\\AutoRBI\\src\\AutoRBI_Database"

# Add it to sys.path if it's not already there
if DB_ROOT not in sys.path:
    sys.path.append(DB_ROOT)
    
    
from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.database.crud.material_crud import create_material

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
