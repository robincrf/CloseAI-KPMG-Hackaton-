
# Granular Market Estimation Architecture

## Core Philosophy
"Granularity > Source Unique".
We do not want a single magic number. We want a constructed number.
If data is missing, we decompose it further until we find data or a proxy.

## Data Structures

### 1. The Fact (Enhanced)
Existing `FactsManager` needs to support:
- `type`: "hard_data", "proxy", "assumption", "computed"
- `related_facts`: list of IDs (if computed from others)
- `formula`: string (if computed)

### 2. Estimation Strategy
An abstract definition of HOW to calculate a market view.

```python
@dataclass
class EstimationStrategy:
    id: str
    name: str # e.g. "Bottom-up by User Base"
    formula_template: str # "{users} * {arpu}"
    required_inputs: Dict[str, str] # {"users": "total_active_users", "arpu": "avg_revenue_per_user"}
    fallback_proxies: Dict[str, List[str]] # {"arpu": ["competitor_arpu", "us_market_arpu"]}
    description: str
```

### 3. The Solver
The engine will not just "get_demand_estimation". It will:
1. Load all available strategies for "Demand".
2. For each strategy:
    - Check if primary inputs exist.
    - If missing, check if proxies exist.
    - If missing, check if we can sub-estimate (recursion).
    - Calculate Result + Confidence Score.
3. Select the best Strategy (highest confidence * coverage).

## Standard Strategies to Implement

### Top-Down (Macro)
1. **Global Share**: `TAM_Global * Segment_Share`
2. **GDP Proxy**: `GDP_Target_Country * Sector_GDP_Share`

### Bottom-Up (Demand)
1. **User Volume**: `Num_Users * Annual_Price`
2. **Consumption**: `Num_Companies * Avg_contract_value`
3. **Niche Penetration**: `Target_Population * Penetration_Rate * Price`

### Supply (Production)
1. **Production Value**: `Volume_Produced * Unit_Price`
2. **Competitor Sum**: `Sum(Competitor_Revenues) / Market_Share_Assumption`

## UX Implication
The UI must show:
- The **Selected Strategy** (e.g. "We used 'Niche Penetration' because hard user data was missing").
- The **Equation**: Visually `[Pop (10k)] x [Penetration (5%)] x [Price (€100)] = €50k`.
- The **Justification**: "Penetration rate inferred from similar market X".
