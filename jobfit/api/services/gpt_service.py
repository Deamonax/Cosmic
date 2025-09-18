from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List


class DummyGptService:
    """Loads static JSON files to simulate AI responses."""

    def __init__(self, mocks_path: Path | None = None) -> None:
        self._mocks_path = mocks_path or Path(__file__).resolve().parent.parent / "mocks"
        self._cache: Dict[str, Any] = {}

    def _load_mock(self, filename: str) -> Any:
        if filename not in self._cache:
            path = self._mocks_path / filename
            with path.open("r", encoding="utf-8") as file:
                self._cache[filename] = json.load(file)
        return deepcopy(self._cache[filename])

    def analyze_job_description(self, jd_text: str) -> Any:
        _ = jd_text  # input ignored for now
        return self._load_mock("jd_analysis.json")

    def assess_candidate_fit(self, jd_json: Dict[str, Any], candidate_chunks: List[Dict[str, Any]]) -> Any:
        _ = (jd_json, candidate_chunks)
        return self._load_mock("fit_assessment.json")

    def rewrite_cv(self, project_id: str, mode: str) -> Any:
        data = self._load_mock("cv_rewrite.json")
        data["project_id"] = project_id
        data["mode"] = mode
        return data

    def generate_qa(self, jd_json: Dict[str, Any], candidate_chunks: List[Dict[str, Any]]) -> Any:
        _ = (jd_json, candidate_chunks)
        return self._load_mock("qa.json")
