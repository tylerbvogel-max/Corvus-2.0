"""ARCHIVED: Classic multi-slot request/response schemas.

These Pydantic models were removed in Session 3 when the codebase transitioned
to agent-based orchestration. Preserved here for reference.

To restore:
1. Copy QuerySlotRequest and SlotResult back to app/schemas.py
2. Update QueryRequest to include:
   - modes: list[str] = ["haiku_neuron"]
   - token_budget: int | None = None
   - slots_v2: list[QuerySlotRequest] | None = None
   - chat_style: str | None = None
3. Update QueryResponse to include:
   - slots: list[SlotResult] = []
"""

from pydantic import BaseModel, Field


class QuerySlotRequest(BaseModel):
    """Configuration for a single slot (LLM execution request) in multi-slot mode."""
    mode: str
    token_budget: int = Field(8000, ge=1000, le=32000)
    top_k: int = Field(60, ge=1, le=500)
    max_output_tokens: int | None = Field(None, ge=256, le=8192)
    label: str | None = None


class SlotResult(BaseModel):
    """Result from executing a single slot."""
    mode: str
    model: str
    neurons: bool
    response: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    token_budget: int | None = None
    top_k: int | None = None
    label: str | None = None


class ClassicQueryRequest(BaseModel):
    """ARCHIVED: Full QueryRequest with multi-slot support (Session 3+)."""
    message: str = Field(..., min_length=1, max_length=5000)
    modes: list[str] = ["haiku_neuron"]
    token_budget: int | None = Field(None, ge=1000, le=32000)
    slots_v2: list[QuerySlotRequest] | None = None
    chat_style: str | None = None
    prior_neuron_ids: list[int] | None = None


class ClassicQueryResponse(BaseModel):
    """ARCHIVED: QueryResponse with multi-slot results (Session 3+)."""
    query_id: int
    intent: str | None = None
    departments: list[str] = []
    role_keys: list[str] = []
    keywords: list[str] = []
    neurons_activated: int = 0
    neuron_scores: list[dict] = []
    classify_cost: float = 0
    classify_input_tokens: int = 0
    classify_output_tokens: int = 0
    slots: list[SlotResult] = []
    total_cost: float = 0
