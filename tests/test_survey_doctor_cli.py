import json
import subprocess

from project_steward import doctor
from project_steward.cli import main as cli_main
from project_steward.scaffold import apply_plan, plan_files
from project_steward.survey import survey


def test_survey_detects_commands_and_questions(git_repo):
    (git_repo / "package.json").write_text(
        json.dumps({"name": "x", "scripts": {"test": "jest",
                                             "build": "tsc"}}),
        encoding="utf-8")
    (git_repo / "src.ts").write_text("export {}\n", encoding="utf-8")
    findings = survey(git_repo)
    assert findings["candidate_commands"]["test"] == "npm run test"
    assert findings["git"]["is_repo"] is True
    assert any("lint" in q for q in findings["open_questions"])


def test_doctor_ok_after_init_and_fails_on_secret(git_repo):
    plan, mapping = plan_files(git_repo, {"project_name": "Demo"})
    apply_plan(git_repo, plan, mapping)
    results = doctor.run_checks(git_repo)
    assert not [r for r in results if r["status"] == doctor.FAIL
                and "project-steward on PATH" not in r["name"]]
    (git_repo / ".project-steward" / "PROJECT.md").write_text(
        'api_key = "abcdef123456789012345"\n', encoding="utf-8")
    results = doctor.run_checks(git_repo)
    fails = [r for r in results if r["status"] == doctor.FAIL]
    assert any("secrets" in r["name"] for r in fails)


def test_cli_init_and_status(git_repo, capsys):
    rc = cli_main(["init", "--root", str(git_repo), "--project-name",
                   "Demo", "--yes"])
    assert rc == 0
    capsys.readouterr()  # flush init output
    rc = cli_main(["status", "--root", str(git_repo), "--json"])
    assert rc == 0
    recap = json.loads(capsys.readouterr().out)
    assert recap["handoff"]["session_status"] == "closed"


def test_cli_version_runs():
    proc = subprocess.run(
        ["python", "-m", "project_steward", "--version"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert proc.returncode == 0
    assert b"project-steward" in proc.stdout
