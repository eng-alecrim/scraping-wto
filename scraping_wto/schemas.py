# =============================================================================
# BIBLIOTECAS E MÓDULOS
# =============================================================================

from pydantic import BaseModel

# =============================================================================
# CLASSES E SCHEMAS
# =============================================================================


class Consulta(BaseModel):
    COUNTRY: str
    YEAR: str
    IMPORTS: str
    NOMENCLATURE: str


class TipoRelatorio(BaseModel):
    nome: str
    regex: str
