#!/usr/bin/env python3
"""Fail if a workflow `run:` step interpolates `${{ secrets.* }}` directly into the shell.

Interpolating a secret into a run script leaks it via shell history, process listings
and command echoing, and opens script injection. Pass it through `env:` and reference
the environment variable inside the script instead (see PrunaAI/prunatree#641).
"""
import pathlib
import re
import sys

import yaml

SECRET_PATTERN = re.compile(r"\$\{\{\s*secrets\.")


def iter_run_steps(workflow: dict):
    for job in (workflow.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            run = step.get("run") if isinstance(step, dict) else None
            if isinstance(run, str):
                yield step.get("name", "<unnamed step>"), run


def main() -> int:
    violations = []
    for path in sorted(pathlib.Path(".github/workflows").glob("*.y*ml")):
        workflow = yaml.safe_load(path.read_text())
        if not isinstance(workflow, dict):
            continue
        for name, run in iter_run_steps(workflow):
            if SECRET_PATTERN.search(run):
                violations.append(
                    f"{path}: step {name!r} interpolates a secret directly into `run:` "
                    "— pass it through `env:` and reference the env var instead"
                )

    if violations:
        print("\n".join(violations))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
