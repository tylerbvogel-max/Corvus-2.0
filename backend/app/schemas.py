"""Pydantic request/response DTOs."""

from pydantic import BaseModel, Field


class QuerySlotRequest(BaseModel):
    mode: str
    token_budget: int = Field(8000, ge=1000, le=32000)
    top_k: int = Field(60, ge=1, le=500)
    max_output_tokens: int | None = Field(None, ge=256, le=8192)
    label: str | None = None


class QuerySlotRequest(BaseModel):
    mode: str = Field(..., min_length=1)  # e.g. "haiku_neuron", "sonnet_raw", "opus_neuron"
    token_budget: int = Field(8000, ge=1000, le=32000)
    top_k: int = Field(60, ge=1, le=500)
    agent_mode: bool = True  # Per-slot control: agent orchestration or direct call
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)
    label: str | None = None


class QueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    slots: list[QuerySlotRequest] | None = None  # Multi-slot testing; if None, use default single slot
    prior_neuron_ids: list[int] | None = None


class SlotResult(BaseModel):
    mode: str
    model: str
    neurons: bool
    response: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    token_budget: int | None = None
    top_k: int | None = None
    label: str | None = None
    agent_mode: bool = False  # Whether this slot used agent orchestration


class NeuronScoreResponse(BaseModel):
    neuron_id: int
    combined: float
    burst: float
    impact: float
    precision: float
    novelty: float
    recency: float
    relevance: float
    spread_boost: float = 0
    label: str | None = None
    department: str | None = None
    layer: int = 0
    parent_id: int | None = None
    summary: str | None = None


class InputGuardOut(BaseModel):
    verdict: str = "pass"  # "pass" | "warn" | "block"
    flags: list[dict] = []
    flag_count: int = 0


class GroundingOut(BaseModel):
    grounded: bool | None = None
    confidence: float | None = None
    overlap_terms: int | None = None
    response_terms: int | None = None
    ungrounded_references: list[str] = []
    reason: str = ""


class OutputCheckOut(BaseModel):
    mode: str | None = None
    risk_flags: list[dict] = []
    grounding: GroundingOut | None = None


class AgentResultOut(BaseModel):
    """Result from a single domain agent."""
    domain_key: str
    department: str
    role_key: str
    role: str
    findings: str
    citations: list[str] = []
    confidence: float
    flags: list[str] = []
    neuron_ids: list[int] = []
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0
    duration_ms: int = 0
    error: bool = False
    error_message: str = ""


class VerificationResultOut(BaseModel):
    """Result from verification agent critique."""
    critique: str
    gaps: list[str] = []
    confidence_adjustment: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0
    error: bool = False
    error_message: str = ""


class AgentExecutionOut(BaseModel):
    """Result from full agent dispatch and coordination."""
    agent_results: list[AgentResultOut] = []
    synthesis: str
    coordinator_model: str
    escalated_to_opus: bool = False
    domains_active: list[str] = []
    coordinator_input_tokens: int = 0
    coordinator_output_tokens: int = 0
    coordinator_cost_usd: float = 0
    total_agents_dispatched: int = 0
    total_cost_usd: float = 0
    verification_result: VerificationResultOut | None = None


class QueryResponse(BaseModel):
    query_id: int
    intent: str | None = None
    departments: list[str] = []
    role_keys: list[str] = []
    keywords: list[str] = []
    neurons_activated: int = 0
    neuron_scores: list[NeuronScoreResponse] = []
    classify_cost: float = 0
    classify_input_tokens: int = 0
    classify_output_tokens: int = 0
    slots: list[SlotResult] = []
    total_cost: float = 0
    input_guard: InputGuardOut | None = None
    output_checks: list[OutputCheckOut] = []
    agent_execution: AgentExecutionOut | None = None


class EvalRequest(BaseModel):
    model: str = Field("sonnet", min_length=1)


class EvalScoreOut(BaseModel):
    answer_label: str
    answer_mode: str
    accuracy: int
    completeness: int
    clarity: int
    faithfulness: int
    overall: int


class SynapticLearningOut(BaseModel):
    outcome: str
    winner_mode: str | None = None
    neurons_adjusted: int = 0
    edges_adjusted: int = 0
    avg_delta: float = 0.0
    total_reward: float = 0.0
    total_penalty: float = 0.0


class EvalResponse(BaseModel):
    query_id: int
    eval_text: str
    eval_model: str
    eval_input_tokens: int
    eval_output_tokens: int
    scores: list[EvalScoreOut] = []
    winner: str | None = None
    learning: SynapticLearningOut | None = None


class LearningEventOut(BaseModel):
    id: int
    query_id: int
    neuron_id: int
    neuron_label: str | None = None
    event_type: str
    old_avg_utility: float
    new_avg_utility: float
    effective_delta: float
    combined_score: float
    attribution_weight: float
    outcome: str
    winner_mode: str | None = None
    created_at: str | None = None


class LearningAnalytics(BaseModel):
    total_events: int
    total_wins: int
    total_losses: int
    avg_reward: float
    avg_penalty: float
    recent_events: list[LearningEventOut] = []


class EvalScoreSummary(BaseModel):
    id: int
    query_id: int
    eval_model: str
    answer_mode: str
    answer_label: str
    accuracy: int
    completeness: int
    clarity: int
    faithfulness: int
    overall: int
    created_at: str | None


class RatingRequest(BaseModel):
    utility: float = Field(..., ge=0.0, le=1.0)


class RatingResponse(BaseModel):
    query_id: int
    utility: float
    neurons_updated: int


class NeuronDetail(BaseModel):
    id: int
    parent_id: int | None
    layer: int
    node_type: str
    label: str
    content: str | None
    summary: str | None
    department: str | None
    role_key: str | None
    invocations: int
    avg_utility: float
    is_active: bool
    cross_ref_departments: list[str] | None = None
    standard_date: str | None = None


class NeuronScoreDetail(BaseModel):
    neuron_id: int
    burst: float
    impact: float
    precision: float
    novelty: float
    recency: float
    relevance: float
    combined: float


class SeedResponse(BaseModel):
    status: str
    neuron_count: int


class ResetResponse(BaseModel):
    status: str


class CostReportResponse(BaseModel):
    total_queries: int
    total_cost_usd: float
    avg_cost_per_query: float
    total_input_tokens: int
    total_output_tokens: int


class QuerySummary(BaseModel):
    id: int
    user_message: str
    classified_intent: str | None
    modes: list[str] = []
    cost_usd: float | None
    user_rating: float | None
    created_at: str | None


class NeuronHit(BaseModel):
    neuron_id: int
    label: str
    layer: int
    department: str | None
    parent_id: int | None = None
    summary: str | None = None
    combined: float
    burst: float
    impact: float
    precision: float
    novelty: float
    recency: float
    relevance: float
    spread_boost: float = 0


class RefinementOut(BaseModel):
    id: int
    neuron_id: int
    action: str  # "update" | "create"
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    reason: str | None = None
    neuron_label: str | None = None


class QueryDetail(BaseModel):
    id: int
    user_message: str
    classified_intent: str | None
    departments: list[str]
    role_keys: list[str]
    keywords: list[str]
    assembled_prompt: str | None
    classify_input_tokens: int
    classify_output_tokens: int
    classify_cost: float = 0
    slots: list[SlotResult] = []
    total_cost: float = 0
    user_rating: float | None
    eval_text: str | None = None
    eval_model: str | None = None
    eval_input_tokens: int = 0
    eval_output_tokens: int = 0
    eval_scores: list[EvalScoreOut] = []
    eval_winner: str | None = None
    neuron_hits: list[NeuronHit]
    refinements: list[RefinementOut] = []
    pending_refine: "RefineResponse | None" = None
    created_at: str | None


class RefineRequest(BaseModel):
    model: str = Field("opus", min_length=1)
    max_tokens: int = Field(4096, ge=512, le=16384)
    user_context: str | None = Field(None, max_length=16000)


class NeuronUpdateSuggestion(BaseModel):
    neuron_id: int
    field: str  # content, summary, label, is_active
    old_value: str
    new_value: str
    reason: str


class NewNeuronSuggestion(BaseModel):
    parent_id: int | None = None
    layer: int
    node_type: str
    label: str
    content: str
    summary: str
    department: str | None = None
    role_key: str | None = None
    reason: str


class RefineResponse(BaseModel):
    query_id: int
    model: str
    input_tokens: int
    output_tokens: int
    reasoning: str
    neuron_vs_raw_verdict: str = ""
    updates: list[NeuronUpdateSuggestion] = []
    new_neurons: list[NewNeuronSuggestion] = []


# Resolve forward reference now that RefineResponse is defined
QueryDetail.model_rebuild()


class ApplyRefineRequest(BaseModel):
    update_ids: list[int] = []
    new_neuron_ids: list[int] = []


class ApplyRefineResponse(BaseModel):
    updated: int
    created: int


class NeuronRefinementOut(BaseModel):
    id: int
    query_id: int | None = None
    neuron_id: int
    action: str
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    reason: str | None = None
    created_at: str | None = None
    neuron_label: str | None = None
    query_snippet: str | None = None


class CheckpointResponse(BaseModel):
    status: str
    filename: str
    neuron_count: int
    commit_sha: str


class HealthResponse(BaseModel):
    status: str
    neuron_count: int
    total_queries: int


class AutopilotConfigOut(BaseModel):
    enabled: bool
    directive: str
    interval_minutes: int
    focus_neuron_id: int | None = None
    focus_neuron_label: str | None = None
    max_layer: int = 5
    eval_model: str = "haiku"
    last_tick_at: str | None = None


class AutopilotConfigUpdate(BaseModel):
    enabled: bool | None = None
    directive: str | None = None
    interval_minutes: int | None = None
    focus_neuron_id: int | None = Field(None, description="Neuron ID to focus on (L0-L5). Set to 0 to clear.")
    max_layer: int | None = Field(None, ge=0, le=5, description="Max layer depth for new neuron creation (0-5)")
    eval_model: str | None = Field(None, min_length=1)


class AutopilotRunOut(BaseModel):
    id: int
    query_id: int | None = None
    generated_query: str
    directive: str
    focus_neuron_label: str | None = None
    gap_source: str | None = None
    gap_target: str | None = None
    neurons_activated: int
    updates_applied: int
    neurons_created: int
    eval_overall: int
    eval_text: str | None = None
    refine_reasoning: str | None = None
    cost_usd: float
    status: str
    error_message: str | None = None
    created_at: str | None = None


class AutopilotTickResponse(BaseModel):
    status: str
    run_id: int | None = None
    message: str | None = None


class ObservationEvalRequest(BaseModel):
    model: str = Field("haiku", min_length=1)


class ObservationBatchEvalRequest(BaseModel):
    observation_ids: list[int] = Field(..., max_length=20)
    model: str = Field("haiku", min_length=1)


class ObservationApplyRequest(BaseModel):
    update_indices: list[int] = []
    new_neuron_indices: list[int] = []
