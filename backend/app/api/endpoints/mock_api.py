import json
import pathlib
from fastapi import APIRouter, HTTPException

router = APIRouter()


def _find_mock_data() -> pathlib.Path:
    """Search for mock_data.json upward from this file (works in both local and Docker)."""
    current = pathlib.Path(__file__).parent
    for _ in range(7):
        candidate = current / "mock_data.json"
        if candidate.exists():
            return candidate
        current = current.parent
    raise FileNotFoundError("mock_data.json not found in any parent directory")


@router.get("/data")
async def get_mock_data():
    try:
        path = _find_mock_data()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse mock_data.json")
