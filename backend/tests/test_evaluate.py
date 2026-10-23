"""backend/evaluate.py: full-context baseline and per-mode result files."""
from __future__ import annotations

import shutil
from pathlib import Path

from backend import assistant, data, evaluate
from backend.models import ChatMessage

from .conftest import REPO_DATA


def test_full_context_holds_every_row_and_paragraph(data_dir: Path) -> None:
    shutil.copy(REPO_DATA / "regulations" / "safety_rules_example.md", data_dir / "regulations")
    log = data.load_events()
    question = "โซนไหนมีการละเมิดมากที่สุด?"
    full, full_src = evaluate.full_context_messages(question, log.df, log.source)
    selected, sel_src = assistant.build_messages([ChatMessage(role="user", content=question)], log.df, log.source)

    system = full[0]["content"]
    assert full[-1] == {"role": "user", "content": question}
    assert all(eid in system for eid in log.df["event_id"])
    paras = evaluate.retrieval.all_paragraphs()
    assert full_src["regulation_paragraphs"] == len(paras) > 5
    assert all(p.title in system for p in paras)
    assert full_src["token_estimate"] > sel_src["token_estimate"]


def test_each_mode_writes_its_own_file(data_dir: Path) -> None:
    assert evaluate.results_path(True, False) == data_dir / "eval_results_mock.csv"
    assert evaluate.results_path(True, True) == data_dir / "eval_results_mock.csv"
    assert evaluate.results_path(False, False) == data_dir / "eval_results_selected.csv"
    assert evaluate.results_path(False, True) == data_dir / "eval_results_full.csv"


def test_real_mode_without_api_key_refuses_instead_of_mocking(data_dir: Path) -> None:
    assert evaluate.main(["--n", "1"]) == 1
    assert not list(data_dir.glob("eval_results*.csv"))


def test_mock_full_context_run_end_to_end(data_dir: Path) -> None:
    assert evaluate.main(["--mock", "--full-context", "--n", "3"]) == 0
    assert (data_dir / "eval_results_mock.csv").is_file()
