import yaml
from services.api.main import rice_score, Story

def test_rice_computation():
    s = Story(id="S1", title="T", status="todo", reach=100, impact=3, confidence=0.8, effort=5)
    assert abs(rice_score(s) - 48.0) < 1e-6

def test_backlog_example_parses():
    with open("backlog.yaml", "r") as f:
        raw = yaml.safe_load(f)
    assert "epics" in raw
