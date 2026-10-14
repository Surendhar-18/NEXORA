from typing import Dict, Any
from pydantic import BaseModel, Field

class StorageHealth(BaseModel):
    data_dir_writable: bool = Field(..., description="Data directory write status")
    uploads_dir_exists: bool = Field(..., description="Uploads directory status")
    evidence_dir_exists: bool = Field(..., description="Evidence directory status")

class ModuleHealth(BaseModel):
    database: str = Field(..., description="Database connection status")
    gis_routing: str = Field(..., description="GIS NetworkX engine availability")
    visionx_cv: str = Field(..., description="Computer vision engine availability")

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    app_name: str = Field(..., json_schema_extra={"example": "NEXORA Intelligence Platform"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    environment: str = Field(..., json_schema_extra={"example": "development"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-10-09T18:30:00Z"})
    database: str = Field(..., json_schema_extra={"example": "connected"})
    storage: StorageHealth
    modules: ModuleHealth
