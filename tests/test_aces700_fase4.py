"""
Compliance tests untuk ACES-700 Fase 4:
ACTS-700-004, 009, dan integrasi AI event ke DB Digital Twin
"""
import pytest
from fastra_core.ai import DrawingResult, DetectedElement, PredictionResult, Prediction
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.ai.audit import AIEventLog
from fastra_core.ai.enums import AIComponent


def test_drawing_ccm_proposal_valid():
    generated_ccm = {
        "entities": [
            {"id": "wall-001", "type": "Wall", "length": 5.0},
        ],
        "relationships": [],
    }
    drawing = DrawingResult(
        model_version="fastra-drawing-v1.0.0",
        input_files=["denah.pdf"],
        detected_elements={
            "walls": [DetectedElement(proposed_uuid="temp-wall-001", type="Wall", confidence=0.95)],
        },
        detected_dimensions={"building_area": 120.0},
        generated_ccm=generated_ccm,
    )
    assert "entities" in drawing.generated_ccm or "relationships" in drawing.generated_ccm


def test_prediction_does_not_touch_knowledge_graph():
    pred = Prediction(
        type="PRICE_FORECAST",
        data={"material": "Besi Beton D10"},
        confidence_interval=[122000, 135000],
    )
    result = PredictionResult(
        model_version="fastra-predict-v1.0.0",
        predictions=[pred],
    )
    assert not hasattr(result, "update_knowledge_graph")
    assert not hasattr(result, "modify_price")
    assert not hasattr(result, "apply_recommendation")


def test_save_ai_event_to_db():
    db = ExtendedDigitalTwinDB("sqlite:///:memory:")
    event = AIEventLog(
        ai_component=AIComponent.VISION_AI,
        model_name="fastra-vision",
        model_version="1.2.0",
        input_hash="abc",
        output_hash="def",
        confidence_scores={"building_type": 0.92},
    )
    db.save_ai_event(event)
    db.close()
