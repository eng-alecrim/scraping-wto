from pydantic import BaseModel


class Consulta(BaseModel):
    COUNTRY: str
    YEAR: str
    IMPORTS: str
    NOMENCLATURE: str
