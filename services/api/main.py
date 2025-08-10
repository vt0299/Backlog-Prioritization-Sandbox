from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Optional
import yaml, os
from datetime import datetime

BACKLOG_PATH = os.getenv("BACKLOG_PATH", "backlog.yaml")

app = FastAPI(title="Backlog API", version="1.0.0")

class Story(BaseModel):
    id: str
    title: str
    status: str = Field(pattern="^(todo|in_progress|done)$")
    reach: float = Field(ge=0)
    impact: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    effort: float = Field(gt=0)
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    depends_on: List[str] = []

class Epic(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    stories: List[Story] = []

class Backlog(BaseModel):
    epics: List[Epic]

def load_backlog() -> Backlog:
    try:
        with open(BACKLOG_PATH, "r") as f:
            raw = yaml.safe_load(f) or {}
        return Backlog(**raw)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="backlog.yaml not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

def rice_score(story: Story) -> float:
    return (story.reach * story.impact * story.confidence) / story.effort

@app.get("/backlog")
def get_backlog():
    return load_backlog().model_dump()

@app.get("/ranked")
def get_ranked():
    bl = load_backlog()
    ranked = []
    for epic in bl.epics:
        for s in epic.stories:
            ranked.append({
                "epic_id": epic.id,
                "epic_name": epic.name,
                **s.model_dump(),
                "rice_score": rice_score(s)
            })
    ranked.sort(key=lambda x: x["rice_score"], reverse=True)
    return ranked

@app.get("/metrics/summary")
def get_metrics_summary():
    bl = load_backlog()
    total = 0
    status_counts = {"todo":0, "in_progress":0, "done":0}
    avg_rice = []
    epic_scores: Dict[str, float] = {}
    for epic in bl.epics:
        for s in epic.stories:
            total += 1
            status_counts[s.status] += 1
            rs = rice_score(s)
            avg_rice.append(rs)
            epic_scores[epic.name] = epic_scores.get(epic.name, 0.0) + rs
    avg_r = sum(avg_rice)/len(avg_rice) if avg_rice else 0.0
    return {
        "story_count": total,
        "status_counts": status_counts,
        "avg_rice": avg_r,
        "epic_scores": epic_scores
    }

@app.get("/roadmap")
def get_roadmap():
    bl = load_backlog()
    rows = []
    for epic in bl.epics:
        for s in epic.stories:
            if s.start_date and s.target_date:
                rows.append({
                    "id": s.id,
                    "task": s.title,
                    "epic": epic.name,
                    "status": s.status,
                    "start": s.start_date.isoformat(),
                    "finish": s.target_date.isoformat(),
                    "depends_on": s.depends_on
                })
    return rows

class GitHubExportRequest(BaseModel):
    owner: str
    repo: str
    token: str

@app.post("/export/github")
def export_github(req: GitHubExportRequest):
    return {"status": "not_implemented", "hint": "Wire GitHub API here."}
