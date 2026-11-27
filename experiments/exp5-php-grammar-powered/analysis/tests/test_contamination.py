"""Tests for contamination.py: the three hit categories of protocol.md Exclusions on exported transcripts."""

import json
import sys
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
FIXTURES = ANALYSIS / "tests" / "fixtures"
TRANSCRIPTS = FIXTURES / "transcripts"
PILOT = ANALYSIS.parent / "scorer" / "pilot-evidence" / "fenced-repilot"
sys.path.insert(0, str(ANALYSIS))
import contamination as mod  # noqa: E402

# scorer/HEADROOM-pilot.md, "h4-5 control re-check": the 2026-11-27 h45-control-r3 leak
LEAK_URL_RESULT = "Web results\n1. https://github.com/clouatre-labs/aptu-coder/issues/1861\n[FEATURE] Add PHP language support via tree-sitter-php grammar #1861"
LEAK_BODY_RESULT = ("Relevant docs\nfn main() -> Result<()> { let language: tree_sitter_php::PtrLanguage = tree_sitter_php::language(); "
                    "data GrammarSource; Statically-known rules corresponding to symbols in the grammar }")
ISSUE_BODY_RESULT = ("EXIT 0\n## Scope\n- A new handler, `crates/aptu-coder-core/src/languages/php.rs`, with the SPDX header\n"
                     "- [ ] `crates/aptu-coder-core/src/languages/php.rs` exists")
PHP_OUTPUT = {"wiring_summary": {"php_rs_language_module": "Create crates/aptu-coder-core/src/languages/php.rs with ELEMENT_QUERY",
                                 "workspace_dependency": "Add tree-sitter-php = \"0.x.x\" to [workspace.dependencies]"}}


def _message(role, *items):
    return {"id": f"m-{role}-{len(items)}", "role": role, "content": list(items)}


def _request(name, arguments, req_id="r1"):
    return {"type": "toolRequest", "id": req_id, "toolCall": {"status": "success", "value": {"name": name, "arguments": arguments}}}


def _response(req_id, text, stdout=None):
    value = {"resultType": "complete", "content": [{"type": "text", "text": text}], "structuredContent": {"stdout": stdout or text, "stderr": "", "exit_code": 0}, "isError": False}
    return {"type": "toolResponse", "id": req_id, "toolResult": {"status": "success", "value": value}}


def _transcript(run_id, *conversation):
    return {"id": "20261127_00", "name": f"exp5-{run_id}", "conversation": [
        _message("user", {"type": "text", "text": "TASK: clouatre-labs/aptu-coder#1864 -- add PHP language support via tree-sitter-php. Issue 1861 is off limits."}),
        *conversation]}


def _hits(transcript, tool_log=()):
    return [(h["category"], h["source"], h["message_index"]) for h in mod.scan(transcript, list(tool_log))]


# ---------------------------------------------------------------- the fenced re-pilot

@pytest.mark.parametrize("run_id, session", [("h45-control", "20261127_91"), ("h45-treatment", "20261127_90"),
                                             ("h55-control", "20261127_92"), ("h55-treatment", "20261127_93")])
def test_fenced_repilot_runs_have_zero_hits(run_id, session):
    transcript = mod.load_transcript(TRANSCRIPTS / f"{run_id}.json")
    tool_log = [json.loads(line) for line in (PILOT / "tool-log.jsonl").read_text().splitlines() if line.strip()]

    assert transcript["id"] == session and transcript["name"] == f"exp5-{run_id}"
    assert mod.scan(transcript, tool_log) == []  # scorer/HEADROOM-pilot.md, Contamination scan (narrowed rule): 0 hits in all four


# ---------------------------------------------------------------- category 1

def test_leak_in_a_web_search_result_is_a_category_1_hit():
    """The 2026-11-27 h45-control-r3 leak: brave_llm_context returned the #1861 URL and title, then a body snippet."""
    transcript = _transcript("h45-control-r3",
                             _message("assistant", _request("brave_search__brave_llm_context", {"query": "tree-sitter-php crate version crates.io"}, "a"),
                                      _request("brave_search__brave_llm_context", {"query": "tree-sitter-php interface_declaration grammar node types"}, "b")),
                             _message("user", _response("a", LEAK_URL_RESULT), _response("b", LEAK_BODY_RESULT)))
    hits = mod.scan(transcript, [])

    assert _hits(transcript) == [("issue_1861", "tool_result", 2)]
    assert [h["match"] for h in hits] == ["1861"] and hits[0]["run_id"] == "h45-control-r3" and hits[0]["number"] == 1


def test_1861_in_a_tool_request_is_a_category_1_hit():
    transcript = _transcript("r", _message("assistant", _request("shell", {"command": "gh issue view 1861 --repo clouatre-labs/aptu-coder"})))
    transcript["conversation"].append(_message("assistant", {"type": "text", "text": "I did not open #1861."}))  # prose is never scanned

    assert _hits(transcript) == [("issue_1861", "tool_request", 1)]


def test_gh_issue_view_1864_is_not_a_hit():
    transcript = _transcript("r",
                             _message("assistant", _request("shell", {"command": "gh issue view 1864 --repo clouatre-labs/aptu-coder"}, "i")),
                             _message("user", _response("i", ISSUE_BODY_RESULT)))
    assert mod.scan(transcript, []) == []


# ---------------------------------------------------------------- category 2

def test_aptu_coder_pull_request_url_and_api_path_are_category_2_hits():
    conversation = [_message("assistant", _request("shell", {"command": "gh api repos/clouatre-labs/aptu-coder/pulls/1742"}, "p")),
                    _message("user", _response("p", "See https://github.com/clouatre-labs/aptu-coder/pull/1742 for the Swift handler"))]
    hits = mod.scan(_transcript("r", *conversation), [])

    assert [(h["category"], h["source"], h["message_index"], h["match"]) for h in hits] == [
        ("aptu_coder_pull_request", "tool_request", 1, "repos/clouatre-labs/aptu-coder/pulls"),
        ("aptu_coder_pull_request", "tool_result", 2, "github.com/clouatre-labs/aptu-coder/pull/1742")]
    assert all(h["number"] == 2 and h["run_id"] == "r" for h in hits)


def test_other_repositories_and_plain_pull_request_prose_are_not_category_2_hits():
    body = "External pull requests are not being accepted. https://github.com/tree-sitter/tree-sitter-php/pull/12 and repos/tree-sitter/tree-sitter-php/pulls"
    transcript = _transcript("r", _message("user", _response("x", body)))
    assert mod.scan(transcript, []) == []


# ---------------------------------------------------------------- category 3

@pytest.mark.parametrize("command, match", [
    ("curl -s https://api.github.com/repos/clouatre-labs/aptu-coder/issues/1861", "curl"),
    ("wget -qO- https://raw.githubusercontent.com/clouatre-labs/aptu-coder/main/README.md", "wget"),
    ("git fetch origin", "git fetch"),
    ("git pull", "git pull"),
    ("cargo fetch", "cargo fetch"),
    ("node -e \"await fetch('https://example.org')\"", "fetch("),
])
def test_network_tokens_in_a_tool_request_are_category_3_hits(command, match):
    hits = mod.scan(_transcript("r", _message("assistant", _request("shell", {"command": command}))), [])

    assert [(h["category"], h["source"], h["message_index"], h["match"]) for h in hits if h["category"] == "network_outside_fence"] == [("network_outside_fence", "tool_request", 1, match)]
    assert mod.NETWORK_TOKENS == ("curl", "wget", "git fetch", "git pull", "cargo fetch", "fetch(")


def test_languages_php_text_anywhere_is_not_a_hit():
    """The rule looks only at what a run requested: issue body, own output file (written or read back) and
    documentation results are not hits by construction."""
    own = json.dumps(PHP_OUTPUT)
    transcript = _transcript("r",
                             _message("assistant", _request("shell", {"command": "gh issue view 1864 --repo clouatre-labs/aptu-coder"}, "i")),
                             _message("user", _response("i", ISSUE_BODY_RESULT)),
                             _message("assistant", _request("write", {"path": "exp5-output.json", "content": own}, "w")),
                             _message("user", _response("w", "wrote 40 lines")),
                             _message("assistant", _request("shell", {"command": "wc -l exp5-output.json && head -20 exp5-output.json"}, "rb")),
                             _message("user", _response("rb", own, stdout=own)),
                             _message("assistant", _request("context7__query-docs", {"libraryId": "/websites/rs_tree-sitter-php", "query": "cargo dependency"}, "d")),
                             _message("user", _response("d", "[dependencies]\ntree-sitter-php = \"0.23\"\nlanguages/php/mod.rs\n1861 is not mentioned")))
    # the documentation result carries "1861" in the text: that one is a category-1 hit, nothing else
    assert _hits(transcript) == [("issue_1861", "tool_result", 8)]
    transcript["conversation"][-1] = _message("user", _response("d", "[dependencies]\ntree-sitter-php = \"0.23\"\nlanguages/php/mod.rs"))
    assert mod.scan(transcript, []) == []


def test_sibling_language_commit_stat_produces_no_hit():
    """scorer/HEADROOM-pilot.md, fenced re-pilot: `git show --stat dbc2971` (Swift support) is a read, not a hit."""
    transcript = _transcript("h55-control",
                             _message("assistant", _request("shell", {"command": "git show --stat dbc2971"}, "s")),
                             _message("user", _response("s", "commit dbc2971\nAuthor: x\n    feat(languages): add Swift support (#1742)\n crates/aptu-coder-core/src/languages/swift.rs | 210 +++++")),
                             _message("assistant", _request("shell", {"command": "git diff --stat dbc2971^ dbc2971"}, "d")),
                             _message("user", _response("d", " crates/aptu-coder-core/src/languages/swift.rs | 2 +-")))
    assert mod.scan(transcript, []) == []


# ---------------------------------------------------------------- tool log and sources

def test_tool_log_targets_are_scanned_with_the_seq_as_index():
    transcript = _transcript("h45-control", _message("assistant", _request("shell", {"command": "date -u"})))
    tool_log = [{"run_id": "h45-control", "seq": 3, "tool": "shell", "target": None},
                {"run_id": "h45-control", "seq": 4, "tool": "shell", "target": "gh issue view 1861"},
                {"run_id": "h45-control", "seq": 5, "tool": "context7__resolve-library-id", "target": "tree-sitter-php"},
                {"run_id": "h45-control", "seq": 6, "tool": "shell", "target": "git pull"}]

    assert _hits(transcript, tool_log) == [("issue_1861", "tool_log", 4), ("network_outside_fence", "tool_log", 6)]


def test_run_id_falls_back_to_the_tool_log_and_absence_is_tolerated():
    tool_log = [{"run_id": "run-9", "seq": 0, "tool": "shell", "target": "curl example.org"}]
    assert [h["run_id"] for h in mod.scan(None, tool_log)] == ["run-9"]
    assert mod.scan({"conversation": []}, []) == [] and mod.scan(None, []) == []


def test_cli_exits_1_on_a_hit(tmp_path, capsys):
    transcript = tmp_path / "transcript.json"
    transcript.write_text(json.dumps(_transcript("r", _message("assistant", _request("shell", {"command": "curl https://example.org"})))))
    tool_log = tmp_path / "tool-log.jsonl"
    tool_log.write_text(json.dumps({"run_id": "r", "seq": 0, "tool": "shell", "target": None}) + "\n")

    assert mod.main([str(transcript), "--tool-log", str(tool_log)]) == 1
    assert "r\tcategory 3 (network_outside_fence)\ttool_request\tmessage 1\tcurl\n1 hit" in capsys.readouterr().out
    clean = tmp_path / "clean.json"
    clean.write_text(json.dumps(_transcript("r")))
    assert mod.main([str(clean)]) == 0
    assert "0 hits" in capsys.readouterr().out
