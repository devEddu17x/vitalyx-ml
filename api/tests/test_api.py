"""End-to-end tests for the public Vitalyx API contract."""

from __future__ import annotations


FRIENDLY_PAYLOAD = {
    "age": 32,
    "sex": "F",
    "answers": [
        {"evidence_id": "E_91", "present": True},
        {"evidence_id": "E_59", "value": "3"},
        {"evidence_id": "E_55", "values": ["V_89", "V_108"]},
    ],
    "top_k": 5,
}

RAW_PAYLOAD = {
    "age": 32,
    "sex": "F",
    "evidences": ["E_91", "E_59_@_3", "E_55_@_V_89", "E_55_@_V_108"],
    "top_k": 5,
}


def test_health_and_readiness(client):
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["feature_count"] == 975
    assert response.json()["class_count"] == 49


def test_catalogs_and_filters(client):
    catalog = client.get("/api/v1/evidences", params={"type": "boolean", "search": "fever"})
    assert catalog.status_code == 200
    assert any(item["id"] == "E_91" for item in catalog.json()["items"])
    pathologies = client.get("/api/v1/pathologies").json()
    assert pathologies["total"] == 49
    assert len(pathologies["items"]) == 49


def test_friendly_and_raw_predictions_are_equivalent(client):
    friendly = client.post("/api/v1/predictions", json=FRIENDLY_PAYLOAD)
    raw = client.post("/api/v1/predictions/raw", json=RAW_PAYLOAD)
    assert friendly.status_code == raw.status_code == 200
    friendly_body, raw_body = friendly.json(), raw.json()
    assert friendly_body["predictions"] == raw_body["predictions"]
    assert len(friendly_body["predictions"]) == 5
    assert friendly_body["predictions"] == sorted(friendly_body["predictions"], key=lambda item: item["rank"])
    assert isinstance(friendly_body["confidence"]["low_confidence"], bool)


def test_prediction_uses_49_class_probability_vector_internally(client):
    response = client.post("/api/v1/predictions/raw", json=RAW_PAYLOAD)
    assert response.status_code == 200
    bundle = client.app.state.bundle
    service = client.app.state.prediction_service
    matrix = service.preprocessor.transform(RAW_PAYLOAD["age"], RAW_PAYLOAD["sex"], RAW_PAYLOAD["evidences"])
    probabilities = bundle.model(matrix.toarray(), training=False).numpy()[0]
    assert matrix.shape == (1, 975)
    assert probabilities.shape == (49,)
    assert abs(float(probabilities.sum()) - 1.0) < 1e-5


def test_invalid_inputs_return_422(client):
    invalid_cases = [
        ("/api/v1/predictions", {**FRIENDLY_PAYLOAD, "age": 110}),
        ("/api/v1/predictions", {**FRIENDLY_PAYLOAD, "sex": "X"}),
        ("/api/v1/predictions", {**FRIENDLY_PAYLOAD, "top_k": 50}),
        ("/api/v1/predictions", {**FRIENDLY_PAYLOAD, "answers": [{"evidence_id": "E_UNKNOWN", "present": True}]}),
        ("/api/v1/predictions", {**FRIENDLY_PAYLOAD, "answers": [{"evidence_id": "E_59", "value": "invalid"}]}),
        ("/api/v1/predictions/raw", {**RAW_PAYLOAD, "evidences": ["E_59_@_invalid"]}),
    ]
    for endpoint, payload in invalid_cases:
        assert client.post(endpoint, json=payload).status_code == 422


def test_e2e_flow(client):
    assert client.get("/ready").status_code == 200
    evidence_response = client.get("/api/v1/evidences", params={"type": "single_choice"})
    assert evidence_response.status_code == 200 and evidence_response.json()["total"] > 0
    prediction = client.post("/api/v1/predictions", json=FRIENDLY_PAYLOAD)
    assert prediction.status_code == 200
    body = prediction.json()
    assert body["model"]["name"] == "Vitalyx final E01"
    assert "synthetic" in body["disclaimer"].lower()
