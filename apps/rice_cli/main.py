import argparse, yaml, json, sys
from pydantic import BaseModel, Field, ValidationError
from typing import List

class Story(BaseModel):
    id: str
    title: str
    status: str = Field(pattern="^(todo|in_progress|done)$")
    reach: float = Field(ge=0)
    impact: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    effort: float = Field(gt=0)
    start_date: str | None = None
    target_date: str | None = None
    depends_on: List[str] = []

class Epic(BaseModel):
    id: str
    name: str
    description: str | None = None
    stories: List[Story] = []

class Backlog(BaseModel):
    epics: List[Epic]

def rice_score(s: Story) -> float:
    return (s.reach * s.impact * s.confidence) / s.effort

def main():
    parser = argparse.ArgumentParser(description="RICE ranking CLI")
    parser.add_argument("--file", "-f", default="backlog.yaml", help="Path to backlog YAML")
    parser.add_argument("--top", type=int, default=10, help="Top N")
    args = parser.parse_args()

    try:
        with open(args.file, "r") as fp:
            raw = yaml.safe_load(fp) or {}
        bl = Backlog(**raw)
    except FileNotFoundError:
        print("backlog file not found", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

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
    print(json.dumps(ranked[:args.top], indent=2))

if __name__ == "__main__":
    main()
