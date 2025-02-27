from pydantic import BaseModel, conlist, confloat

class GridCellSchema(BaseModel):
    coordinates: conlist(int, min_length=4, max_length=4)  # <-- Correction ici
    mean_value: confloat(ge=0.0, le=1.0)