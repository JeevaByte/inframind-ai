# FieldReady

FieldReady is an English-language climate-resilience pilot for corn and soybean growers in the contiguous United States. It uses the Strands Agents SDK to retrieve official National Weather Service (NWS) alerts and forecasts, assess limited heat and drought alert signals, and explain cautious next steps in plain language.

## Run locally

1. Install the backend requirements from `backend/requirements.txt`.
2. Configure AWS credentials and Amazon Bedrock model access using the standard AWS credential chain.
3. Optionally set `FIELDREADY_CONTACT_EMAIL` in `backend/.env`; it is included in the NWS API user-agent.
4. Start the FastAPI backend and Next.js web app using the repository quick-start instructions.
5. Open `/fieldready`, enter field coordinates, crop, and growth stage, then request an update.

The browser sends coordinates to the backend for the request, and the backend sends them to the NWS API. FieldReady does not persist the submitted coordinates or generated update. Network and model providers still receive data needed to answer the request.

## Pilot boundaries and safety

- The supported region is approximately bounded by latitude 24–50 and longitude -125 to -66; the bounds are a simple pilot limit, not a precise U.S. boundary check.
- Supported crops are corn and soybean; supported stages are seedling, vegetative, flowering, and grain fill.
- NWS alerts are displayed separately from the forecast screening signal. A missing alert is not proof that no hazard or drought exists.
- The heat screening uses a simple 90°F forecast signal and does not estimate crop water needs, yield, or crop-specific thresholds.
- Drought status reflects only active NWS alerts. This pilot does not ingest U.S. Drought Monitor data.
- Recommendations direct farmers to official alerts and local Extension services; they are not irrigation prescriptions or emergency instructions.
- If weather data is unavailable, the agent must disclose that limitation rather than infer current conditions.

## Evaluation

The pilot should be evaluated with representative test cases for heat alerts, drought alerts, normal forecasts, missing sources, and flowering-stage requests. Review results with agricultural Extension experts before relying on crop-specific recommendations. Track pilot measures such as:

- Time from request to a sourced update
- Correct distinction between official alerts and forecast signals
- Whether users can identify the source and uncertainty of each signal
- User-reported comprehension and whether they took a suggested follow-up action

These are proposed measurements, not demonstrated impact claims.

## Builder Center article outline

1. Describe the local heat and drought preparedness challenge and the intended underserved community.
2. Explain the FieldReady workflow, NWS data sources, and Strands tool sequence.
3. Show how the interface labels official alerts, forecast screening, source freshness, and uncertainty.
4. Report evaluation methods and any measured results honestly; distinguish planned measures from completed research.
5. Discuss limitations, lessons learned, and next steps such as Extension review and drought-monitor data.

## Demo outline (under three minutes)

1. Enter a sample contiguous-U.S. coordinate, corn or soybean, and a growth stage.
2. Show the NWS alert and forecast checks, then the short agent response and source links.
3. Explain how alert data is distinguished from a forecast screening signal.
4. Show the unavailable-data message or explain the safe fallback.
5. Close with the pilot limits and state that FieldReady is general decision support, not a substitute for official or local advice.

The required Strands workshop, Builder Center project article, public source repository, and public demo video are submission steps to complete separately; this repository does not claim they have been completed.
