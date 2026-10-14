from typing import Optional, List
from pydantic import BaseModel, Field

class CrowdRuleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Detailed explanation of the rule condition")
    rule_type: str = Field("threshold", description="'threshold' or 'sustained'")
    operator: str = Field(">=", description="Comparison operator ('>=' or '>')")
    threshold_count: int = Field(..., ge=1, le=10000, description="Person detection count threshold per frame")
    sustained_seconds: float = Field(0.0, ge=0.0, le=3600.0, description="Minimum duration across qualifying frames in seconds")
    min_consecutive_frames: int = Field(1, ge=1, le=1000, description="Minimum consecutive qualifying sampled frames")
    zone_id: Optional[str] = Field(None, description="Monitored venue zone identifier (null for all zones)")
    severity: str = Field("medium", description="Alert severity: 'low', 'medium', 'high', 'critical'")
    cooldown_seconds: float = Field(10.0, ge=0.0, le=3600.0, description="Cooldown suppression window in seconds")
    is_active: bool = Field(True, description="Whether this rule is actively evaluated")

class CrowdRuleCreate(CrowdRuleBase):
    id: Optional[str] = Field(None, description="Optional custom rule identifier (e.g., 'RULE-SURGE-CUSTOM')")

class CrowdRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    threshold_count: Optional[int] = Field(None, ge=1, le=10000)
    sustained_seconds: Optional[float] = Field(None, ge=0.0, le=3600.0)
    min_consecutive_frames: Optional[int] = Field(None, ge=1, le=1000)
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    cooldown_seconds: Optional[float] = Field(None, ge=0.0, le=3600.0)

class CrowdRuleResponse(CrowdRuleBase):
    id: str
    created_by: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

class RuleListResponse(BaseModel):
    rules: List[CrowdRuleResponse]
    total: int
