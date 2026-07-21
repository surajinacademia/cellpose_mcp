# Pinned Cellpose Upstream Contract Probes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce strict, durable, machine-readable contract evidence for
Python 3.12/Cellpose `4.2.1.1` and Python 3.11/Cellpose `3.1.1.3` without
constructing a model, loading a checkpoint, or downloading model weights, and
record the official stable-version decision before runtime-dependent product
contracts are frozen.

**Architecture:** Two private probe projects own disjoint checked locks. A
stdlib-first guarded probe is copied with a declarative contract into a fresh private
directory. The root runner creates a fresh runtime from the selected lock and
warm cache using a frozen, offline, no-build sync, then launches the probe via
that runtime's Python directly in isolated mode. Guards are installed before Torch or
Cellpose imports. The runner validates the subprocess result with strict
Pydantic records, binds it to product/probe/contract/lock/artifact hashes, and
writes canonical JSON plus a detached digest. A separate official-metadata
command is the only component with network authority. Probe evidence is
source, signature, guarded stub, or synthetic evidence; it never promotes a
scientific feature.

**Tech Stack:** Python 3.11/3.12, uv 0.10.4, Cellpose 4.2.1.1 and 3.1.1.3,
Pydantic 2, NumPy, Torch as installed by the pinned Cellpose distributions,
stdlib AST/inspect/importlib.metadata/hashlib/json/socket/subprocess/tomllib,
pytest, Ruff, and mypy.

## Global Constraints

- The approved designs are
  `docs/superpowers/specs/2026-07-16-cellpose-local-first-design.md` and
  `docs/superpowers/specs/2026-07-21-cellpose-stable-v4-migration-design.md`;
  the latter controls on conflict.
- Phase 0 must be complete and green from a clean committed clone before this
  plan starts.
- CP4 is exactly Cellpose `4.2.1.1` on Python 3.12. CP3 is exactly Cellpose
  `3.1.1.3` on Python 3.11.
- `probes/upstream/cp4/uv.lock` and `probes/upstream/cp3/uv.lock` are probe
  locks. They are neither the transitional root lock nor the production
  worker locks later created under `runtime/`.
- Dependency packages may be downloaded only during a separately approved
  provisioning step. A provisioning request may target package indexes but
  must not target Cellpose or Hugging Face model endpoints.
- Evidence runtimes are provisioned with `uv sync --frozen --offline
  --no-build --no-python-downloads --no-config`; the measured child then executes
  `environment_dir/bin/python -B -I -S` directly, so no resolver, sync wrapper,
  `site`, `.pth`, or `sitecustomize` startup hook can run during measurement.
- Root/controller environments use the same sync hardening plus
  `--no-install-project`; a local editable project cannot be installed under
  `--no-build`. Each controller environment instead contains exactly one
  mode-0600, data-only `cellpose_mcp_probe_source.pth` whose sole UTF-8 line is
  the selected canonical root's `src` directory plus `\n`. The creator uses
  exclusive creation, rejects any `import` line or second path, and verifies
  the file, its SHA-256, every imported `cellpose_mcp.release` path, and the
  selected source root before and after use. Evidence/stable-generation
  controllers additionally require that root to be the exact clean bound
  product clone; Task 0's RED/GREEN development controllers instead bind the
  exact reviewed candidate/root source path while it is intentionally dirty.
  Probe runtime environments never contain this controller binding.
- Every `bash` fence is an independent `/bin/bash` process. Its first command
  is `set -euo pipefail`; a failed preflight terminates the fence before any
  later mutation. A derived value is assigned and validated before a separate
  `export`, never created with `export NAME=$(...)`.
- Every authoritative `uv sync`, `uv lock`, and `uv run` command starts with
  `/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C`, receives a private
  hash-bound `HOME` and `TMPDIR` defined and validated in that same fence, and
  passes only the needed `UV_PROJECT_ENVIRONMENT` and/or `UV_CACHE_DIR` values.
  Every `uv run` additionally fixes `PYTHONNOUSERSITE=1` and
  `PYTHONDONTWRITEBYTECODE=1`; no proxy, token, `PYTHONPATH`, user site, or uv
  config leaks in from the caller. The hash/version-only executable preflight
  is the sole non-provisioning exception.
- Every direct Python command that executes repository or runtime code supplies
  `-B -I` in that order. `-B` is mandatory because isolated mode ignores
  `PYTHONDONTWRITEBYTECODE`. Measured-probe and generator/controller launches add
  `-S` immediately after `-I`; their stdlib bootstrap manually inserts only the
  validated environment `site-packages` and, for controllers, the exact bound
  repository `src`, without importing `site` or processing any `.pth` file.
  An exact sanitized `INTERPRETER --version` executable preflight is the sole
  direct-interpreter exception because it executes no repository/runtime code.
  `uv ... --python INTERPRETER`, `uv run` entrypoints such as `pytest`, and shell
  hash/readlink operations are wrapper/tool invocations, not direct Python
  commands. Every explicit `uv run ... python` payload still supplies `-B -I`.
  Exact command tests freeze all applicable flags and their order.
- No probe calls any of these five constructors: `CellposeModel(...)`,
  `Cellpose(...)`, `SizeModel(...)`, `DenoiseModel(...)`, or
  `CellposeDenoiseModel(...)`.
- No probe calls `torch.load`, `torch.save`, a network connection, or a
  Cellpose model downloader. Any attempt is a guard violation even if caught.
- The probe is trusted-process instrumentation for the exact pinned Python
  dependency graph. Early CPython audit hooks and Python-level wrappers detect
  and reject the enumerated audited network, subprocess, constructor, and
  checkpoint attempts from cooperative Python code;
  this is not hostile native-code containment and makes no OS-sandbox claim.
  Native extensions are trusted only as hash-bound locked artifacts and are
  never given model paths or intentional network/process-spawn authority.
- Stubbed upstream methods allocate instances with `Class.__new__(Class)` and
  replace all network/model operations. They are labeled
  `runtime_stubbed_upstream`, never `runtime_import` or real-model evidence.
- Synthetic metrics and I/O use only generated arrays and a declared private
  scratch directory. No user image, checkpoint, result, or training data is
  read or changed.
- The base package remains the controller/release environment. It does not
  import either probe runtime in-process.
- Every runtime subprocess sets `KMP_DUPLICATE_LIB_OK=TRUE` and
  `OMP_NUM_THREADS=1` in its allowlisted environment before Torch or Cellpose
  is imported. These values are fixed by the runner, never inherited.
- Existing modified and untracked work belongs to the user. No broad add,
  cleanup, reset, checkout, move, deletion, or overwrite is permitted.
- This plan does not freeze public enums, implement workers, expose an MCP
  tool, remove legacy code, load a real model, claim scientific correctness,
  or publish a release.
- Ruff always runs with `--no-fix`.
- Every pytest command that targets the repository root or any clean/candidate
  clone also passes `-p no:cacheprovider`, and every such Ruff command passes
  `--no-cache --no-fix`; evidence work must not create `.pytest_cache` or
  `.ruff_cache` beneath a bound product tree.

### Mandatory execution gates

These gates are part of every referenced fence even where the task prints the
long command only once. They may not be moved to an earlier shell.

Define this helper in each expected-failing RED pytest fence and pass that
fence's displayed sanitized command as its remaining arguments:

```text
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
```

For example, the existing `/usr/bin/env -i ... pytest ...` argv becomes
`probe_expect_red 2 "No module named 'cellpose_mcp.release.upstream_runner'"
/usr/bin/env -i ... pytest ...`, with the argv otherwise byte-for-byte
unchanged. Immediately afterward, run the displayed `.pth`/executable
hash-after comparison and assert the missing target is still absent. The exact
RED contracts are:

| Task | Status | Required unique signature | Required absence after RED |
| --- | ---: | --- | --- |
| 0 | 1 | `runtime imports leaked:` | candidate initializer remains the committed eager bytes |
| 1 | 2 | `No module named 'cellpose_mcp.release.upstream_evidence'` | `src/cellpose_mcp/release/upstream_evidence.py` |
| 2 | 1 | `PROBE_PROJECT_FILES_MISSING` | both probe `pyproject.toml` and `uv.lock` pairs |
| 2 Step 3 full-file rerun | 1 | `PROBE_LOCK_FILES_MISSING` | both probe `uv.lock` files |
| 3 | 1 | `PROBE_EXECUTABLE_MISSING` | `scripts/probe_cellpose_runtime.py` |
| 4 | 1 | `PROBE_CONTRACT_FILES_MISSING` | both `contract.toml` files |
| 5 | 2 | `No module named 'cellpose_mcp.release.upstream_runner'` | runner plus all three generator/verifier scripts |
| 8 | 1 | `EVIDENCE_MISSING` | all six report/digest artifacts |

The RED tests emit the three uppercase sentinel strings above explicitly;
generic `FileNotFoundError` text is not the proof. A bare failing command under
`set -e` is forbidden because it skips the after-checks.

Every commit is merged into its preceding GREEN fence. At the start of that
same shell, before staging, require the exact root and branch, the Phase 0
ancestor, and an empty index:

```text
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
```

Set `PROBE_COMMIT_PATHS` to the task's exact ordered set below, capture
`PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")`
before GREEN, rerun the same `shasum` after GREEN, then stage exactly that
array. Require the sorted cached names to equal the sorted array and bind each
cached blob to the reviewed working byte before `git commit`:

```text
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

| Task | Exact `PROBE_COMMIT_PATHS` |
| --- | --- |
| 0 | `src/cellpose_mcp/__init__.py` `tests/contract/upstream/test_release_import_isolation.py` |
| 1 | `src/cellpose_mcp/release/upstream_evidence.py` `src/cellpose_mcp/release/__init__.py` `tests/contract/upstream/conftest.py` `tests/contract/upstream/test_evidence_schema.py` `tests/packaging/test_distribution_contents.py` |
| 2 | `probes/upstream/cp4/pyproject.toml` `probes/upstream/cp4/uv.lock` `probes/upstream/cp3/pyproject.toml` `probes/upstream/cp3/uv.lock` `tests/contract/upstream/test_probe_projects.py` |
| 3 | `scripts/probe_cellpose_runtime.py` `tests/contract/upstream/conftest.py` `tests/contract/upstream/test_probe_engine.py` |
| 4 | `probes/upstream/cp4/contract.toml` `probes/upstream/cp3/contract.toml` `scripts/probe_cellpose_runtime.py` `tests/contract/upstream/test_cp4_expectations.py` `tests/contract/upstream/test_cp3_expectations.py` `tests/contract/upstream/test_probe_engine.py` |
| 5 | `src/cellpose_mcp/release/upstream_runner.py` `scripts/generate_upstream_contract_evidence.py` `scripts/generate_cellpose_stable_release_check.py` `scripts/check_upstream_contract_evidence.py` `tests/contract/upstream/conftest.py` `tests/contract/upstream/test_runner_isolation.py` `tests/packaging/test_distribution_contents.py` |
| 8 | `docs/evidence/upstream/README.md` plus the six exact report/digest artifacts and `tests/contract/upstream/test_committed_reports.py` |

`PROBE_COMMIT_SUBJECT` is the exact subject already printed in each task's
commit command. Task 0 additionally requires the staged and committed
`src/cellpose_mcp/__init__.py` blob to have SHA-256
`445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50`.
Before Task 8 stages anything, typed-load and digest-verify all three reports,
require their one shared `product.commit_sha` to equal `PROBE_PRECOMMIT_HEAD`,
and after commit require that implementation SHA to be the evidence commit's
sole parent.

Before the first `uv sync` or mutating `uv lock` in each fence, perform this
same-fence controller gate, via this helper or its exact inline equivalent, for
uv and every selected managed Python,
using the three hashes and exact version strings from Task 0. A Task 7
official-metadata fence invokes no uv or separate managed-runtime path. It uses
`/usr/bin/shasum` for data files, requires the controller symlink's exact lexical
target with `/usr/bin/readlink`, then applies the hash/version gate to the
controller environment's Python before its first Python execution. That target
must be the sealed CP4/controller Python:

```text
probe_require_tool() {
  PROBE_TOOL_PATH=$1
  PROBE_TOOL_SHA256=$2
  PROBE_TOOL_VERSION=$3
  test "$(/usr/bin/shasum -a 256 "$PROBE_TOOL_PATH" | /usr/bin/awk '{print $1}')" = "$PROBE_TOOL_SHA256"
  test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$HOME" TMPDIR="$TMPDIR" "$PROBE_TOOL_PATH" --version 2>&1)" = "$PROBE_TOOL_VERSION"
}
```

The target interpreter never reads or hashes its own executable. This
same-fence gate applies to Task 0 Steps 7 and 10, Task 2 Steps 5 and 6, both
Task 6 controller sync paths, both Task 9 syncs, and the runner immediately
before each provisioning spawn. Task 7 uses the controller-Python variant just
defined.

Exact executable policy is closed and code-owned: uv is path
`/Users/suraj/.local/bin/uv`, SHA-256
`392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5`,
and version output `uv 0.10.4 (079e3fd05 2026-02-17)`; CP4/controller Python is
the displayed 3.12.12 path with SHA-256
`6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483`;
CP3 Python is the displayed 3.11.14 path with SHA-256
`e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5`.
The generator derives `ProbeRequest` hashes and expected version from its
closed runtime-ID mapping; the CLI accepts no hash/version override. A request
whose path, approved hash, or version does not equal that mapping is rejected
before any child spawn. The explicit inline hash/version comparisons in task
fences are the same-fence equivalent of `probe_require_tool`; either exact form
satisfies the gate, and a mere pre/post self-consistency hash does not.

`validate_transitive_lock_sources` is implemented and unit-tested in Task 1,
before either probe lock is generated. It parses the complete TOML package
closure. Every installable package must have exactly
`source = { registry = "https://pypi.org/simple" }`; every wheel/sdist URL must
parse as HTTPS, host `files.pythonhosted.org`, path beginning `/packages/`, no
userinfo, port, query, or fragment, and a SHA-256 plus positive size. It rejects
`git`, `url`, `path`, `directory`, `editable`, `workspace`, or unknown source
keys anywhere, not only on direct dependencies. The required
`excluded_project_name` must equal the adjacent `pyproject.toml` project name
and excludes exactly one non-installable project record: `{ editable = "." }`
for the root controller, whose syncs use `--no-install-project`, or
`{ virtual = "." }` for a probe project whose `[tool.uv] package` is exactly
`false`. That record has no artifacts; all of its dependency edges must resolve,
and every transitive package is still checked. No other local source is
accepted.

Before an existing lock is used or updated, validate it. The first creation of
each absent probe lock is the sole unavoidable exception: assert the destination
is absent and the adjacent project is exact, run the approved sanitized network
`uv lock` command, and immediately validate the new lock before any sync or
package import. A validation failure stops with the new untracked lock retained
for inspection; it is never synced, staged, or silently deleted. Validate again
before every online or offline sync and immediately after any later lock write.
This quarantine ordering acknowledges that CP3 metadata is not guaranteed to
exist in the new private cache while ensuring unvalidated lock data never
authorizes installation.

The root controller lock is the already Phase-0-validated immutable exception
to invoking the Task-1 validator before that validator exists. This plan never
modifies `uv.lock`; every root, candidate, clean-clone, acceptance, and
reproduction controller fence independently requires its SHA-256 to equal
`dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b`
before sync. Any different root lock stops the plan for review. After Task 1,
the validator's synthetic and probe-lock tests prove the same complete-closure
policy; no root sync is authorized by a merely shape-valid 64-hex digest.

## Evidence boundary

The report permits exactly these evidence kinds:

| Kind | Meaning | May authorize a real feature? |
| --- | --- | --- |
| `runtime_import` | Imported symbol/version/path observed in the isolated pinned environment | No |
| `runtime_signature` | `inspect.signature` observed on an imported pinned callable | No |
| `runtime_stubbed_upstream` | Upstream method body executed with no constructor, net, checkpoint, or downloader | No |
| `static_ast` | Branch/call/property observed in the installed source AST | No |
| `synthetic_pure` | Pure metrics/transforms/I/O exercised with generated arrays | No |
| `official_metadata` | Version/tag/release metadata from an approved official endpoint | No |

Every real-model requirement remains an explicit unresolved gate. A PASS in
this plan means “the pinned upstream contract was measured safely,” not “the
Cellpose feature works for users.”

## File map

### Create

| Path | Responsibility |
| --- | --- |
| `src/cellpose_mcp/release/upstream_evidence.py` | Strict report schema, canonical serialization, and digest verification |
| `src/cellpose_mcp/release/upstream_runner.py` | Clean-commit checks, isolated environment/command construction, subprocess validation, and atomic report writes |
| `probes/upstream/cp4/pyproject.toml` | Private Python 3.12/Cellpose 4.2.1.1 probe project |
| `probes/upstream/cp4/uv.lock` | Checked CP4 probe dependency graph |
| `probes/upstream/cp4/contract.toml` | Declarative CP4 check IDs and exact expectations |
| `probes/upstream/cp3/pyproject.toml` | Private Python 3.11/Cellpose 3.1.1.3 probe project |
| `probes/upstream/cp3/uv.lock` | Checked CP3 probe dependency graph |
| `probes/upstream/cp3/contract.toml` | Declarative CP3 check IDs and exact expectations |
| `scripts/probe_cellpose_runtime.py` | Stdlib-first guarded executable copied into each isolated probe |
| `scripts/generate_upstream_contract_evidence.py` | Offline contract-report CLI |
| `scripts/generate_cellpose_stable_release_check.py` | Official-metadata-only stable-version CLI |
| `scripts/check_upstream_contract_evidence.py` | Offline report/digest/source-binding verifier |
| `tests/contract/upstream/conftest.py` | Deterministic valid records and fake probe projects |
| `tests/contract/upstream/test_release_import_isolation.py` | Prove release/controller imports do not load the legacy server, Cellpose, Torch, or FastMCP |
| `tests/contract/upstream/test_evidence_schema.py` | Schema/canonical JSON/digest adversarial coverage |
| `tests/contract/upstream/test_probe_projects.py` | Pin, lock, Python, artifact, and isolation policy |
| `tests/contract/upstream/test_probe_engine.py` | Guard installation, exit codes, fake-source behavior, and pure checks |
| `tests/contract/upstream/test_runner_isolation.py` | Command/environment/path/process/report atomicity |
| `tests/contract/upstream/test_cp4_expectations.py` | Complete CP4 required-ID and exact-expectation coverage |
| `tests/contract/upstream/test_cp3_expectations.py` | Complete CP3 required-ID and exact-expectation coverage |
| `tests/contract/upstream/test_committed_reports.py` | Committed report, digest, source-commit, and no-model enforcement |
| `docs/evidence/upstream/README.md` | Human-readable evidence scope and reproduction commands |
| `docs/evidence/upstream/cp4-4.2.1.1-contract.json` | Canonical CP4 contract report |
| `docs/evidence/upstream/cp4-4.2.1.1-contract.json.sha256` | Detached CP4 report digest |
| `docs/evidence/upstream/cp3-3.1.1.3-contract.json` | Canonical CP3 contract report |
| `docs/evidence/upstream/cp3-3.1.1.3-contract.json.sha256` | Detached CP3 report digest |
| `docs/evidence/upstream/cellpose-stable-release-check.json` | Official PyPI/GitHub stable-version report |
| `docs/evidence/upstream/cellpose-stable-release-check.json.sha256` | Detached stable-version report digest |

### Modify

| Path | Exact scope |
| --- | --- |
| `src/cellpose_mcp/__init__.py` | With explicit approval, adopt the already-inventoried lazy `mcp` export hunk exactly; make release/controller imports runtime-light |
| `src/cellpose_mcp/release/__init__.py` | Preserve all eight existing feature-manifest exports; append the four evidence functions and two report types |
| `tests/packaging/test_distribution_contents.py` | Add only the two new release modules to the exact wheel/sdist allowlists |

### Do not modify

- `pyproject.toml` or the transitional root `uv.lock`
- `MANIFEST.in`; its existing allowlist keeps probe projects and evidence out
  of the public wheel
- `.github/workflows/ci.yml`
- `src/cellpose_mcp/tools.py`
- `src/cellpose_mcp/operations.py`
- `src/cellpose_mcp/server.py`
- `src/cellpose_mcp/mcp_instance.py`
- `src/cellpose_mcp/cli/`
- Existing legacy tests, demos, results, training data, or user experiments

## Exact interfaces

`src/cellpose_mcp/release/upstream_evidence.py` exposes:

```python
def load_upstream_report(
    path: Path,
) -> UpstreamContractReport | StableReleaseCheckReport:
    """Load one strict report selected by its report_kind discriminator."""


def canonical_report_bytes(
    report: UpstreamContractReport | StableReleaseCheckReport,
) -> bytes:
    """Serialize sorted compact UTF-8 JSON with one trailing newline."""


def report_sha256(
    report: UpstreamContractReport | StableReleaseCheckReport,
) -> str:
    """Hash canonical_report_bytes with SHA-256."""


def verify_report_digest(path: Path) -> None:
    """Require PATH.sha256 to contain '<digest>  <basename>\\n'."""
```

Canonical JSON uses `sort_keys=True`, `separators=(",", ":")`,
`ensure_ascii=False`, `allow_nan=False`, UTF-8, and exactly one final newline.

`src/cellpose_mcp/release/upstream_runner.py` exposes:

```python
class ProbeIsolationError(RuntimeError):
    """The requested runtime or filesystem boundary is unsafe."""


class ProbeProvisioningError(RuntimeError):
    """Fresh offline runtime provisioning failed."""


class ProbeProtocolError(RuntimeError):
    """The isolated subprocess violated the probe protocol."""


@dataclass(frozen=True, slots=True)
class ProbeRequest:
    runtime_id: Literal["cp4", "cp3"]
    project_dir: Path
    environment_dir: Path
    contract_path: Path
    probe_path: Path
    generator_path: Path
    cache_dir: Path
    provisioning_home: Path
    provisioning_tmp: Path
    python_path: Path
    expected_python_version: Literal["Python 3.12.12", "Python 3.11.14"]
    approved_python_sha256: Sha256Hex
    uv_path: Path
    approved_uv_sha256: Sha256Hex


def build_probe_environment(
    request: ProbeRequest,
    scratch: Path,
) -> dict[str, str]:
    """Return the complete allowlisted environment for one probe."""


def build_probe_command(
    request: ProbeRequest,
    copied_probe: Path,
    copied_contract: Path,
) -> tuple[str, ...]:
    """Return the direct isolated runtime-Python probe argv."""


def build_provisioning_command(request: ProbeRequest) -> tuple[str, ...]:
    """Return the frozen/offline/no-build/no-download/no-config sync argv."""


def build_provisioning_environment(request: ProbeRequest) -> dict[str, str]:
    """Return the complete allowlisted environment for offline provisioning."""


def expected_probe_project_name(
    request: ProbeRequest,
) -> Literal[
    "cellpose-mcp-cp4-contract-probe",
    "cellpose-mcp-cp3-contract-probe",
]:
    """Map one closed runtime ID to its sole accepted virtual project root."""


def build_controller_environment(home: Path, temporary: Path) -> dict[str, str]:
    """Return the exact environment supplied to a direct controller Python."""


def require_sanitized_controller_environment() -> dict[str, str]:
    """Validate and return the complete current controller environment."""


def require_controller_source_binding(repo_root: Path) -> Sha256Hex:
    """Validate the sole plain-path .pth file and imports beneath REPO_ROOT/src."""


def bind_current_python_command(repo_root: Path) -> CommandBinding:
    """Bind the directly executed interpreter, argv, cwd, and sanitized env."""


def require_clean_product(repo_root: Path) -> ProductBinding:
    """Return the canonical root/HEAD binding or reject a dirty/non-Git root."""


def write_report_exclusive(
    report: UpstreamContractReport | StableReleaseCheckReport,
    output_path: Path,
) -> None:
    """Atomically create canonical JSON and its digest without overwrite."""


def run_probe(
    request: ProbeRequest,
    *,
    repo_root: Path,
    output_path: Path,
) -> UpstreamContractReport:
    """Run, validate, bind, and atomically write one clean-commit report."""
```

Task 1 also adds this pure-stdlib lock-policy function to
`upstream_evidence.py`; `upstream_runner.py` imports and re-exports the same
function object rather than duplicating it:

```python
def validate_transitive_lock_sources(
    lock_path: Path,
    *,
    excluded_project_name: str,
) -> Sha256Hex:
    """Bind a lock whose complete installable closure is exact PyPI HTTPS."""
```

The copied probe CLI is:

```text
python -B -I -S probe_cellpose_runtime.py --contract CONTRACT.toml --output -
```

Exit codes are fixed:

- `0`: every required check passed and all safety counters are zero;
- `2`: one or more upstream contract checks failed;
- `3`: network, process-spawn, model-constructor, checkpoint-load/save, isolation,
  filesystem, cache, or SSL-context guard violation; and
- `4`: malformed contract, unsupported runtime, or internal probe failure.

The copied probe emits an internal stdlib JSON payload with
`payload_kind = "cellpose_probe"`, runtime/import/installation observations,
guards, verification totals, checks, and unresolved gates. It does not invent
product, Git, lock, command-executable, or upstream-metadata fields it cannot
observe. `run_probe` validates that payload, adds those outer bindings, and
constructs the final Pydantic `UpstreamContractReport`.

The offline generator CLI is:

```text
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME=ABSOLUTE_PRIVATE_HOME TMPDIR=ABSOLUTE_PRIVATE_TMP PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 ABSOLUTE_CONTROLLER_PYTHON -B -I -S scripts/generate_upstream_contract_evidence.py contract --runtime cp4|cp3 --environment ABSOLUTE_ENVIRONMENT_PATH --cache ABSOLUTE_WARM_UV_CACHE_PATH --python ABSOLUTE_MANAGED_PYTHON_PATH --uv /Users/suraj/.local/bin/uv --output ABSOLUTE_JSON_PATH
```

That command also requires
`--provisioning-home ABSOLUTE_FRESH_PROVISIONING_HOME` and
`--provisioning-tmp ABSOLUTE_FRESH_PROVISIONING_TMP`; the two paths are
distinct absent children of one runner-owned private root and are never the
measured child's HOME/TMP.

The official metadata CLI is:

```text
python -B -I -S scripts/generate_cellpose_stable_release_check.py
  --cp4-version 4.2.1.1
  --cp3-version 3.1.1.3
  --output ABSOLUTE_JSON_PATH
```

That script also exposes this exact dependency-injected boundary for tests;
production `main` supplies the hardened HTTPS implementation:

```python
@dataclass(frozen=True, slots=True)
class OfficialHttpResponse:
    url: str
    status: int
    body: bytes


class OfficialResponseSource(Protocol):
    def get(
        self,
        url: str,
        *,
        timeout_seconds: Literal[30],
        maximum_bytes: Literal[10485760],
    ) -> OfficialHttpResponse: ...


def generate_stable_release_check(
    *,
    repo_root: Path,
    cp4_version: Literal["4.2.1.1"],
    cp3_version: Literal["3.1.1.3"],
    output_path: Path,
    responses: OfficialResponseSource,
) -> StableReleaseCheckReport:
    """Fetch, bind, validate, and exclusively write one stable report."""
```

The contract generator preserves probe exit `0`, `2`, or `3`; protocol/setup
errors exit `4`. The stable generator exits `0` for a canonical PASS report,
`2` for a canonical policy-FAIL report, and `4` for transport, schema, or
writer failure. Exit `4` never creates a final JSON/digest pair.

The offline verifier CLI is:

```text
python -B -I scripts/check_upstream_contract_evidence.py
  --root docs/evidence/upstream
  --require-all

python -B -I scripts/check_upstream_contract_evidence.py
  --compare-invariants EXPECTED_REPORT ACTUAL_REPORT
```

The verifier exits `0` only on complete success and `1` for any missing,
stale, noncanonical, mismatched, or non-PASS committed evidence.

Both generator CLIs reject an unsanitized controller before importing any
project module. Each script starts under `-B -I -S`, requires
`sys.flags.dont_write_bytecode == sys.flags.isolated == sys.flags.no_site == 1`,
`"site" not in sys.modules`, and exact `sys.orig_argv`, then runs a tiny
stdlib-only bootstrap. The bootstrap derives `repo_root` from the exact
canonical generator script path, derives the lexical controller root from
`Path(sys.executable).parent.parent` without resolving away the environment,
and derives its exact `lib/python3.12/site-packages`. It validates
`cellpose_mcp_probe_source.pth` with `lstat` as a regular, non-symlink,
current-user-owned mode-0600 file containing one UTF-8 canonical
`repo_root/src` line and no `import` or second path. It then performs
`sys.path[:0] = [str(source_root), str(site_packages)]`. It never imports
`site`, calls `site.addsitedir`, or executes any `.pth`, `sitecustomize.py`, or
`usercustomize.py` content. Only after this bootstrap may
the script import and repeat the canonical validation from `upstream_runner`.
Their shell recipes invoke the already-provisioned controller environment's
absolute `bin/python -B -I -S` directly through `/usr/bin/env -i`.
`build_controller_environment` supplies exactly `PATH=/usr/bin:/bin`,
`LANG=C`, `LC_ALL=C`, a private `HOME`, a private `TMPDIR`,
`PYTHONNOUSERSITE=1`, and `PYTHONDONTWRITEBYTECODE=1`.
`require_sanitized_controller_environment` permits only those seven keys plus
macOS's automatically injected `__CF_USER_TEXT_ENCODING`, whose value must
match three hexadecimal colon-separated fields. It rejects inherited Python
paths, tokens, proxies, index settings, cookies, netrc overrides, and
`SSL_CERT_*`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, or `PIP_CERT` variables.
Immediately after importing the runner, each CLI calls
`require_controller_source_binding(repo_root)`, requires its own module plus
every imported `cellpose_mcp.release` module to resolve beneath that exact
`repo_root/src`, records the returned `.pth` digest in memory, and repeats the
path/content/mode/digest/import checks immediately before any report write.
The stable report's `command` binds exactly `tuple(sys.orig_argv)`, canonical
cwd, the complete validated current environment, and the directly executed
controller-Python bytes; `sys.argv` is never used to infer interpreter flags
because CPython removes those flags from it. The binding requires
`sys.orig_argv[0] == sys.executable` and the exact lexical controller path,
followed by `-B`, `-I`, `-S`, the exact stable-generator path, and the exact
application arguments in order. It never claims to bind an outer shell or uv
process. `executable_path` is that lexical path's pre/post-identical canonical
target, and `executable_sha256` is the pre/post-identical target-byte digest.

## Strict report schema

All Pydantic models use:

```python
model_config = ConfigDict(extra="forbid", frozen=True)
```

Use constrained strings for a 64-character lowercase SHA-256, a 40-character
lowercase Git commit, a non-empty relative POSIX path, and a timezone-aware UTC
timestamp ending in `Z`. `RepoRelativeCwd` permits the exact string `.` for the
repository root or an otherwise valid relative POSIX path; ordinary
`RelativePosixPath` never permits `.`. Reject absolute paths in
repository-relative fields, `..` components, duplicate check IDs, non-finite
numbers, and empty required collections.

Implement these strict nested models; every tuple is non-empty unless the
field name below explicitly says it may be empty:

```text
ProductBinding
  repository: absolute canonical path string
  commit_sha: GitCommitHex
  pre_run_dirty: Literal[false]
  post_run_dirty: Literal[false]

CommandBinding
  argv: tuple[non-empty string, ...]
  cwd_repo_relative: RepoRelativeCwd
  environment: dict[non-empty string, string]
  executable_path: absolute canonical path string
  executable_sha256: Sha256Hex

ProvisioningBinding
  all CommandBinding fields
  provisioning_home: absolute canonical path string
  provisioning_home_before_sha256: Sha256Hex
  provisioning_home_after_sha256: Sha256Hex
  provisioning_tmp: absolute canonical path string
  provisioning_tmp_before_sha256: Sha256Hex
  provisioning_tmp_after_sha256: Sha256Hex

ProbeInterpreterObservation
  lexical_path: absolute path string exactly used as argv[0]
  canonical_path: absolute canonical path string
  sha256: Sha256Hex
  base_prefix: absolute canonical path string
  base_prefix_python_path: absolute canonical path string

InterpreterBinding
  all ProbeInterpreterObservation fields
  approved_managed_python_path: absolute canonical path string

ScriptBinding
  path: RelativePosixPath
  sha256: Sha256Hex

ProbeBinding
  path: RelativePosixPath
  sha256: Sha256Hex
  contract_path: RelativePosixPath
  contract_sha256: Sha256Hex

ProbeRuntimeObservation
  runtime_id: Literal["cp4", "cp3"]
  python_implementation: non-empty string
  python_version: non-empty string
  platform: non-empty string
  machine: non-empty string
  sys_prefix: absolute canonical path string
  environment_root: absolute canonical path string
  site_packages_path: absolute canonical path string
  interpreter: ProbeInterpreterObservation
  imported_cellpose_path: absolute canonical path string
  compatible_wheel_tags: tuple[non-empty PEP 425 tag string, ...]
  user_site_enabled: Literal[false]
  repository_paths_on_sys_path: tuple[absolute canonical path string, ...]
    (may be empty and must be empty for PASS)

RuntimeObservation
  all ProbeRuntimeObservation fields except interpreter
  interpreter: InterpreterBinding
  uv_version: Literal["0.10.4"]

RegistryArtifact
  version: non-empty PEP 440 version string
  filename: non-empty basename
  url: absolute HTTPS URL
  sha256: Sha256Hex
  size: positive integer

OfficialRegistryArtifact
  all RegistryArtifact fields
  yanked: boolean

LockBinding
  path: RelativePosixPath
  sha256: Sha256Hex
  python_constraint: non-empty string
  expected_cellpose_version: Literal["4.2.1.1", "3.1.1.3"]
  artifact_candidates: tuple[RegistryArtifact, ...]

InstalledDistribution
  name: normalized non-empty distribution name
  version: non-empty PEP 440 version string

ObservedCellposeInstallation
  version: Literal["4.2.1.1", "3.1.1.3"]
  metadata_sha256: Sha256Hex
  normalized_record_sha256: Sha256Hex
  normalized_installed_tree_sha256: Sha256Hex
  source_file_hashes: dict[RelativePosixPath, Sha256Hex]

ProbeInstallationObservation
  distributions: tuple[InstalledDistribution, ...]
  cellpose: ObservedCellposeInstallation

CellposeInstallation
  all ObservedCellposeInstallation fields
  installation_policy: Literal["uv-frozen-offline-no-build-no-python-downloads-no-config-unique-compatible-wheel"]
  selected_artifact: RegistryArtifact

InstallationObservation
  distributions: tuple[InstalledDistribution, ...]
  cellpose: CellposeInstallation

DeclaredUpstreamSource
  repository: Literal["https://github.com/MouseLand/cellpose"]
  declared_tag: Literal["v4.2.1.1", "v3.1.1.3"]
  declared_tag_commit: GitCommitHex
  locked_pypi_artifacts: tuple[RegistryArtifact, ...]

GuardObservation
  network_attempt_count: non-negative integer
  network_attempts: tuple[JsonValue, ...] (may be empty)
  torch_load_count: non-negative integer
  torch_load_attempts: tuple[JsonValue, ...] (may be empty)
  torch_save_count: non-negative integer
  torch_save_attempts: tuple[JsonValue, ...] (may be empty)
  model_constructor_count: non-negative integer
  model_constructor_attempts: tuple[JsonValue, ...] (may be empty)
  process_spawn_count: non-negative integer
  process_spawn_attempts: tuple[JsonValue, ...] (may be empty)
  model_directory_before_sha256: Sha256Hex
  model_directory_after_sha256: Sha256Hex
  managed_root_hashes_before: dict[non-empty root name, Sha256Hex]
  managed_root_hashes_after: dict[non-empty root name, Sha256Hex]
  unapproved_filesystem_deltas: tuple[non-empty string, ...] (may be empty)
  ssl_context_unchanged: boolean

VerificationSummary
  required: non-negative integer
  executed: non-negative integer
  passed: non-negative integer
  failed: non-negative integer

SymbolTarget
  module: non-empty importable module name
  qualname: non-empty qualified symbol name

SourceEvidence
  path: RelativePosixPath relative to the canonical runtime site-packages root
  sha256: Sha256Hex
  lines: tuple[positive integer, ...] (non-empty, unique, ascending)

SourceExpectation
  path: RelativePosixPath relative to the canonical runtime site-packages root
  lines: tuple[positive integer, ...] (non-empty, unique, ascending)

ContractCheck
  id: non-empty dotted identifier
  category: non-empty string
  evidence_kind: one of the six evidence kinds in this plan
  required: boolean
  targets: tuple[SymbolTarget, ...]
  expected: JsonValue
  observed: JsonValue
  status: Literal["PASS", "FAIL"]
  sources: tuple[SourceEvidence, ...] (may be empty only where the contract declares no installed source)

ContractDescriptor
  id: non-empty dotted identifier
  category: non-empty string
  evidence_kind: one of the six evidence kinds in this plan
  required: Literal[true]
  targets: tuple[SymbolTarget, ...]
  expected: JsonValue
  sources: tuple[SourceExpectation, ...] (may be empty only for a declared source-less observation)

ParsedContractV1
  runtime_id: Literal["cp4", "cp3"]
  python_constraint: non-empty string
  cellpose_version: Literal["4.2.1.1", "3.1.1.3"]
  scope: Literal["no-weight-no-download"]
  required_check_ids: tuple[non-empty dotted identifier, ...]
  unresolved_real_model_gates: tuple[non-empty string, ...]
  repository: Literal["https://github.com/MouseLand/cellpose"]
  tag: Literal["v4.2.1.1", "v3.1.1.3"]
  tag_commit: GitCommitHex
  checks: tuple[ContractDescriptor, ...]

ProbePayloadV1
  payload_schema_version: Literal[1]
  payload_kind: Literal["cellpose_probe"]
  outcome: Literal["PASS", "FAIL"]
  runtime: ProbeRuntimeObservation
  installation: ProbeInstallationObservation
  guards: GuardObservation
  verification: VerificationSummary
  checks: tuple[ContractCheck, ...]
  unresolved_real_model_gates: tuple[non-empty string, ...]

UpstreamContractReport
  schema_version: Literal[1]
  report_kind: Literal["cellpose_contract"]
  report_id: non-empty string
  scope: Literal["no-weight-no-download"]
  outcome: Literal["PASS", "FAIL"]
  generated_at_utc: UTC timestamp
  product: ProductBinding
  provisioning: ProvisioningBinding
  command: CommandBinding
  runner: ScriptBinding
  generator: ScriptBinding
  probe: ProbeBinding
  runtime: RuntimeObservation
  lock: LockBinding
  installation: InstallationObservation
  upstream_source: DeclaredUpstreamSource
  guards: GuardObservation
  verification: VerificationSummary
  checks: tuple[ContractCheck, ...]
  unresolved_real_model_gates: tuple[non-empty string, ...]

OfficialSource
  url: absolute allowlisted HTTPS URL
  http_status: Literal[200]
  response_sha256: Sha256Hex
  response_bytes: integer in 1..10485760

StablePolicy
  cp4_required: Literal["4.2.1.1"]
  cp3_required: Literal["3.1.1.3"]

MetadataCheck
  id: non-empty dotted identifier
  expected: JsonValue
  observed: JsonValue
  status: Literal["PASS", "FAIL"]
  source_url: absolute allowlisted HTTPS URL
  source_response_sha256: Sha256Hex
  json_pointer: non-empty RFC 6901 JSON pointer | null

StableObservation
  latest_non_yanked_stable: non-empty PEP 440 version string
  cp4_tag_commit: GitCommitHex
  cp3_tag_commit: GitCommitHex
  release_files_by_version: dict[
    Literal["4.2.1.1", "3.1.1.3"],
    tuple[OfficialRegistryArtifact, ...]
  ]

StableReleaseCheckReport
  schema_version: Literal[1]
  report_kind: Literal["stable_release_check"]
  report_id: non-empty string
  scope: Literal["official-metadata"]
  outcome: Literal["PASS", "FAIL"]
  generated_at_utc: UTC timestamp
  product: ProductBinding
  command: CommandBinding
  script: ScriptBinding
  sources: tuple[OfficialSource, ...]
  policy: StablePolicy
  observed: StableObservation
  checks: tuple[MetadataCheck, ...]
```

The stdlib probe serializes exactly `ProbePayloadV1`; the controller validates
it before constructing a report. Translation is mechanical and has no
optional fallback:

| Final field | Sole source |
| --- | --- |
| `product` | clean clone root, one unchanged `git rev-parse HEAD`, and clean pre/post porcelain status |
| `provisioning` | runner-owned frozen/offline/no-build/no-python-downloads/no-config sync argv, environment, cwd, uv bytes, and the distinct private HOME/TMP paths with unchanged before/after tree hashes |
| `command` | exact direct runtime-Python argv/environment plus interpreter bytes |
| `runner` | current `upstream_runner.py` path and pre-run bytes beneath the clean clone |
| `generator` | caller-supplied offline generator path and pre-run bytes beneath the clean clone |
| `probe` | repository-relative source paths and pre-copy byte hashes |
| `runtime` | validated payload, exact lexical/canonical/base-prefix/approved-managed interpreter binding, plus `/Users/suraj/.local/bin/uv --version` |
| `lock` | selected probe `uv.lock` bytes and its exact Cellpose record |
| `installation` | validated observed payload plus the lock's sole compatible wheel and fixed no-build policy |
| `upstream_source.declared_*` | selected contract `[upstream]` table |
| `upstream_source.locked_pypi_artifacts` | exact Cellpose registry artifacts in the selected lock |
| guards, verification, checks, unresolved gates | validated payload |

The offline report therefore makes no official-current-release claim. The
separate `stable_release_check` report is the only authority that verifies
PyPI state or GitHub refs.

The stable report has this exact source map:

| Final field | Sole source |
| --- | --- |
| `product` | unchanged clean clone root/HEAD and clean pre/post porcelain status |
| `command` | `bind_current_python_command`: direct controller Python, exact validated `tuple(sys.orig_argv)` including `-B -I -S`, cwd, complete sanitized environment, and executable bytes |
| `script` | repository-relative stable-generator path and pre/post-identical bytes |
| `sources` | exact approved HTTPS response URL/status/body length/body SHA-256 |
| `policy` | the two CLI version arguments after exact-literal validation |
| `observed` | parsed official responses only |
| `checks` | deterministic comparisons of policy with the exact bound response/pointer data |

The stable generator hashes and canonically binds its direct controller
`sys.executable` and exact `sys.orig_argv` before its first request, then
rechecks the same canonical
path and bytes after the final response and immediately before writing. It also
rechecks clean HEAD, worktree porcelain, script bytes, and output nonexistence
immediately before the exclusive report/digest write. Any controller-Python
path/byte swap is setup failure `4` and creates no final report or digest.
An adversarial test copies the approved executable bytes to a different
canonical path and proves the stable generator rejects that same-byte alias
before its fake transport records any request.
Separate adversarial tests remove each of `-B`, `-I`, and `-S`, reorder the
flags, substitute the script path, and alter one application argument; every
case exits `4` before the fake transport records a request or any report/digest
is created.

Model validators require counter/list lengths to agree, before/after model
directory and complete managed-root hash maps to match for PASS,
`ssl_context_unchanged is true`, every attempt/delta list empty, `required == executed == passed ==
len(required checks)` and `failed == 0` for PASS, exact required-check order
from the selected contract, unique distribution/artifact/check IDs, CP4 with
Python `3.12.*` and Cellpose `4.2.1.1`, CP3 with Python `3.11.*` and Cellpose
`3.1.1.3`, and identical contract/lock/installation versions. A source-backed
check must provide every contract-required `SourceExpectation` as measured
`SourceEvidence`; a
contract-declared source-less import or synthetic check provides an empty
tuple. Stable PASS requires every metadata check PASS, all official
`(source_url, source_response_sha256)` pairs referenced by checks to match
exactly one `OfficialSource`, every JSON pointer to have resolved against that
exact response during generation, the exact two tag commits, version-keyed
release-file identities, and `latest_non_yanked_stable == "4.2.1.1"`.
Every official artifact preserves its file-level `yanked` flag. The selected
CP4/CP3 installed wheel must match an official artifact with `yanked is false`;
a release containing some other non-yanked file is insufficient.

Contract PASS also requires exactly one lock wheel whose parsed tags intersect
`runtime.compatible_wheel_tags`, `selected_artifact` byte-for-byte equal to
that wheel record, and the fixed no-build installation policy. The raw RECORD
verification and console-script normalization must have completed without an
ignored row.

Cross-record validators also require `command.argv[0]` to equal
`runtime.interpreter.lexical_path`, `command.executable_path` to equal
`runtime.interpreter.canonical_path`, and `command.executable_sha256` to equal
`runtime.interpreter.sha256`; `command.argv[1:4]` must equal
`("-B", "-I", "-S")`. The canonical runtime target,
`runtime.interpreter.base_prefix_python_path`, and
`runtime.interpreter.approved_managed_python_path` must all be the same path;
the observed canonical `base_prefix` must be the exact parent prefix implied by
that approved managed-Python path. These are exact equalities, not basename,
version-string, or common-prefix checks.
They require `command.argv[0]` to equal
`runtime.environment_root/bin/python`, `runtime.site_packages_path` to equal the
exact regular, non-symlink `lib/pythonX.Y/site-packages` child derived from that
environment root, both `command.environment["VIRTUAL_ENV"]` and
`command.environment["UV_PROJECT_ENVIRONMENT"]` to equal that environment root,
and `runtime.imported_cellpose_path` to resolve beneath that site-packages
directory. Under `-S`, `runtime.sys_prefix` must equal
`runtime.interpreter.base_prefix`, not `runtime.environment_root`; treating
`sys.prefix` as evidence that the virtual environment was activated is a
protocol error.

They additionally require `provisioning.argv[0]` and
`provisioning.executable_path` to bind the approved uv executable,
`provisioning.environment["HOME"]` and `["TMPDIR"]` to equal the two explicit
provisioning paths, and both before/after storage hashes to match for PASS.
Those two paths must be distinct fresh regular directories beneath the same
new mode-0700 non-symlink parent and disjoint from the repository, controller
HOME/TMP, warm cache, runtime environment, measured scratch, and output.
Adversarial typed-model tests mutate each equality, alias the paths, substitute
the pre-existing `/private/tmp` parent, and change each after hash; every case
is rejected before committed evidence can load as PASS.

After validating `ProbePayloadV1`, `run_probe` parses the copied TOML again as
`ParsedContractV1` and compares every payload check, position by position, to
the contract descriptor tuple. `id`, `category`, `evidence_kind`, `required`,
the complete ordered `targets` tuple, and canonicalized `expected` must all be
exactly equal. For each descriptor source, the payload must reproduce the
ordered `path` and `lines` and add the SHA-256 of that exact installed file;
only `observed`, `status`, and those measured hashes come from execution. Payload and
contract unresolved-gate tuples must also be exactly equal. Extra, missing,
reordered, or semantically altered descriptors are protocol exit `4`, never a
FAIL/PASS report. Adversarial tests mutate each descriptor field and the gate
list independently.

Each contract report contains exactly this envelope:

```text
schema_version = 1
report_kind = "cellpose_contract"
report_id
scope = "no-weight-no-download"
outcome = "PASS" | "FAIL"
generated_at_utc

product.commit_sha
product.pre_run_dirty = false
product.post_run_dirty = false
product.repository

provisioning.argv[]
provisioning.cwd_repo_relative
provisioning.environment{}
provisioning.executable_path
provisioning.executable_sha256
provisioning.provisioning_home
provisioning.provisioning_home_before_sha256
provisioning.provisioning_home_after_sha256
provisioning.provisioning_tmp
provisioning.provisioning_tmp_before_sha256
provisioning.provisioning_tmp_after_sha256

command.argv[]
command.cwd_repo_relative
command.environment{}
command.executable_path
command.executable_sha256

runner.path
runner.sha256
generator.path
generator.sha256

probe.path
probe.sha256
probe.contract_path
probe.contract_sha256

runtime.runtime_id = "cp4" | "cp3"
runtime.python_implementation
runtime.python_version
runtime.platform
runtime.machine
runtime.uv_version
runtime.sys_prefix
runtime.environment_root
runtime.site_packages_path
runtime.interpreter.lexical_path
runtime.interpreter.canonical_path
runtime.interpreter.sha256
runtime.interpreter.base_prefix
runtime.interpreter.base_prefix_python_path
runtime.interpreter.approved_managed_python_path
runtime.imported_cellpose_path
runtime.compatible_wheel_tags[]
runtime.user_site_enabled = false
runtime.repository_paths_on_sys_path[] = []

lock.path
lock.sha256
lock.python_constraint
lock.expected_cellpose_version
lock.artifact_candidates[]

installation.distributions[]
installation.cellpose.version
installation.cellpose.installation_policy
installation.cellpose.selected_artifact
installation.cellpose.metadata_sha256
installation.cellpose.normalized_record_sha256
installation.cellpose.normalized_installed_tree_sha256
installation.cellpose.source_file_hashes{}

upstream_source.repository = "https://github.com/MouseLand/cellpose"
upstream_source.declared_tag
upstream_source.declared_tag_commit
upstream_source.locked_pypi_artifacts[]

guards.network_attempt_count = 0
guards.network_attempts[] = []
guards.torch_load_count = 0
guards.torch_load_attempts[] = []
guards.torch_save_count = 0
guards.torch_save_attempts[] = []
guards.model_constructor_count = 0
guards.model_constructor_attempts[] = []
guards.process_spawn_count = 0
guards.process_spawn_attempts[] = []
guards.model_directory_before_sha256
guards.model_directory_after_sha256
guards.managed_root_hashes_before{}
guards.managed_root_hashes_after{}
guards.unapproved_filesystem_deltas[] = []
guards.ssl_context_unchanged = true

verification.required
verification.executed
verification.passed
verification.failed

checks[]
unresolved_real_model_gates[]
```

Each `checks[]` item contains exactly:

```text
id
category
evidence_kind
required
targets[].module
targets[].qualname
expected
observed
status = "PASS" | "FAIL"
sources[].path
sources[].sha256
sources[].lines[]
```

`expected` and `observed` are Pydantic `JsonValue`; the schema rejects NaN and
infinity before serialization. Each `SourceEvidence.lines` stores
one-based inclusive line numbers, never copied source text. Every
`SourceEvidence.path` and `SourceExpectation.path` is relative to the canonical
site-packages directory containing the selected distribution, is joined only
after `RelativePosixPath` validation, and must resolve back beneath that exact
directory; it is never relative to the repository, current directory, or
`cellpose/` package directory. A grouped check
may bind multiple ordered targets and multiple installed source files; every
source item has a package path, hash, and non-empty line list. A contract may
use an empty source tuple only for a runtime/synthetic observation with no
installed upstream source.

The stable-release report uses the same strict primitives and contains:

```text
schema_version = 1
report_kind = "stable_release_check"
report_id
scope = "official-metadata"
outcome = "PASS" | "FAIL"
generated_at_utc
product: ProductBinding
command: CommandBinding
script: ScriptBinding
sources[]
policy.cp4_required = "4.2.1.1"
policy.cp3_required = "3.1.1.3"
observed.latest_non_yanked_stable
observed.cp4_tag_commit
observed.cp3_tag_commit
observed.release_files_by_version{}
checks[]
```

`sources[]` items contain exact HTTPS URL, HTTP status `200`, response
SHA-256, and response byte count. Each
`observed.release_files_by_version[version]` item uses
`OfficialRegistryArtifact`; its own `version` equals the map key and its
`yanked` flag is copied from that exact PyPI file record. Stable checks contain
exactly `id`, `expected`, `observed`, `status`, `source_url`,
`source_response_sha256`, and `json_pointer`; they do not pretend to have
installed-package source lines.

The stable report passes only when the latest non-yanked stable Cellpose
release is exactly `4.2.1.1`, the two required releases exist with hashed
files, and official GitHub refs resolve to:

```text
v4.2.1.1 -> a54cb48849b7e225a81e8e43dcb042d42427f543
v3.1.1.3 -> e6eec1537501436c48a2c75d23f2aa61f8d715fd
```

Those commits are planning expectations, not hard-coded forever. A later
official observation that differs makes the report FAIL and forces a reviewed
stable-version decision.

The stable report contains this exact ordered check sequence:

```text
stable.pypi.latest_non_yanked_stable
stable.pypi.cp4_release_present
stable.pypi.cp3_release_present
stable.pypi.required_release_files_hashed
stable.github.cp4_tag_resolves_to_commit
stable.github.cp3_tag_resolves_to_commit
```

The PyPI source is the exact response from `/pypi/cellpose/json`.
`latest_non_yanked_stable` uses pointer `/releases`, CP4/CP3 release-presence
use `/releases/4.2.1.1` and `/releases/3.1.1.3`, and the aggregate
`required_release_files_hashed` check uses `json_pointer = null` because it
combines both release arrays. GitHub checks use `/object/sha` in their final
dereferenced tag responses. Every check binds the exact source URL and
response SHA-256. The verifier later adds the cross-report lock-artifact
comparison; it is not fabricated as an online check inside either offline
contract report.

## Required check IDs

### CP4 contract

`probes/upstream/cp4/contract.toml` declares this exact ordered sequence:

```text
cp4.import.version
cp4.models.model_names
cp4.models.cellpose_model_present
cp4.models.legacy_classes_absent
cp4.denoise.restoration_classes_absent
cp4.models.constructor_signature
cp4.models.legacy_constructor_args_ignored
cp4.models.pretrained_model_required
cp4.models.eval_signature
cp4.models.eval_return_arity
cp4.models.flow_return_arity
cp4.models.channels_ignored
cp4.models.caller_rescale_overwritten
cp4.models.diameter_none_native
cp4.models.diameter_zero_native
cp4.models.diameter_negative_native
cp4.models.diameter_positive_rescale
cp4.models.normalize_bool_mutates_default
cp4.models.normalize_dict_copies_default
cp4.models.known_names_reach_download
cp4.models.missing_path_falls_back_to_download
cp4.train.signature
cp4.train.return_and_save_layout
cp4.train.mutates_network_in_place
cp4.train.zero_epoch_false_success
cp4.train.no_cooperative_cancellation
cp4.metrics.signatures
cp4.io.export_signatures
cp4.io.pickle_dependent_segmentation_record
cp4.metrics.synthetic_identity
cp4.transforms.explicit_axes
```

The CP4 descriptors are frozen by the following exact matrix. `T(m, q)` means
one ordered `{module = m, qualname = q}` target. `S(p, lines)` means one
ordered `{path = p, lines = [...]}` source expectation. A hyphenated line
range is expanded inclusively into ascending integers in TOML. `S()` is
permitted only for the two runtime absence observations, where no positive
source construct exists and the complete installed tree hash still binds the
module. Every row has `required = true`; the category is the second dotted ID
component. Cells that say “printed below” inline that exact printed signature
or mapping as the TOML string/map value; the phrase is not contract data.

| ID | Evidence kind | Ordered targets | Exact TOML-native `expected` | Ordered sources |
| --- | --- | --- | --- | --- |
| `cp4.import.version` | `runtime_import` | `T("importlib.metadata", "version")`, `T("cellpose", "version")` | `{metadata_version = "4.2.1.1", module_version = "4.2.1.1"}` | `S("cellpose-4.2.1.1.dist-info/METADATA", 2-3)`, `S("cellpose/version.py", 4, 9-12)`, `S("cellpose/__init__.py", 1)` |
| `cp4.models.model_names` | `runtime_import` | `T("cellpose.models", "MODEL_NAMES")` | `["cpsam_v2", "cpdino", "cpdino-vitb", "cpsam"]` | `S("cellpose/models.py", 31)` |
| `cp4.models.cellpose_model_present` | `runtime_import` | `T("cellpose.models", "CellposeModel")` | `true` | `S("cellpose/models.py", 81)` |
| `cp4.models.legacy_classes_absent` | `runtime_import` | `T("cellpose.models", "Cellpose")`, `T("cellpose.models", "SizeModel")` | `{Cellpose = false, SizeModel = false}` | `S()` |
| `cp4.denoise.restoration_classes_absent` | `runtime_import` | `T("cellpose.denoise", "DenoiseModel")`, `T("cellpose.denoise", "CellposeDenoiseModel")` | `{DenoiseModel = false, CellposeDenoiseModel = false}` | `S()` |
| `cp4.models.constructor_signature` | `runtime_signature` | `T("cellpose.models", "CellposeModel.__init__")` | `"(self, gpu=False, pretrained_model='cpsam_v2', model_type=None, diam_mean=None, device=None, nchan=None, use_bfloat16=True)"` | `S("cellpose/models.py", 104-105)` |
| `cp4.models.legacy_constructor_args_ignored` | `static_ast` | `T("cellpose.models", "CellposeModel.__init__")` | `{diam_mean = "ignored_warning", model_type = "ignored_warning", nchan = "deprecated_ignored_warning"}` | `S("cellpose/models.py", 117-126)` |
| `cp4.models.pretrained_model_required` | `static_ast` | `T("cellpose.models", "CellposeModel.__init__")` | `{none = "ValueError", false = "ValueError", message = "Must specify a pretrained model, training from scratch is not implemented", before_network_creation = true}` | `S("cellpose/models.py", 138-140, 157-164)` |
| `cp4.models.eval_signature` | `runtime_signature` | `T("cellpose.models", "CellposeModel.eval")` | the exact `CellposeModel.eval` signature printed below | `S("cellpose/models.py", 167-172)` |
| `cp4.models.eval_return_arity` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `{arity = 3, items = ["masks", "flows", "styles"]}` | `S("cellpose/models.py", 329)` |
| `cp4.models.flow_return_arity` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `{arity = 3, items = ["circular_visualization", "vector_flow", "cell_probability"]}` | `S("cellpose/models.py", 327-329)` |
| `cp4.models.channels_ignored` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `{channels = ["None", "[2, 1]"], convert_records_equal = true, run_net_records_equal = true, outputs_equal = true}` | `S("cellpose/models.py", 224-225, 257-329)` |
| `cp4.models.caller_rescale_overwritten` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `{caller_rescale = 9.0, run_net_rescale = 1.0}` | `S("cellpose/models.py", 267-269, 295-298)` |
| `cp4.models.diameter_none_native` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `1.0` | `S("cellpose/models.py", 267-269, 295-298)` |
| `cp4.models.diameter_zero_native` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `1.0` | `S("cellpose/models.py", 267-269, 295-298)` |
| `cp4.models.diameter_negative_native` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `1.0` | `S("cellpose/models.py", 267-269, 295-298)` |
| `cp4.models.diameter_positive_rescale` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")` | `2.0` | `S("cellpose/models.py", 267-269, 295-298)` |
| `cp4.models.normalize_bool_mutates_default` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")`, `T("cellpose.models", "normalize_default")` | `{input = false, global_before = true, global_after = false, same_global_mapping = true}` | `S("cellpose/models.py", 35-45, 272, 275-278)` |
| `cp4.models.normalize_dict_copies_default` | `runtime_stubbed_upstream` | `T("cellpose.models", "CellposeModel.eval")`, `T("cellpose.models", "normalize_default")` | `{input = {invert = true, percentile = [2.0, 98.0]}, observed = {normalize = true, norm3D = true, invert = true, percentile = [2.0, 98.0]}, global_unchanged = true}` | `S("cellpose/models.py", 35-45, 272-274, 292-293)` |
| `cp4.models.known_names_reach_download` | `static_ast` | `T("cellpose.models", "MODEL_NAMES")`, `T("cellpose.models", "CellposeModel.__init__")`, `T("cellpose.models", "cache_model_path")` | `{names = ["cpsam_v2", "cpdino", "cpdino-vitb", "cpsam"], callee = "cache_model_path", download_if_cache_missing = true}` | `S("cellpose/models.py", 31, 48-54, 141-147)` |
| `cp4.models.missing_path_falls_back_to_download` | `static_ast` | `T("cellpose.models", "CellposeModel.__init__")`, `T("cellpose.models", "cache_model_path")` | `{callee = "cache_model_path", argument = "cpsam_v2", download_if_cache_missing = true}` | `S("cellpose/models.py", 48-54, 141-152)` |
| `cp4.train.signature` | `runtime_signature` | `T("cellpose.train", "train_seg")` | the exact `train.train_seg` signature printed below | `S("cellpose/train.py", 309-317)` |
| `cp4.train.return_and_save_layout` | `static_ast` | `T("cellpose.train", "train_seg")` | `{return_items = ["filename", "train_losses", "test_losses"], filename_expression = "Path(save_path) / \"models\" / model_name", train_losses_shape = ["n_epochs"], test_losses_shape = ["n_epochs"], final_save_unconditional = true}` | `S("cellpose/train.py", 431-440, 526-539)` |
| `cp4.train.mutates_network_in_place` | `static_ast` | `T("cellpose.train", "train_seg")` | `{optimizer = "torch.optim.AdamW", parameters = "net.parameters()", step = "optimizer.step()", network_rebound = false}` | `S("cellpose/train.py", 365-369, 399, 427-428, 472-474, 534-537)` |
| `cp4.train.zero_epoch_false_success` | `static_ast` | `T("cellpose.train", "train_seg")` | `{n_epochs = 0, epoch_iterations = 0, train_losses_shape = [0], test_losses_shape = [0], final_save_reachable = true, return_arity = 3}` | `S("cellpose/train.py", 439-440, 534, 539)` |
| `cp4.train.no_cooperative_cancellation` | `static_ast` | `T("cellpose.train", "train_seg")` | `{cancellation_parameters = [], epoch_loop_exit_nodes = []}` | `S("cellpose/train.py", 309-317, 440, 539)` |
| `cp4.metrics.signatures` | `runtime_signature` | `T("cellpose.metrics", "boundary_scores")`, `T("cellpose.metrics", "aggregated_jaccard_index")`, `T("cellpose.metrics", "average_precision")` | the exact three-signature mapping printed below | `S("cellpose/metrics.py", 24, 64, 88)` |
| `cp4.io.export_signatures` | `runtime_signature` | `T("cellpose.io", "masks_flows_to_seg")`, `T("cellpose.io", "save_rois")`, `T("cellpose.io", "save_masks")`, `T("cellpose.utils", "outlines_list")` | the exact four-signature mapping printed below | `S("cellpose/io.py", 601-603, 712, 746-748)`, `S("cellpose/utils.py", 216)` |
| `cp4.io.pickle_dependent_segmentation_record` | `static_ast` | `T("cellpose.io", "masks_flows_to_seg")`, `T("cellpose.io", "imread")` | `{suffix = "_seg.npy", writer = "np.save", payload = "dict", reader = "np.load", allow_pickle = true, item = true}` | `S("cellpose/io.py", 263-279, 678-701)` |
| `cp4.metrics.synthetic_identity` | `synthetic_pure` | `T("cellpose.metrics", "average_precision")`, `T("cellpose.metrics", "aggregated_jaccard_index")`, `T("cellpose.metrics", "boundary_scores")` | `{thresholds = [0.5, 0.75, 0.9], average_precision_shape = [1, 3], average_precision = [1.0, 1.0, 1.0], true_positives_shape = [1, 3], true_positives = [2.0, 2.0, 2.0], false_positives_shape = [1, 3], false_positives = [0.0, 0.0, 0.0], false_negatives_shape = [1, 3], false_negatives = [0.0, 0.0, 0.0], aggregated_jaccard_index_shape = [1], aggregated_jaccard_index = 1.0, scales = [1.0], boundary_precision_shape = [1, 1], boundary_precision = 1.0, boundary_recall_shape = [1, 1], boundary_recall = 1.0, boundary_fscore_shape = [1, 1], boundary_fscore = 1.0}` | `S("cellpose/metrics.py", 24-55, 64-85, 88-142)` |
| `cp4.transforms.explicit_axes` | `synthetic_pure` | `T("cellpose.transforms", "convert_image")`, `T("cellpose.transforms", "_convert_image_3d")` | `{output_dtype = "int32", yxc_shape = [2, 2, 3], yxc_values = [0, 100, 200, 1, 101, 201, 2, 102, 202, 3, 103, 203], zyxc_shape = [2, 2, 2, 3], zyxc_values = [0, 100, 200, 1, 101, 201, 2, 102, 202, 3, 103, 203, 10, 110, 210, 11, 111, 211, 12, 112, 212, 13, 113, 213]}` | `S("cellpose/transforms.py", 387-456, 459-532)` |

The `cp4.train.no_cooperative_cancellation` predicate is normative and finite:
the signature contains no cancellation-named parameter and the epoch-loop AST
subtree contains no `Break`, `Continue`, `Return`, or `Raise`. The
`cp4.train.zero_epoch_false_success` descriptor is only a static reachability
claim; it does not claim that an arbitrary real zero-epoch invocation succeeds.

The exact imported expectations are:

```text
importlib.metadata.version("cellpose") == "4.2.1.1"
cellpose.version == "4.2.1.1"
models.MODEL_NAMES == ["cpsam_v2", "cpdino", "cpdino-vitb", "cpsam"]
models.CellposeModel is present
models.Cellpose and models.SizeModel are absent
denoise.DenoiseModel and denoise.CellposeDenoiseModel are absent
```

The exact signatures, serialized with `str(inspect.signature(...))`, are:

```text
CellposeModel.__init__:
(self, gpu=False, pretrained_model='cpsam_v2', model_type=None, diam_mean=None, device=None, nchan=None, use_bfloat16=True)

CellposeModel.eval:
(self, x, batch_size=8, resample=True, channels=None, channel_axis=None, z_axis=None, normalize=True, rescale=None, diameter=None, flow_threshold=0.4, cellprob_threshold=0.0, do_3D=False, anisotropy=None, flow3D_smooth=0, stitch_threshold=0.0, min_size=15, max_size_fraction=0.4, niter=None, augment=False, tile_overlap=0.1, bsize=None, compute_masks=True, progress=None)

train.train_seg:
(net, train_data=None, train_labels=None, train_files=None, train_labels_files=None, train_probs=None, test_data=None, test_labels=None, test_files=None, test_labels_files=None, test_probs=None, channel_axis=None, load_files=True, batch_size=1, learning_rate=1e-05, SGD=False, n_epochs=100, weight_decay=0.1, normalize=True, compute_flows=False, save_path=None, save_every=100, save_each=False, nimg_per_epoch=None, nimg_test_per_epoch=None, rescale=False, scale_range=None, bsize=None, min_train_masks=5, model_name=None, class_weights=None)
```

The guarded stub calls `CellposeModel.eval` without a constructor and proves:

- the top-level return has three items `(masks, flows, styles)`;
- `flows` has three items: circular visualization, vector flow, and cell
  probability;
- changing `channels` does not change the stub inputs or result;
- a caller `rescale=9.0` is overwritten;
- `diameter=None`, `0`, and `-1` pass `rescale=1.0` to `_run_net`;
- `diameter=15` passes `rescale=2.0`;
- boolean normalization aliases and mutates module-global `normalize_default`;
  and
- dictionary normalization merges into a new mapping without changing the
  global mapping.

All CP4 stubbed-eval descriptors share this exact constructor-free fixture:

```python
x = np.array(
    [
        [[0.0, 10.0, 20.0], [1.0, 11.0, 21.0]],
        [[2.0, 12.0, 22.0], [3.0, 13.0, 23.0]],
    ],
    dtype=np.float32,
)
model = models.CellposeModel.__new__(models.CellposeModel)
model.backbone = "stub"
dP = np.array(
    [
        [[[1.0, 2.0], [3.0, 4.0]]],
        [[[5.0, 6.0], [7.0, 8.0]]],
    ],
    dtype=np.float32,
)
cellprob = np.array([[[9.0, 10.0], [11.0, 12.0]]], dtype=np.float32)
styles = np.array([13.0, 14.0, 15.0], dtype=np.float32)
stub_masks = np.array([[[0, 1], [2, 0]]], dtype=np.int32)
circular = np.array(
    [
        [[16.0, 17.0], [18.0, 19.0]],
        [[20.0, 21.0], [22.0, 23.0]],
        [[24.0, 25.0], [26.0, 27.0]],
    ],
    dtype=np.float32,
)
```

The `convert_image` stub records arguments and returns `x`; `_run_net`
records arguments and returns `(dP, cellprob, styles)`; `_compute_masks`
returns `stub_masks`; and `plot.dx_to_circ` returns `circular`. The canonical
result is masks `[[0, 1], [2, 0]]`, flows
`[circular, dP.squeeze(), cellprob.squeeze()]`, and styles
`[13.0, 14.0, 15.0]`. Each substituted callable and the exact contents and
identity of `normalize_default` are restored in `finally`.

Static AST checks prove all built-in names and a nonexistent arbitrary path
can reach `cache_model_path`; non-`None` `diam_mean`, `model_type`, and `nchan`
only emit ignored/deprecated warnings and none is read later by the
constructor; `pretrained_model is None or False` raises before network
creation; `train_seg` mutates the supplied network and saves even for
`n_epochs=0`; no cancellation parameter/check exists; and legacy `.npy`
segmentation records rely on pickle-capable NumPy loading. No download,
training loop, save, or pickle load is executed.

The CP4 training-layout check requires a three-item return
`(filename, train_losses, test_losses)`, `filename == Path(save_path) /
"models" / model_name`, both loss arrays have shape `(n_epochs,)`, and the
final `net.save_model(filename)` is unconditional after the epoch loop. The
signature checks require exactly:

```text
metrics.boundary_scores:
(masks_true, masks_pred, scales)

metrics.aggregated_jaccard_index:
(masks_true, masks_pred)

metrics.average_precision:
(masks_true, masks_pred, threshold=[0.5, 0.75, 0.9])

io.masks_flows_to_seg:
(images, masks, flows, file_names, channels=None, imgs_restore=None, restore_type=None, ratio=1.0)

io.save_rois:
(masks, file_name, multiprocessing=None, prefix='', pad=False)

io.save_masks:
(images, masks, flows, file_names, png=True, tif=False, channels=[0, 0], suffix='_cp_masks', save_flows=False, save_outlines=False, dir_above=False, in_folders=False, savedir=None, save_txt=False, save_mpl=False)

utils.outlines_list:
(masks, multiprocessing_threshold=50000, multiprocessing=None)
```

The synthetic identity fixture is:

```python
truth = np.array(
    [[0, 1, 1], [0, 0, 2], [0, 0, 2]],
    dtype=np.int32,
)
prediction = truth.copy()
thresholds = [0.5, 0.75, 0.9]
```

Call `metrics.average_precision([truth], [prediction],
threshold=thresholds)`, `metrics.aggregated_jaccard_index([truth],
[prediction])`, and `metrics.boundary_scores([truth], [prediction],
scales=[1.0])`. It requires average precision `[1.0, 1.0, 1.0]`, true positives
`[2.0, 2.0, 2.0]`, false positives and false negatives all zero,
aggregated Jaccard index `1.0`, and boundary precision/recall/F-score `1.0`
for scale `1.0`. The raw AP/TP/FP/FN arrays must have shape `(1, 3)`, AJI
shape `(1,)`, and each boundary array shape `(1, 1)`; the scalar/list values
above are taken from their sole row/item. The explicit-axis transform fixture
is exactly:

```python
yxc = np.array(
    [
        [[0, 100, 200], [1, 101, 201]],
        [[2, 102, 202], [3, 103, 203]],
    ],
    dtype=np.int32,
)
cyx = yxc.transpose(2, 0, 1)
yxc_observed = transforms.convert_image(
    cyx,
    channel_axis=0,
    z_axis=None,
    do_3D=False,
)

zyxc = np.array(
    [
        [
            [[0, 100, 200], [1, 101, 201]],
            [[2, 102, 202], [3, 103, 203]],
        ],
        [
            [[10, 110, 210], [11, 111, 211]],
            [[12, 112, 212], [13, 113, 213]],
        ],
    ],
    dtype=np.int32,
)
czyx = zyxc.transpose(3, 0, 1, 2)
zyxc_observed = transforms.convert_image(
    czyx,
    channel_axis=0,
    z_axis=1,
    do_3D=True,
)
```

For CP4, both returned arrays must remain `int32`; their shapes and C-order
flattened values are exactly those in the CP4 descriptor matrix. CP3 uses the
same inputs but its pinned implementation returns `float32`, as frozen in
`E_TRANSFORMS_CP3` below.

### CP3 contract

`probes/upstream/cp3/contract.toml` declares this exact ordered sequence:

```text
cp3.import.version
cp3.models.core_classes_present
cp3.denoise.restoration_classes_present
cp3.models.cellpose_signature
cp3.models.cellpose_eval_signature
cp3.models.cellpose_model_signature
cp3.models.cellpose_model_eval_signature
cp3.models.size_model_signature
cp3.models.size_model_eval_signature
cp3.denoise.constructor_signatures
cp3.denoise.eval_signatures
cp3.models.cellpose_eval_return_arity
cp3.denoise.combined_eval_return_arity
cp3.models.diameter_none_size_branch
cp3.models.diameter_zero_size_branch
cp3.denoise.required_base_model_names
cp3.denoise.channels_none_behavior
cp3.denoise.explicit_z_axis_behavior
cp3.download.all_model_name_paths
cp3.train.signature
cp3.train.return_and_save_layout
cp3.metrics.signatures
cp3.io.export_signatures
cp3.io.pickle_dependent_segmentation_record
cp3.metrics.synthetic_identity
cp3.transforms.explicit_axes
```

The CP3 descriptors use the same `T`/`S` notation and inclusive-range rule as
CP4. Symbolic expected-value names in this matrix refer to the exact normative
TOML values defined immediately after the signature/name sections below; they
are constants, not implementation placeholders.

| ID | Evidence kind | Ordered targets | Exact expected value | Ordered sources |
| --- | --- | --- | --- | --- |
| `cp3.import.version` | `runtime_import` | `T("importlib.metadata", "version")`, `T("cellpose", "version")` | `{distribution_version = "3.1.1.3", exported_version = "3.1.1.3"}` | `S("cellpose/version.py", 5, 10-13)`, `S("cellpose/__init__.py", 1)` |
| `cp3.models.core_classes_present` | `runtime_import` | `T("cellpose.models", "Cellpose")`, `T("cellpose.models", "CellposeModel")`, `T("cellpose.models", "SizeModel")` | `{Cellpose = true, CellposeModel = true, SizeModel = true}` | `S("cellpose/models.py", 96, 271, 650)` |
| `cp3.denoise.restoration_classes_present` | `runtime_import` | `T("cellpose.denoise", "DenoiseModel")`, `T("cellpose.denoise", "CellposeDenoiseModel")` | `{DenoiseModel = true, CellposeDenoiseModel = true}` | `S("cellpose/denoise.py", 494, 602)` |
| `cp3.models.cellpose_signature` | `runtime_signature` | `T("cellpose.models", "Cellpose.__init__")` | exact `Cellpose.__init__` signature below | `S("cellpose/models.py", 116-117)` |
| `cp3.models.cellpose_eval_signature` | `runtime_signature` | `T("cellpose.models", "Cellpose.eval")` | exact `Cellpose.eval` signature below | `S("cellpose/models.py", 150-151)` |
| `cp3.models.cellpose_model_signature` | `runtime_signature` | `T("cellpose.models", "CellposeModel.__init__")` | exact `CellposeModel.__init__` signature below | `S("cellpose/models.py", 297-299)` |
| `cp3.models.cellpose_model_eval_signature` | `runtime_signature` | `T("cellpose.models", "CellposeModel.eval")` | exact `CellposeModel.eval` signature below | `S("cellpose/models.py", 378-384)` |
| `cp3.models.size_model_signature` | `runtime_signature` | `T("cellpose.models", "SizeModel.__init__")` | exact `SizeModel.__init__` signature below | `S("cellpose/models.py", 673)` |
| `cp3.models.size_model_eval_signature` | `runtime_signature` | `T("cellpose.models", "SizeModel.eval")` | exact `SizeModel.eval` signature below | `S("cellpose/models.py", 698-699)` |
| `cp3.denoise.constructor_signatures` | `runtime_signature` | `T("cellpose.denoise", "DenoiseModel.__init__")`, `T("cellpose.denoise", "CellposeDenoiseModel.__init__")` | exact two-signature mapping below | `S("cellpose/denoise.py", 497-499, 634-635)` |
| `cp3.denoise.eval_signatures` | `runtime_signature` | `T("cellpose.denoise", "DenoiseModel.eval")`, `T("cellpose.denoise", "CellposeDenoiseModel.eval")` | exact two-signature mapping below | `S("cellpose/denoise.py", 506-510, 697-699)` |
| `cp3.models.cellpose_eval_return_arity` | `runtime_stubbed_upstream` | `T("cellpose.models", "Cellpose.eval")` | `{top_level_arity = 4, item_order = ["masks", "flows", "styles", "diameters"], passthrough_identity = [true, true, true], forwarded_diameter = 23.0, returned_diameter = 23.0}` | `S("cellpose/models.py", 150-151, 177-214)` |
| `cp3.denoise.combined_eval_return_arity` | `runtime_stubbed_upstream` | `T("cellpose.denoise", "CellposeDenoiseModel.eval")` | `{top_level_arity = 4, item_order = ["masks", "flows", "styles", "restored_image"], item_identity = [true, true, true, true], denoise_channels_none = true, denoise_channel_axis = 0, denoise_z_axis = 1, segmentation_channels_none = true, segmentation_channel_axis = -1, segmentation_z_axis = 0}` | `S("cellpose/denoise.py", 506-510, 572-599)` |
| `cp3.models.diameter_none_size_branch` | `runtime_stubbed_upstream` | `T("cellpose.models", "Cellpose.eval")` | `E_DIAMETER_NONE` | `S("cellpose/models.py", 177-214)` |
| `cp3.models.diameter_zero_size_branch` | `runtime_stubbed_upstream` | `T("cellpose.models", "Cellpose.eval")` | `E_DIAMETER_ZERO` | `S("cellpose/models.py", 177-214)` |
| `cp3.denoise.required_base_model_names` | `runtime_import` | `T("cellpose.denoise", "MODEL_NAMES")` | `RESTORE_BASE_12` | `S("cellpose/denoise.py", 24-32)` |
| `cp3.denoise.channels_none_behavior` | `runtime_stubbed_upstream` | `T("cellpose.denoise", "DenoiseModel.eval")` | `E_CHANNELS_NONE` | `S("cellpose/denoise.py", 697-699, 765-766, 790-814)` |
| `cp3.denoise.explicit_z_axis_behavior` | `runtime_stubbed_upstream` | `T("cellpose.denoise", "DenoiseModel.eval")`, `T("cellpose.transforms", "convert_image")` | `{caller_channel_axis = 0, caller_z_axis = 1, convert_channel_axis = 0, convert_z_axis = 1, convert_do_3D = true, convert_nchan_none = true}` | `S("cellpose/denoise.py", 697-699, 765-766)` |
| `cp3.download.all_model_name_paths` | `static_ast` | `T("cellpose.models", "MODEL_NAMES")`, `T("cellpose.models", "model_path")`, `T("cellpose.models", "size_model_path")`, `T("cellpose.models", "get_user_models")`, `T("cellpose.models", "get_model_params")`, `T("cellpose.models", "Cellpose.__init__")`, `T("cellpose.models", "CellposeModel.__init__")`, `T("cellpose.denoise", "MODEL_NAMES")`, `T("cellpose.denoise", "one_chan_cellpose")`, `T("cellpose.denoise", "DenoiseModel.__init__")`, `T("cellpose.denoise", "CellposeDenoiseModel.__init__")`, `T("cellpose.models", "cache_model_path")`, `T("cellpose.utils", "download_url_to_file")` | `E_DOWNLOAD` | `S("cellpose/models.py", 23-36, 51-93, 116-148, 216-268, 297-320)`, `S("cellpose/denoise.py", 22-32, 450-470, 497-504, 634-695)`, `S("cellpose/utils.py", 63-101)` |
| `cp3.train.signature` | `runtime_signature` | `T("cellpose.train", "train_seg")` | exact `train.train_seg` signature below | `S("cellpose/train.py", 329-337)` |
| `cp3.train.return_and_save_layout` | `static_ast` | `T("cellpose.train", "train_seg")` | `{return_arity = 3, return_order = ["filename", "train_losses", "test_losses"], filename_layout = ["save_path", "models", "model_name"], train_losses_shape = ["n_epochs"], test_losses_shape = ["n_epochs"], final_save_after_epoch_loop = true, final_save_unconditional = true}` | `S("cellpose/train.py", 449-459, 538-548)` |
| `cp3.metrics.signatures` | `runtime_signature` | `T("cellpose.metrics", "boundary_scores")`, `T("cellpose.metrics", "aggregated_jaccard_index")`, `T("cellpose.metrics", "average_precision")` | exact three-signature mapping below | `S("cellpose/metrics.py", 24, 58, 82)` |
| `cp3.io.export_signatures` | `runtime_signature` | `T("cellpose.io", "masks_flows_to_seg")`, `T("cellpose.io", "save_rois")`, `T("cellpose.io", "save_masks")`, `T("cellpose.utils", "outlines_list")` | exact four-signature mapping below | `S("cellpose/io.py", 474-475, 581, 607-609)`, `S("cellpose/utils.py", 217)` |
| `cp3.io.pickle_dependent_segmentation_record` | `static_ast` | `T("cellpose.io", "masks_flows_to_seg")`, `T("cellpose.io", "imread")`, `T("cellpose.gui.io", "_get_train_set")`, `T("cellpose.gui.io", "_load_seg")` | `{suffix = "_seg.npy", saved_value_kind = "dict", save_call = "numpy.save", writer_uses_pickle_default = true, load_call = "numpy.load", allow_pickle = true, item_called = true, reader_count = 3}` | `S("cellpose/io.py", 143, 203-219, 474-475, 547-570)`, `S("cellpose/gui/io.py", 73, 81-82, 262, 268)` |
| `cp3.metrics.synthetic_identity` | `synthetic_pure` | `T("cellpose.metrics", "average_precision")`, `T("cellpose.metrics", "aggregated_jaccard_index")`, `T("cellpose.metrics", "boundary_scores")` | the exact metric-identity mapping in the CP4 matrix | `S("cellpose/metrics.py", 24-55, 58-79, 82-136)` |
| `cp3.transforms.explicit_axes` | `synthetic_pure` | `T("cellpose.transforms", "convert_image")` | `E_TRANSFORMS_CP3` | `S("cellpose/transforms.py", 452-560)` |

The cached CP3 source inspected while writing this plan is byte-identical to
Git commit `e6eec1537501436c48a2c75d23f2aa61f8d715fd`, but the prior temporary
CP3 installation had already been pruned and could not support a fresh
`importlib.metadata.version` observation. Therefore `3.1.1.3` remains approved
contract data here; the newly provisioned, locked, offline CP3 probe in Task 4
is the authoritative runtime observation and must fail closed if it differs.

The exact imported expectations are:

```text
importlib.metadata.version("cellpose") == "3.1.1.3"
cellpose.version == "3.1.1.3"
models.Cellpose, models.CellposeModel, and models.SizeModel are present
denoise.DenoiseModel and denoise.CellposeDenoiseModel are present
```

The exact signatures are:

```text
Cellpose.__init__:
(self, gpu=False, model_type='cyto3', nchan=2, device=None, backbone='default')

Cellpose.eval:
(self, x, batch_size=8, channels=[0, 0], channel_axis=None, invert=False, normalize=True, diameter=30.0, do_3D=False, **kwargs)

CellposeModel.__init__:
(self, gpu=False, pretrained_model=False, model_type=None, mkldnn=True, diam_mean=30.0, device=None, nchan=2, pretrained_model_ortho=None, backbone='default')

CellposeModel.eval:
(self, x, batch_size=8, resample=True, channels=None, channel_axis=None, z_axis=None, normalize=True, invert=False, rescale=None, diameter=None, flow_threshold=0.4, cellprob_threshold=0.0, do_3D=False, anisotropy=None, flow3D_smooth=0, stitch_threshold=0.0, min_size=15, max_size_fraction=0.4, niter=None, augment=False, tile_overlap=0.1, bsize=224, interp=True, compute_masks=True, progress=None)

SizeModel.__init__:
(self, cp_model, device=None, pretrained_size=None, **kwargs)

SizeModel.eval:
(self, x, channels=None, channel_axis=None, normalize=True, invert=False, augment=False, batch_size=8, progress=None)

DenoiseModel.__init__:
(self, gpu=False, pretrained_model=False, nchan=1, model_type=None, chan2=False, diam_mean=30.0, device=None)

DenoiseModel.eval:
(self, x, batch_size=8, channels=None, channel_axis=None, z_axis=None, normalize=True, rescale=None, diameter=None, tile=True, do_3D=False, tile_overlap=0.1, bsize=224)

CellposeDenoiseModel.__init__:
(self, gpu=False, pretrained_model=False, model_type=None, restore_type='denoise_cyto3', nchan=2, chan2_restore=False, device=None)

CellposeDenoiseModel.eval:
(self, x, batch_size=8, channels=None, channel_axis=None, z_axis=None, normalize=True, rescale=None, diameter=None, tile_overlap=0.1, augment=False, resample=True, invert=False, flow_threshold=0.4, cellprob_threshold=0.0, do_3D=False, anisotropy=None, stitch_threshold=0.0, min_size=15, niter=None, interp=True, bsize=224, flow3D_smooth=0)

train.train_seg:
(net, train_data=None, train_labels=None, train_files=None, train_labels_files=None, train_probs=None, test_data=None, test_labels=None, test_files=None, test_labels_files=None, test_probs=None, load_files=True, batch_size=8, learning_rate=0.005, n_epochs=2000, weight_decay=1e-05, momentum=0.9, SGD=False, channels=None, channel_axis=None, rgb=False, normalize=True, compute_flows=False, save_path=None, save_every=100, save_each=False, nimg_per_epoch=None, nimg_test_per_epoch=None, rescale=True, scale_range=None, bsize=224, min_train_masks=5, model_name=None)
```

CP3 requires the same three-item training return, `save_path/models/model_name`
layout, `(n_epochs,)` loss arrays, and unconditional final save as CP4. Its
metric signatures are identical to CP4. Its export signatures are:

```text
io.masks_flows_to_seg:
(images, masks, flows, file_names, diams=30.0, channels=None, imgs_restore=None, restore_type=None, ratio=1.0)

io.save_rois:
(masks, file_name, multiprocessing=None)

io.save_masks:
(images, masks, flows, file_names, png=True, tif=False, channels=[0, 0], suffix='_cp_masks', save_flows=False, save_outlines=False, dir_above=False, in_folders=False, savedir=None, save_txt=False, save_mpl=False)

utils.outlines_list:
(masks, multiprocessing_threshold=1000, multiprocessing=None)
```

The exact required restoration-name subset is:

```text
denoise_cyto3 deblur_cyto3 upsample_cyto3 oneclick_cyto3
denoise_cyto2 deblur_cyto2 upsample_cyto2 oneclick_cyto2
denoise_nuclei deblur_nuclei upsample_nuclei oneclick_nuclei
```

The following CP3 constants are normative data definitions. The executor
serializes each referenced value as a TOML-native value inside its check; the
names themselves never appear in the contract.

```text
E_DIAMETER_NONE = {
  requested_diameter_none = true,
  top_level_arity = 4,
  size_eval_calls = 1,
  size_input_identity = true,
  size_channels = [0, 0],
  size_channel_axis_none = true,
  size_batch_size = 3,
  size_normalize = false,
  size_invert = true,
  segmentation_eval_calls = 1,
  segmentation_input_identity = true,
  segmentation_diameter = 17.25,
  returned_diameter = 17.25,
}

E_DIAMETER_ZERO = {
  requested_diameter = 0.0,
  top_level_arity = 4,
  size_eval_calls = 1,
  size_input_identity = true,
  size_channels = [0, 0],
  size_channel_axis_none = true,
  size_batch_size = 3,
  size_normalize = false,
  size_invert = true,
  segmentation_eval_calls = 1,
  segmentation_input_identity = true,
  segmentation_diameter = 17.25,
  returned_diameter = 17.25,
}

E_CHANNELS_NONE = {
  convert_channels_none = true,
  convert_nchan_none = true,
  converted_shape = [2, 2, 2, 2],
  channel_eval_calls = 2,
  channel_input_shapes = [[2, 2, 2, 1], [2, 2, 2, 1]],
  channel_rescales = [1.0, 1.7647058823529411],
  result_shape = [2, 2, 2, 2],
}

E_TRANSFORMS_CP3 = {
  output_dtype = "float32",
  yxc_shape = [2, 2, 3],
  yxc_values = [
    0.0, 100.0, 200.0, 1.0, 101.0, 201.0,
    2.0, 102.0, 202.0, 3.0, 103.0, 203.0,
  ],
  zyxc_shape = [2, 2, 2, 3],
  zyxc_values = [
    0.0, 100.0, 200.0, 1.0, 101.0, 201.0,
    2.0, 102.0, 202.0, 3.0, 103.0, 203.0,
    10.0, 110.0, 210.0, 11.0, 111.0, 211.0,
    12.0, 112.0, 212.0, 13.0, 113.0, 213.0,
  ],
}
```

The finite built-in general-model list is exactly 26 entries and deliberately
preserves the upstream duplicate `CPx`:

```text
MODEL_NAMES_26 = [
  "cyto3", "nuclei", "cyto2_cp3", "tissuenet_cp3", "livecell_cp3",
  "yeast_PhC_cp3", "yeast_BF_cp3", "bact_phase_cp3", "bact_fluor_cp3",
  "deepbacs_cp3", "cyto2", "cyto", "CPx", "transformer_cp3",
  "neurips_cellpose_default", "neurips_cellpose_transformer",
  "neurips_grayscale_cyto2", "CP", "CPx", "TN1", "TN2", "TN3",
  "LC1", "LC2", "LC3", "LC4",
]
```

The finite built-in restoration list is exactly:

```text
DENOISE_NAMES_38 = [
  "denoise_cyto3", "deblur_cyto3", "upsample_cyto3", "oneclick_cyto3",
  "denoise_cyto2", "denoise_per_cyto2", "denoise_seg_cyto2",
  "denoise_rec_cyto2", "deblur_cyto2", "deblur_per_cyto2",
  "deblur_seg_cyto2", "deblur_rec_cyto2", "upsample_cyto2",
  "upsample_per_cyto2", "upsample_seg_cyto2", "upsample_rec_cyto2",
  "oneclick_cyto2", "oneclick_per_cyto2", "oneclick_seg_cyto2",
  "oneclick_rec_cyto2", "aniso_cyto2", "denoise_nuclei",
  "denoise_per_nuclei", "denoise_seg_nuclei", "denoise_rec_nuclei",
  "deblur_nuclei", "deblur_per_nuclei", "deblur_seg_nuclei",
  "deblur_rec_nuclei", "upsample_nuclei", "upsample_per_nuclei",
  "upsample_seg_nuclei", "upsample_rec_nuclei", "oneclick_nuclei",
  "oneclick_per_nuclei", "oneclick_seg_nuclei", "oneclick_rec_nuclei",
  "aniso_nuclei",
]
```

`E_DOWNLOAD` is exactly:

```text
{
  builtin_model_names = MODEL_NAMES_26,
  builtin_model_name_count = 26,
  builtin_model_unique_count = 25,
  duplicate_builtin_model_names = ["CPx"],
  builtin_restoration_names = DENOISE_NAMES_38,
  builtin_restoration_name_count = 38,
  size_model_types = ["cyto", "nuclei", "cyto2", "cyto3"],
  direct_model_path_accepts_arbitrary_name = true,
  user_model_list_names_reach_download = true,
  one_chan_missing_pretrained_name_reaches_download = true,
  invalid_denoise_name_fallback = "denoise_cyto3",
  unknown_size_type_without_local_pair_downloads = false,
  cache_miss_calls_downloader = true,
  routes = [
    "cellpose.models.model_path->cellpose.models.cache_model_path->cellpose.utils.download_url_to_file",
    "cellpose.models.size_model_path->cellpose.models.cache_model_path->cellpose.utils.download_url_to_file",
    "cellpose.models.get_model_params[builtin_or_user]->cellpose.models.model_path->cellpose.models.cache_model_path",
    "cellpose.models.get_model_params[pretrained_model_ortho]->cellpose.models.model_path->cellpose.models.cache_model_path",
    "cellpose.models.get_model_params[missing_path_default]->cellpose.models.model_path->cellpose.models.cache_model_path",
    "cellpose.models.Cellpose.__init__->cellpose.models.size_model_path->cellpose.models.cache_model_path",
    "cellpose.models.Cellpose.__init__->cellpose.models.CellposeModel.__init__->cellpose.models.get_model_params",
    "cellpose.denoise.one_chan_cellpose->cellpose.models.model_path->cellpose.models.cache_model_path",
    "cellpose.denoise.DenoiseModel.__init__[primary]->cellpose.models.model_path->cellpose.models.cache_model_path",
    "cellpose.denoise.DenoiseModel.__init__[chan2]->cellpose.models.model_path->cellpose.models.cache_model_path",
    "cellpose.denoise.CellposeDenoiseModel.__init__->cellpose.denoise.DenoiseModel.__init__",
    "cellpose.denoise.CellposeDenoiseModel.__init__->cellpose.models.CellposeModel.__init__",
  ],
}
```

This download descriptor explicitly separates finite built-in names from the
open-ended domain accepted by `model_path`, user model-list entries, and
`one_chan_cellpose`; it never falsely calls the finite lists “all possible
names.” Static derivation also records: `cyto -> cytotorch_0`, `cyto2 ->
cyto2torch_0`, `nuclei -> nucleitorch_0`; all other general built-ins map to
themselves; size names map to `size_cytotorch_0.npy`,
`size_nucleitorch_0.npy`, `size_cyto2torch_0.npy`, and `size_cyto3.npy`; each
restoration name maps unchanged; and a second-channel restoration name is the
first underscore token plus `_nuclei`. These derived cache basenames are
source-inspection observations only and are not checkpoint filenames or local
paths stored in the public contract.

Additional upstream names may be recorded but cannot silently expand the
public product. `oneclick_*` remains unresolved until checkpoint-backed
evidence establishes its real semantics.

Guarded stubs prove `Cellpose.eval` returns four items, combined restoration
returns `(masks, flows, styles, restored_image)`, `diameter=None` and `0`
enter size-estimation control flow using a fake size-model recorder, and
`channels=None` preserves both denoise channels, while `channel_axis=0` and
`z_axis=1` reach `transforms.convert_image` unchanged. The combined wrapper
passes those caller axes to denoising, then passes `channel_axis=-1` and a
restored-array-derived `z_axis=0` to segmentation.
No real size, restoration, or segmentation network is invoked.

The CP3 fixtures are exact:

- `Cellpose.eval` arity: construct with `Cellpose.__new__`, use
  `x=np.arange(12,dtype=np.float32).reshape(3,4)`, make fake `cp.eval` return
  three distinct sentinels, and call with `batch_size=2`, `channels=[0,0]`,
  and `diameter=23.0`.
- Diameter branches: construct with `Cellpose.__new__`, use
  `x=[np.arange(12,dtype=np.float32).reshape(3,4)]`, set
  `pretrained_size="stub-size"`, return `(17.25,19.5)` from the fake size
  model, return three sentinels from fake segmentation, and call with
  `batch_size=3`, `channels=[0,0]`, `channel_axis=None`, `invert=True`,
  `normalize=False`, and `do_3D=False` for requested diameter `None` then
  `0.0`.
- Combined restoration: construct with `CellposeDenoiseModel.__new__`, use
  caller input `np.arange(24,dtype=np.float32).reshape(3,2,2,2)`, return the
  exact restored object
  `np.arange(16,dtype=np.float32).reshape(2,2,2,2)` from the fake denoiser,
  set `ratio=1.0` and `diam_mean=30.0`, and return distinct mask/flow/style
  sentinels from the fake segmenter. With caller `channels=None`,
  `channel_axis=0`, and `z_axis=1`, the denoiser receives those exact values;
  segmentation receives `channels=None`, `channel_axis=-1`, and recomputed
  `z_axis=0`.
- Denoise channel/axis behavior: construct with `DenoiseModel.__new__`, use
  CZYX input `np.arange(24,dtype=np.float32).reshape(3,2,2,2)`, make the fake
  converter return nonconstant ZYXC
  `np.arange(16,dtype=np.float32).reshape(2,2,2,2)`, set
  `pretrained_model="denoise_cyto3"`, `diam_mean=30.0`, `net` to a sentinel,
  and `net_chan2=None`; make fake `_eval` return its channel plus one. Call
  with `batch_size=5`, `channels=None`, `channel_axis=0`, `z_axis=1`,
  `normalize=False`, `rescale=None`, `diameter=None`, `do_3D=True`,
  `tile_overlap=0.2`, and `bsize=128`.

Every substituted global is restored in `finally`, including the exact
contents and identity of `normalize_default`.

CP3 uses the same pure identity metrics and explicit-axis fixtures as CP4.
Static AST enumerates every restoration/model-name path that can download and
records the training and pickle-dependent I/O surfaces without executing them.

## Unresolved real-model gates

Both reports contain this exact ordered list, with runtime-inapplicable entries
retained and labeled by runtime:

```text
checkpoint-source-license-size-authenticity-sha256
verified-local-path-model-construction
real-checkpoint-read
cp4-cpsam-v2-cpu-inference
cp4-cpsam-cpu-inference
cp4-mask-flow-style-shape-dtype-finiteness
cp4-scientific-correctness
cp4-batch-multichannel-3d-stitch-diameter-threshold-matrix
cp4-state-isolated-model-reuse
cp4-refinement-metrics-export-through-product
cp4-positive-step-training-parameter-change-finite-loss
cp4-saved-model-reopen-and-infer
real-worker-cancellation-cleanup-replacement-isolation
apple-silicon-mps-inference-and-training
cp4-dino-go-no-go
cp3-all-12-restoration-checkpoints
cp3-real-restored-image-and-restore-segment
installed-controller-mcp-user-journeys
```

No skip, xfail, xpass, deselection, source inspection, or stubbed execution can
remove an item from this list.

---

### Task 0: Verify the predecessor gate and preservation boundary

**Files:**

- Modify with explicit approval: `src/cellpose_mcp/__init__.py`
- Create: `tests/contract/upstream/test_release_import_isolation.py`

- [ ] **Step 1: Verify branch, clean index, and Phase 0 commits**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git diff --cached --quiet
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
EXPECTED_FOUNDATION_SUBJECTS=$'ci: enforce truthful repository foundation\ntest: make distribution proof offline\nfix: clarify inventory archive failures'
test "$(git log -3 --format=%s)" = "$EXPECTED_FOUNDATION_SUBJECTS"
```

Expected: the exact repository root and branch match, the index is empty,
`45021a21604328b268f75f09c4e026ae1cdabec2` is an ancestor, and `git log -3`
has the exact final ci/test/fix foundation subjects even though their future
commit hashes are not yet known. Existing working-tree changes are allowed and
remain inventoried.

- [ ] **Step 2: Consume the completed Phase 0 proof without reusing fresh paths**

Do not re-run Task 7 Step 1 of
`2026-07-16-cellpose-repository-foundation.md`: its clone, cache,
environments, HOME, and TMP paths are intentionally fresh-only and remain as
the completed Phase 0 evidence. Verify those exact artifacts offline instead:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(pwd -P)
test "$FOUNDATION_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
FOUNDATION_ACCEPTANCE_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_ACCEPTANCE_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_ACCEPTANCE_SHA:0:12}
FOUNDATION_ACCEPTANCE=/private/tmp/cellpose-mcp-foundation-acceptance-${FOUNDATION_RUN_SHA}
test -d "$FOUNDATION_ACCEPTANCE"
test "$(git -C "$FOUNDATION_ACCEPTANCE" rev-parse HEAD)" = "$FOUNDATION_ACCEPTANCE_SHA"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
FOUNDATION_ACCEPTANCE_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_ACCEPTANCE/uv.lock" | /usr/bin/awk '{print $1}')
test "$FOUNDATION_ACCEPTANCE_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
FOUNDATION_ACCEPTANCE_CACHE=/private/tmp/cellpose-mcp-foundation-acceptance-cache-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_311=/private/tmp/cellpose-mcp-foundation-acceptance-py311-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_312=/private/tmp/cellpose-mcp-foundation-acceptance-py312-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-foundation-acceptance-home-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-foundation-acceptance-tmp-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
test -d "$FOUNDATION_ACCEPTANCE_CACHE"
test -d "$FOUNDATION_ACCEPTANCE_HOME"
test -d "$FOUNDATION_ACCEPTANCE_TMP"
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$FOUNDATION_ACCEPTANCE_ENV_311/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11"
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_ACCEPTANCE_ENV_311/bin/python" | /usr/bin/awk '{print $1}')" = "e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5"
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
JUNIT_311="$FOUNDATION_ACCEPTANCE_TMP/foundation-60-py311.xml"
JUNIT_312="$FOUNDATION_ACCEPTANCE_TMP/foundation-60-py312.xml"
JUNIT_DISTRIBUTION="$FOUNDATION_ACCEPTANCE_TMP/foundation-distribution-19.xml"
/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I - "$JUNIT_311" "$JUNIT_312" "$JUNIT_DISTRIBUTION" <<'PY'
import sys
import xml.etree.ElementTree as ET

expected_tests = (60, 60, 19)
assert len(sys.argv[1:]) == len(expected_tests)
for path, expected in zip(sys.argv[1:], expected_tests, strict=True):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    actual = {
        key: sum(int(suite.get(key, "0")) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    assert actual == {
        "tests": expected,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }, (path, actual)
PY
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" -B -I -S -c 'from pathlib import Path; import importlib.util,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; repo=Path(sys.argv[1]).resolve(strict=True); env=Path(sys.executable).parent.parent; site=(env/"lib"/f"python{sys.version_info.major}.{sys.version_info.minor}"/"site-packages").resolve(strict=True); sys.path.insert(0,str(site)); forbidden=("cellpose","torch","fastmcp","cellpose_mcp","cellpose_mcp.server","cellpose_mcp.tools"); assert not any(name==item or name.startswith(item+".") for name in sys.modules for item in forbidden); module_path=(repo/"src/cellpose_mcp/release/feature_manifest.py").resolve(strict=True); spec=importlib.util.spec_from_file_location("phase0_feature_manifest",module_path); assert spec is not None and spec.loader is not None; module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module); failures=module.release_gate_failures(module.load_feature_manifest(repo/"src/cellpose_mcp/features.toml")); expected=(("unresolved_core_matrix",module.BOOTSTRAP_BLOCKER),)+tuple(("missing_stable_tool",tool) for tool in module.CORE_TOOLS); assert tuple((item.code,item.subject) for item in failures)==expected and len(failures)==14; assert not any(name==item or name.startswith(item+".") for name in sys.modules for item in forbidden)' "$FOUNDATION_ACCEPTANCE"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
```

Expected: the exact Phase 0 clone and its immutable lock remain clean; both
managed interpreter bindings match; the recorded focused suites contain
exactly 60/60 passing tests and the distribution suite exactly 19, with no
failure, error, or skip. The stdlib-first consumer inserts only the validated
foundation environment's site-packages, loads `feature_manifest.py` under a
standalone module name with `importlib.util.spec_from_file_location`, passes the
TOML path explicitly, verifies the exact ordered matrix blocker plus all 13
missing stable-tool identities, and proves before/after that `cellpose`, `torch`,
`fastmcp`, `cellpose_mcp`, `cellpose_mcp.server`, and `cellpose_mcp.tools` never
loaded. It therefore cannot execute the still-eager committed package
initializer. Missing or changed artifacts stop execution. Never delete or
recreate a Phase 0 path from this plan.

- [ ] **Step 3: Record probe prerequisites without importing Cellpose**

```bash
set -euo pipefail
PROBE_UV_SHA=$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv)
test "${PROBE_UV_SHA%% *}" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
PROBE_PY311_SHA=$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11)
test "${PROBE_PY311_SHA%% *}" = "e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --version 2>&1)" = "Python 3.11.14"
PROBE_PY312_SHA=$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12)
test "${PROBE_PY312_SHA%% *}" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
```

Expected: all three canonical executable paths, byte hashes, and full version
strings match exactly. Official tag currency is checked once, through the
hardened metadata command in Task 7; no extra Git endpoint is contacted.

- [ ] **Step 4: Verify the inventoried lazy-initializer hunk is unchanged**

```bash
set -euo pipefail
/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; assert hashlib.sha256(Path("src/cellpose_mcp/__init__.py").read_bytes()).hexdigest()=="445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50"'
/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'import json; from pathlib import Path; p=Path("local_archive/worktree-inventory-20260716T132515.517507Z.json"); d=json.loads(p.read_text()); e=next(item for item in d["entries"] if item["path"]=="src/cellpose_mcp/__init__.py"); assert e["worktree_sha256"]=="445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50"; assert e["index_sha256"]=="51eb1ed7ef10e977f588eae759ffb9d32741c716dffea31bc6f7b35c23a0b7a0"'
```

Expected: both assertions pass. A hash mismatch pauses this task for a new
exact-path review; do not overwrite the user's initializer.

- [ ] **Step 5: Obtain explicit approval to adopt that exact user hunk**

Present the diff and both hashes. The approved change removes the eager
`from cellpose_mcp.server import mcp` and adds a lazy `__getattr__` that imports
the server only when a caller explicitly asks for `mcp`. Do not stage it until
the user approves this exact adoption.

- [ ] **Step 6: Write the import-isolation test in a clean candidate clone**

Create
`tests/contract/upstream/test_release_import_isolation.py` with exactly:

```python
# ruff: noqa: S603

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]


def test_release_import_does_not_load_runtime_stack() -> None:
    source = """
import sys
from cellpose_mcp.release import feature_manifest

forbidden = (
    "cellpose",
    "torch",
    "fastmcp",
    "cellpose_mcp.server",
    "cellpose_mcp.tools",
)
loaded = sorted(
    name
    for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
)
if loaded:
    raise SystemExit("runtime imports leaked: " + ", ".join(loaded))
assert len(feature_manifest.CORE_TOOLS) == 13
"""
    environment = {**os.environ, "PYTHONNOUSERSITE": "1"}
    completed = subprocess.run(
        [sys.executable, "-B", "-I", "-c", source],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
```

Use a clean candidate clone so the dirty working initializer does not make RED
falsely green:

```bash
set -euo pipefail
IMPORT_CANDIDATE=/private/tmp/cellpose-mcp-import-candidate-$(git rev-parse --short=12 HEAD)
[[ $IMPORT_CANDIDATE =~ ^/private/tmp/cellpose-mcp-import-candidate-[0-9a-f]{12}$ ]]
export IMPORT_CANDIDATE
test ! -e "$IMPORT_CANDIDATE"
git clone --no-hardlinks --local . "$IMPORT_CANDIDATE"
```

Add only the new test to the candidate with `apply_patch`.

- [ ] **Step 7: Provision one controller environment under the approved dependency boundary**

This is the sole network-capable root/controller provisioning action. The
approval covers ordinary package-index artifacts required by the checked root
lock, not model hosts or weights.

```bash
set -euo pipefail
IMPORT_CANDIDATE=/private/tmp/cellpose-mcp-import-candidate-$(git rev-parse --short=12 HEAD)
[[ $IMPORT_CANDIDATE =~ ^/private/tmp/cellpose-mcp-import-candidate-[0-9a-f]{12}$ ]]
export IMPORT_CANDIDATE
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$IMPORT_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_DEV_ENV=/private/tmp/cellpose-mcp-probe-dev-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test ! -e "$PROBE_DEV_ENV"
test ! -e "$PROBE_UV_CACHE"
test ! -e "$PROBE_PACKAGE_HOME"
test ! -e "$PROBE_PACKAGE_TMP"
install -d -m 700 "$PROBE_UV_CACHE" "$PROBE_PACKAGE_HOME" "$PROBE_PACKAGE_TMP"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_PROJECT_ENVIRONMENT="$PROBE_DEV_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$IMPORT_CANDIDATE" sync --project "$IMPORT_CANDIDATE" --frozen --no-build --no-install-project --no-python-downloads --no-config --default-index https://pypi.org/simple --keyring-provider disabled --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev
PROBE_DEV_SITE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_DEV_ENV/bin/python" -B -I -c 'import site; paths=site.getsitepackages(); assert len(paths)==1; print(paths[0])')
[[ $PROBE_DEV_SITE == "$PROBE_DEV_ENV"/*/site-packages ]]
export PROBE_DEV_SITE
PROBE_DEV_PTH_SHA=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_DEV_ENV/bin/python" -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; target=Path(sys.argv[1]); payload=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.fchmod(fd,0o600); assert os.write(fd,payload)==len(payload); os.fsync(fd); os.close(fd); info=target.lstat(); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert target.read_bytes()==payload; print(hashlib.sha256(payload).hexdigest())' "$PROBE_DEV_SITE/cellpose_mcp_probe_source.pth" "$IMPORT_CANDIDATE/src")
[[ $PROBE_DEV_PTH_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_DEV_PTH_SHA
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_DEV_ENV/bin/python" -B -I -c 'from importlib.util import find_spec; from pathlib import Path; import sys; spec=find_spec("cellpose_mcp"); assert spec is not None and spec.origin is not None; root=Path(spec.origin).resolve(strict=True); expected=Path(sys.argv[1]).resolve(strict=True); assert root.is_relative_to(expected)' "$IMPORT_CANDIDATE/src"
```

Expected: dependency provisioning succeeds with exactly the displayed
environment and package-index authority limited to `https://pypi.org/simple`
and its PyPI-declared artifact host `files.pythonhosted.org`, with the keyring
disabled and no private index or inherited proxy, credential, config, custom
certificate variable, Cellpose model, or Hugging Face request. The local
project is not built or installed; the exact plain-path controller source
binding resolves imports beneath `IMPORT_CANDIDATE/src`. After this command,
all controller test commands through
Task 5 use this environment with `--frozen --offline --no-sync`.

- [ ] **Step 8: Run RED against the committed eager initializer**

```bash
set -euo pipefail
IMPORT_CANDIDATE=/private/tmp/cellpose-mcp-import-candidate-$(git rev-parse --short=12 HEAD)
[[ $IMPORT_CANDIDATE =~ ^/private/tmp/cellpose-mcp-import-candidate-[0-9a-f]{12}$ ]]
export IMPORT_CANDIDATE
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$IMPORT_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_DEV_ENV=/private/tmp/cellpose-mcp-probe-dev-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_DEV_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_DEV_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$IMPORT_CANDIDATE/src")
[[ $PROBE_DEV_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 1 "runtime imports leaked:" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_DEV_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$IMPORT_CANDIDATE" run --project "$IMPORT_CANDIDATE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_release_import_isolation.py -v
PROBE_DEV_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_DEV_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$IMPORT_CANDIDATE/src")
test "$PROBE_DEV_PTH_SHA_AFTER" = "$PROBE_DEV_PTH_SHA_BEFORE"
git -C "$IMPORT_CANDIDATE" diff --quiet -- src/cellpose_mcp/__init__.py
```

Expected: one failure whose subprocess reports imported legacy runtime modules.

- [ ] **Step 9: Apply the exact approved lazy initializer in the candidate**

The candidate `src/cellpose_mcp/__init__.py` must end with exactly:

```python
__version__ = "0.1.4"

__all__ = ["__version__", "mcp"]


def __getattr__(name: str):
    """Lazily expose the MCP server without importing Cellpose for CLI help."""
    if name == "mcp":
        from cellpose_mcp.server import mcp

        return mcp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

No other initializer bytes change.

- [ ] **Step 10: Run GREEN, verify the root copy, stage the exact adopted hunk, and commit**

```bash
set -euo pipefail
IMPORT_CANDIDATE=/private/tmp/cellpose-mcp-import-candidate-$(git rev-parse --short=12 HEAD)
[[ $IMPORT_CANDIDATE =~ ^/private/tmp/cellpose-mcp-import-candidate-[0-9a-f]{12}$ ]]
export IMPORT_CANDIDATE
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$IMPORT_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_DEV_ENV=/private/tmp/cellpose-mcp-probe-dev-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_DEV_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_DEV_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$IMPORT_CANDIDATE/src")
[[ $PROBE_DEV_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_DEV_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$IMPORT_CANDIDATE" run --project "$IMPORT_CANDIDATE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_release_import_isolation.py -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_DEV_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$IMPORT_CANDIDATE" run --project "$IMPORT_CANDIDATE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix src/cellpose_mcp/__init__.py tests/contract/upstream/test_release_import_isolation.py
PROBE_DEV_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_DEV_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$IMPORT_CANDIDATE/src")
test "$PROBE_DEV_PTH_SHA_AFTER" = "$PROBE_DEV_PTH_SHA_BEFORE"
/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; assert hashlib.sha256(Path("src/cellpose_mcp/__init__.py").read_bytes()).hexdigest()=="445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50"'
```

Add the same test to the root with `apply_patch`, provision a fresh root-bound
environment from the already populated cache, and verify the changed root
before staging:

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(src/cellpose_mcp/__init__.py tests/contract/upstream/test_release_import_isolation.py)
PROBE_COMMIT_SUBJECT="refactor: make package import lazy"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test ! -e "$PROBE_ROOT_ENV"
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" sync --project "$PROBE_ROOT" --frozen --offline --no-build --no-install-project --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev
PROBE_ROOT_SITE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_ROOT_ENV/bin/python" -B -I -c 'import site; paths=site.getsitepackages(); assert len(paths)==1; print(paths[0])')
[[ $PROBE_ROOT_SITE == "$PROBE_ROOT_ENV"/*/site-packages ]]
export PROBE_ROOT_SITE
PROBE_ROOT_PTH_SHA=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_ROOT_ENV/bin/python" -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; target=Path(sys.argv[1]); payload=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.fchmod(fd,0o600); assert os.write(fd,payload)==len(payload); os.fsync(fd); os.close(fd); info=target.lstat(); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert target.read_bytes()==payload; print(hashlib.sha256(payload).hexdigest())' "$PROBE_ROOT_SITE/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_ROOT_PTH_SHA
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_release_import_isolation.py tests/contract/test_feature_manifest.py tests/packaging/test_distribution_contents.py -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix src/cellpose_mcp/__init__.py tests/contract/upstream/test_release_import_isolation.py
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA"
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
test "$(/usr/bin/shasum -a 256 src/cellpose_mcp/__init__.py | /usr/bin/awk '{print $1}')" = "445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
test "$(git show :src/cellpose_mcp/__init__.py | /usr/bin/shasum -a 256 | /usr/bin/awk '{print $1}')" = "445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50"
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
test "$(git show HEAD:src/cellpose_mcp/__init__.py | /usr/bin/shasum -a 256 | /usr/bin/awk '{print $1}')" = "445bca24d4db191f102bc7f1b37f0c3c1f1d940b8da9bb951b81787f40b37b50"
git diff --cached --quiet
```

The same fence stages and commits only the two bound paths; do not run a
second staging or commit shell.

Expected: the approved user initializer is now represented exactly in history,
its working-tree diff disappears, the new test passes, and every unrelated
user change remains unstaged.

### Task 1: Add strict evidence records and canonical digests

**Files:**

- Create: `src/cellpose_mcp/release/upstream_evidence.py`
- Modify: `src/cellpose_mcp/release/__init__.py`
- Modify: `tests/packaging/test_distribution_contents.py`
- Create: `tests/contract/upstream/conftest.py`
- Create: `tests/contract/upstream/test_evidence_schema.py`

- [ ] **Step 1: Write RED schema tests**

The tests must cover:

```python
def test_unknown_field_is_rejected(valid_contract_document: dict[str, object]) -> None:
    valid_contract_document["invented"] = True
    with pytest.raises(ValidationError, match="extra_forbidden"):
        UpstreamContractReport.model_validate(valid_contract_document)


def test_canonical_json_is_stable(valid_contract_report: UpstreamContractReport) -> None:
    first = canonical_report_bytes(valid_contract_report)
    second = canonical_report_bytes(valid_contract_report)
    assert first == second
    assert first.endswith(b"\n")
    assert not first.endswith(b"\n\n")
    assert b": " not in first
    assert b", " not in first


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_json_is_rejected(
    valid_contract_document: dict[str, object],
    value: float,
) -> None:
    checks = valid_contract_document["checks"]
    assert isinstance(checks, list)
    check = checks[0]
    assert isinstance(check, dict)
    check["observed"] = value
    with pytest.raises(ValidationError, match="finite"):
        UpstreamContractReport.model_validate(valid_contract_document)


def test_digest_tampering_is_rejected(
    tmp_path: Path,
    valid_contract_report: UpstreamContractReport,
) -> None:
    report = tmp_path / "report.json"
    report.write_bytes(canonical_report_bytes(valid_contract_report))
    report.with_suffix(".json.sha256").write_text(
        f"{'0' * 64}  report.json\n",
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_report_digest(report)
```

Also reject bad hashes, non-UTC timestamps, absolute values in fields declared
repository-relative, `..` paths, duplicate check IDs, PASS with a failed required check, PASS with a
nonzero guard counter, changed SSL context, nonempty filesystem delta, changed
managed-root hash, mismatched required/executed totals, an empty unresolved
gate list, and a contract runtime/version mismatch.

Before any real lock exists, add synthetic lock-policy cases for
`validate_transitive_lock_sources`. Accept exactly one adjacent
`package=false` project record with `source = { virtual = "." }` and one
controller fixture whose selected project record is `{ editable = "." }`.
Require every dependency edge to resolve to a package record. Parameterized
mutations reject a missing/duplicate/wrong excluded project, a project-name or
version mismatch with `pyproject.toml`, virtual for a packaged controller,
editable for a `package=false` probe, artifacts on the excluded record, an
unknown dependency, Git/path/directory/workspace/URL/unknown sources anywhere,
non-PyPI registries, and artifact URLs with the wrong scheme, host, path,
userinfo, port, query, fragment, missing SHA-256, or non-positive size.

Add a packaging-policy RED test requiring the new module's exact two paths:

```python
def test_upstream_evidence_paths_are_allowlisted() -> None:
    assert "cellpose_mcp/release/upstream_evidence.py" in VALID_WHEEL_PATHS
    assert (
        "src/cellpose_mcp/release/upstream_evidence.py" in VALID_SDIST_PATHS
    )
```

- [ ] **Step 2: Run RED**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 2 "No module named 'cellpose_mcp.release.upstream_evidence'" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_evidence_schema.py tests/packaging/test_distribution_contents.py::test_upstream_evidence_paths_are_allowlisted -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/src/cellpose_mcp/release/upstream_evidence.py"
```

Expected: collection fails because `upstream_evidence` does not exist.

- [ ] **Step 3: Implement strict models and canonical serialization**

Use a discriminated union selected from raw `report_kind`. Serialize with:

```python
def canonical_report_bytes(
    report: UpstreamContractReport | StableReleaseCheckReport,
) -> bytes:
    payload = report.model_dump(mode="json")
    try:
        rendered = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except ValueError as exc:
        raise ValueError("report contains non-finite JSON") from exc
    return (rendered + "\n").encode("utf-8")


def report_sha256(
    report: UpstreamContractReport | StableReleaseCheckReport,
) -> str:
    return hashlib.sha256(canonical_report_bytes(report)).hexdigest()
```

`verify_report_digest` requires the exact two-space detached-digest format and
uses `hmac.compare_digest`. `load_upstream_report` rejects noncanonical bytes by
re-serializing the validated model and comparing them to the file bytes.

Implement `validate_transitive_lock_sources` in this module with only stdlib
TOML, URL, path, and hash helpers. It requires `excluded_project_name`, loads
the adjacent `pyproject.toml`, enforces the exact single local-project exception
and complete dependency closure defined in the mandatory lock gate, validates
every artifact of every registry record (not merely the selected wheel), and
returns the SHA-256 of the unchanged lock bytes. It performs no resolution,
network access, package import, or lock mutation.

In `release/__init__.py`, retain the existing eight names and their order:
`BOOTSTRAP_BLOCKER`, `CORE_TOOLS`, `BootstrapFeatureManifest`,
`FeatureBootstrapGateError`, `GateFailure`, `assert_release_ready`,
`load_feature_manifest`, and `release_gate_failures`. Then append
`StableReleaseCheckReport`, `UpstreamContractReport`,
`canonical_report_bytes`, `load_upstream_report`, `report_sha256`, and
`verify_report_digest` to imports and `__all__`. The import-isolation test must
still pass; no existing release name may disappear.

Append exactly `cellpose_mcp/release/upstream_evidence.py` to
`VALID_WHEEL_PATHS` and
`src/cellpose_mcp/release/upstream_evidence.py` to `VALID_SDIST_PATHS`. Do not
loosen either equality validator.

- [ ] **Step 4: Run GREEN, bind the tested bytes, and commit**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(src/cellpose_mcp/release/upstream_evidence.py src/cellpose_mcp/release/__init__.py tests/contract/upstream/conftest.py tests/contract/upstream/test_evidence_schema.py tests/packaging/test_distribution_contents.py)
PROBE_COMMIT_SUBJECT="feat: add strict upstream evidence records"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_evidence_schema.py -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_distribution_contents.py::test_upstream_evidence_paths_are_allowlisted -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix src/cellpose_mcp/release/upstream_evidence.py src/cellpose_mcp/release/__init__.py tests/contract/upstream/conftest.py tests/contract/upstream/test_evidence_schema.py
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev mypy src/cellpose_mcp/release/upstream_evidence.py
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
git diff --check
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

Expected: all commands exit 0.

- [ ] **Step 5: Verify the committed artifact set**

Run the complete `tests/packaging/test_distribution_contents.py` from the new
commit so its internal clean clone includes the module. Expected: all 20 tests
pass and the exact wheel/sdist sets contain the evidence module. Stop for a
corrective commit if this post-commit gate fails.

### Task 2: Add isolated probe projects and checked locks

**Files:**

- Create: `probes/upstream/cp4/pyproject.toml`
- Create: `probes/upstream/cp4/uv.lock`
- Create: `probes/upstream/cp3/pyproject.toml`
- Create: `probes/upstream/cp3/uv.lock`
- Create: `tests/contract/upstream/test_probe_projects.py`

- [ ] **Step 1: Write RED project-policy tests**

Tests parse both TOML files and require exact project names, versions, Python
ranges, exactly two direct dependencies, `package = false`, absent root/product
editable sources, absent model files, and absent locks before generation. Lock
tests require one exact Cellpose version, `packaging==26.2`, hashes on every
registry artifact, no Git/path source for either direct dependency, and
exactly one compatible Cellpose wheel for the selected
interpreter/platform tag set. They construct the full
`RegistryArtifact(version, filename, url, sha256, size)` identity and reject a
second compatible wheel, sdist selection, or a wheel without size/hash.
They walk every `[[package]]` record, including transitive-only fixtures, and
require the exact registry and file-URL grammar in the mandatory lock gate.
Parameterized mutations reject Git, arbitrary URL, path, directory, editable,
workspace, unknown source keys, a non-PyPI registry, and files URLs with a
wrong scheme/host/path prefix, userinfo, port, query, or fragment. The product
record exclusion is always required and exact: CP4 accepts only its one
`cellpose-mcp-cp4-contract-probe` virtual root, CP3 only its one
`cellpose-mcp-cp3-contract-probe` virtual root, and the controller fixture only
its one `cellpose-mcp` editable root. Every other local source is rejected.

Put these ordered existence tests first so both RED phases emit deterministic
sentinels instead of incidental file-open errors:

```python
def test_probe_project_files_exist() -> None:
    paths = (
        ROOT / "probes/upstream/cp4/pyproject.toml",
        ROOT / "probes/upstream/cp3/pyproject.toml",
    )
    assert all(path.is_file() for path in paths), "PROBE_PROJECT_FILES_MISSING"


def test_probe_lock_files_exist() -> None:
    paths = (
        ROOT / "probes/upstream/cp4/uv.lock",
        ROOT / "probes/upstream/cp3/uv.lock",
    )
    assert all(path.is_file() for path in paths), "PROBE_LOCK_FILES_MISSING"
```

```python
@pytest.mark.parametrize(
    ("runtime", "python_range", "cellpose"),
    [
        ("cp4", ">=3.12,<3.13", "cellpose==4.2.1.1"),
        ("cp3", ">=3.11,<3.12", "cellpose==3.1.1.3"),
    ],
)
def test_probe_project_is_private_and_exact(
    runtime: str,
    python_range: str,
    cellpose: str,
) -> None:
    document = tomllib.loads(
        (ROOT / "probes" / "upstream" / runtime / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )
    assert document["project"]["requires-python"] == python_range
    assert document["project"]["dependencies"] == [
        cellpose,
        "packaging==26.2",
    ]
    assert document["tool"]["uv"]["package"] is False
```

- [ ] **Step 2: Run RED before either project exists**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_ENV =~ ^/private/tmp/cellpose-mcp-probe-root-[0-9a-f]{64}$ ]]
export PROBE_ROOT_ENV
PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_UV_CACHE =~ ^/private/tmp/cellpose-mcp-probe-uv-cache-[0-9a-f]{64}$ ]]
export PROBE_UV_CACHE
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
PROBE_PACKAGE_HOME=${PROBE_ROOT_ENV/cellpose-mcp-probe-root-/cellpose-mcp-probe-package-home-}
[[ $PROBE_PACKAGE_HOME =~ ^/private/tmp/cellpose-mcp-probe-package-home-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME
PROBE_PACKAGE_TMP=${PROBE_ROOT_ENV/cellpose-mcp-probe-root-/cellpose-mcp-probe-package-tmp-}
[[ $PROBE_PACKAGE_TMP =~ ^/private/tmp/cellpose-mcp-probe-package-tmp-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_TMP
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 1 "PROBE_PROJECT_FILES_MISSING" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_probe_projects.py -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/probes/upstream/cp4/pyproject.toml"
test ! -e "$PROBE_ROOT/probes/upstream/cp4/uv.lock"
test ! -e "$PROBE_ROOT/probes/upstream/cp3/pyproject.toml"
test ! -e "$PROBE_ROOT/probes/upstream/cp3/uv.lock"
```

Expected: failure because both project files are absent.

- [ ] **Step 3: Create the exact private project files**

CP4:

```toml
[project]
name = "cellpose-mcp-cp4-contract-probe"
version = "0.0.0"
requires-python = ">=3.12,<3.13"
dependencies = ["cellpose==4.2.1.1", "packaging==26.2"]

[tool.uv]
package = false
```

CP3:

```toml
[project]
name = "cellpose-mcp-cp3-contract-probe"
version = "0.0.0"
requires-python = ">=3.11,<3.12"
dependencies = ["cellpose==3.1.1.3", "packaging==26.2"]

[tool.uv]
package = false
```

Run only `test_probe_project_is_private_and_exact` offline. Expected: both
parameter cases pass. Then prove the full-file lock RED explicitly:

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 1 "PROBE_LOCK_FILES_MISSING" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_probe_projects.py -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/probes/upstream/cp4/uv.lock"
test ! -e "$PROBE_ROOT/probes/upstream/cp3/uv.lock"
```

Expected: status 1 with the exact `PROBE_LOCK_FILES_MISSING` sentinel; both
lock destinations remain absent and the controller source binding is unchanged.

- [ ] **Step 4: Verify the single recorded dependency-network approval**

The pre-execution handoff asks once for the Task 0 controller sync, the two
`uv lock` commands, the two runtime syncs below, and a narrowly identified
cache-miss retry if required. Confirm that approval is recorded. It permits
ordinary package-index artifacts only; model constructors, model hosts, and
weights remain forbidden. Every authorized package command names only
`https://pypi.org/simple`, accepts only PyPI-declared artifacts from
`files.pythonhosted.org`, disables keyring lookup, and permits no private or
supplemental index. Do not ask piecemeal questions or continue on an ambiguous
answer.

- [ ] **Step 5: Generate locks with the exact managed interpreters**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_UV_CACHE =~ ^/private/tmp/cellpose-mcp-probe-uv-cache-[0-9a-f]{64}$ ]]
export PROBE_UV_CACHE
PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_PACKAGE_HOME =~ ^/private/tmp/cellpose-mcp-probe-package-home-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME
PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_PACKAGE_TMP =~ ^/private/tmp/cellpose-mcp-probe-package-tmp-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_TMP
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
test -x "$PROBE_ROOT_ENV/bin/python"
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$PROBE_ROOT_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_ROOT_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_ROOT_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_ROOT_PTH="$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_PTH" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
test ! -e "$PROBE_ROOT/probes/upstream/cp4/uv.lock"
test ! -e "$PROBE_ROOT/probes/upstream/cp3/uv.lock"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 | /usr/bin/awk '{print $1}')" = "e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --version 2>&1)" = "Python 3.11.14"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" lock --project "$PROBE_ROOT/probes/upstream/cp4" --no-build --no-python-downloads --no-config --default-index https://pypi.org/simple --keyring-provider disabled --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_ROOT_ENV/bin/python" -B -I -c 'from pathlib import Path; from cellpose_mcp.release.upstream_evidence import validate_transitive_lock_sources; validate_transitive_lock_sources(Path("probes/upstream/cp4/uv.lock"), excluded_project_name="cellpose-mcp-cp4-contract-probe")'
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" lock --project "$PROBE_ROOT/probes/upstream/cp3" --no-build --no-python-downloads --no-config --default-index https://pypi.org/simple --keyring-provider disabled --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_ROOT_ENV/bin/python" -B -I -c 'from pathlib import Path; from cellpose_mcp.release.upstream_evidence import validate_transitive_lock_sources; validate_transitive_lock_sources(Path("probes/upstream/cp3/uv.lock"), excluded_project_name="cellpose-mcp-cp3-contract-probe")'
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" lock --project "$PROBE_ROOT/probes/upstream/cp4" --check --offline --no-build --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" lock --project "$PROBE_ROOT/probes/upstream/cp3" --check --offline --no-build --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_PTH" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
```

Expected: all commands exit 0. Review the Cellpose records and confirm exact
versions and hashed release artifacts before provisioning.

- [ ] **Step 6: Provision dedicated environments, then revoke network use**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_UV_CACHE =~ ^/private/tmp/cellpose-mcp-probe-uv-cache-[0-9a-f]{64}$ ]]
export PROBE_UV_CACHE
CP4_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("probes/upstream/cp4/uv.lock").read_bytes()).hexdigest())')
[[ $CP4_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP4_LOCK_SHA
CP3_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("probes/upstream/cp3/uv.lock").read_bytes()).hexdigest())')
[[ $CP3_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP3_LOCK_SHA
export CP4_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp4-${CP4_LOCK_SHA}
export CP3_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp3-${CP3_LOCK_SHA}
PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_PACKAGE_HOME =~ ^/private/tmp/cellpose-mcp-probe-package-home-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME
PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_PACKAGE_TMP =~ ^/private/tmp/cellpose-mcp-probe-package-tmp-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_TMP
test ! -e "$CP4_PROBE_ENV"
test ! -e "$CP3_PROBE_ENV"
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
test -x "$PROBE_ROOT_ENV/bin/python"
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$PROBE_ROOT_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_ROOT_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" "$PROBE_ROOT_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_ROOT_PTH="$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_PTH" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 | /usr/bin/awk '{print $1}')" = "e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --version 2>&1)" = "Python 3.11.14"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_ROOT_ENV/bin/python" -B -I -c 'from pathlib import Path; from cellpose_mcp.release.upstream_evidence import validate_transitive_lock_sources; validate_transitive_lock_sources(Path("probes/upstream/cp4/uv.lock"), excluded_project_name="cellpose-mcp-cp4-contract-probe")'
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_PROJECT_ENVIRONMENT="$CP4_PROBE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" sync --project "$PROBE_ROOT/probes/upstream/cp4" --frozen --no-build --no-python-downloads --no-config --default-index https://pypi.org/simple --keyring-provider disabled --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_ROOT_ENV/bin/python" -B -I -c 'from pathlib import Path; from cellpose_mcp.release.upstream_evidence import validate_transitive_lock_sources; validate_transitive_lock_sources(Path("probes/upstream/cp3/uv.lock"), excluded_project_name="cellpose-mcp-cp3-contract-probe")'
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_PROJECT_ENVIRONMENT="$CP3_PROBE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" sync --project "$PROBE_ROOT/probes/upstream/cp3" --frozen --no-build --no-python-downloads --no-config --default-index https://pypi.org/simple --keyring-provider disabled --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$CP4_PROBE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT/probes/upstream/cp4" --frozen --offline --no-sync --no-python-downloads --no-config python -B -I -c 'import importlib.metadata; assert importlib.metadata.version("cellpose") == "4.2.1.1"'
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$CP3_PROBE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT/probes/upstream/cp3" --frozen --offline --no-sync --no-python-downloads --no-config python -B -I -c 'import importlib.metadata; assert importlib.metadata.version("cellpose") == "3.1.1.3"'
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_PTH" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
```

These commands inspect package metadata only; they do not import Cellpose.

- [ ] **Step 7: Run GREEN and commit locks**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(probes/upstream/cp4/pyproject.toml probes/upstream/cp4/uv.lock probes/upstream/cp3/pyproject.toml probes/upstream/cp3/uv.lock tests/contract/upstream/test_probe_projects.py)
PROBE_COMMIT_SUBJECT="build: add isolated Cellpose probe locks"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_ROOT_ENV
PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
PROBE_PACKAGE_HOME=${PROBE_ROOT_ENV/cellpose-mcp-probe-root-/cellpose-mcp-probe-package-home-}
[[ $PROBE_PACKAGE_HOME =~ ^/private/tmp/cellpose-mcp-probe-package-home-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME
PROBE_PACKAGE_TMP=${PROBE_ROOT_ENV/cellpose-mcp-probe-root-/cellpose-mcp-probe-package-tmp-}
[[ $PROBE_PACKAGE_TMP =~ ^/private/tmp/cellpose-mcp-probe-package-tmp-[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_TMP
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_probe_projects.py -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
git diff --check -- probes/upstream tests/contract/upstream/test_probe_projects.py
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

### Task 3: Build the guarded stdlib-first probe engine

**Files:**

- Create: `scripts/probe_cellpose_runtime.py`
- Create: `tests/contract/upstream/test_probe_engine.py`
- Modify: `tests/contract/upstream/conftest.py`

- [ ] **Step 1: Write RED subprocess fixtures**

Use temporary fake `cellpose` and `torch` packages so guard behavior is tested
without either real runtime. Required cases are safe import exit 0, signature
mismatch exit 2, high-level socket attempt exit 3, direct `_socket.socket`
creation/connect exit 3, `connect_ex`/`bind`/unconnected UDP `sendto`/`sendmsg`
exit 3, DNS `getaddrinfo`/`gethostbyname`/`gethostbyaddr`/`getnameinfo`
exit 3, `subprocess.Popen`, `os.system`, `os.posix_spawn`, `os.posix_spawnp`,
`os.exec*`, `os.fork`, and `os.forkpty` exit 3, downloader attempt exit 3,
constructor attempt exit 3, `torch.load` attempt exit 3, write outside scratch
exit 3, `torch.save` attempt exit 3, SSL-context replacement exit 3, retained
managed-cache delta exit 3, and malformed contract exit 4.

Put this deterministic existence test before fixture-dependent cases:

```python
def test_probe_executable_exists() -> None:
    assert (ROOT / "scripts/probe_cellpose_runtime.py").is_file(), (
        "PROBE_EXECUTABLE_MISSING"
    )
```

`tests/contract/upstream/conftest.py` defines the fixture interface exactly:

```python
@dataclass(frozen=True, slots=True)
class FakeProbe:
    root: Path
    script: Path
    contract: Path
    environment: Mapping[str, str]
    side_effect_marker: Path
    startup_hook_markers: tuple[Path, Path, Path]
    audit_order_marker: Path

    def run(self, scenario: str) -> subprocess.CompletedProcess[str]:
        """Run one scenario in a brand-new child with no inherited caller fds."""


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--forbid-nonpass-outcomes", action="store_true", default=False)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not session.config.getoption("--forbid-nonpass-outcomes"):
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    assert reporter is not None
    reports = [report for values in reporter.stats.values() for report in values]
    collected = len(session.items)
    executed = len({
        report.nodeid
        for report in reports
        if getattr(report, "when", None) == "call"
    })
    skipped = [report for report in reporter.stats.get("skipped", ())
               if not hasattr(report, "wasxfail")]
    xfailed = [report for report in reports
               if getattr(report, "outcome", None) == "skipped"
               and hasattr(report, "wasxfail")]
    xpassed = [report for report in reports
               if getattr(report, "outcome", None) == "passed"
               and hasattr(report, "wasxfail")]
    deselected = list(reporter.stats.get("deselected", ()))
    forbidden = {
        "skipped": len({report.nodeid for report in skipped}),
        "xfailed": len({report.nodeid for report in xfailed}),
        "xpassed": len({report.nodeid for report in xpassed}),
        "deselected": len({report.nodeid for report in deselected}),
    }
    reporter.write_line(
        f"probe execution proof: collected={collected} executed={executed} "
        f"nonpass={forbidden}"
    )
    if collected != executed or any(forbidden.values()):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
```

The final probe and clean-clone invocations pass
`--forbid-nonpass-outcomes`. The hook makes skip, xfail, xpass, or deselection
or a collected-versus-executed mismatch an exit-1 failure. It prints both
execution totals and the four machine-counted non-pass totals; prose inspection
of `-v` output is never the proof.

The fixture writes only beneath `tmp_path`. It creates a private fake runtime
root with a real `bin/python` lexical symlink to the already tested interpreter
and an exact `lib/pythonX.Y/site-packages` directory; fake `cellpose`, `torch`,
minimal `packaging`, and distribution metadata live only in that directory.
The fake Cellpose modules contain all five constructor targets and named
download helpers. The fixture writes a complete minimal contract and invokes
every scenario through the fake runtime's absolute Python symlink in a
brand-new child process with the exact `-B -I -S` flags. It also writes an
executable `.pth`, `sitecustomize.py`, and `usercustomize.py` into the fake
runtime site-packages, each of which would create its own startup marker if
executed. It rejects any existing marker; every
forbidden scenario attempts to create that allowed in-scratch marker only
after the candidate operation returns, while process-spawn scenarios make the
candidate child command itself create the marker. Thus every blocking test
also requires the marker to remain absent. No socket or process descriptor is
inherited from the pytest parent. For `connect`, `connect_ex`, `bind`, `sendto`,
and `sendmsg`, the stdlib-only audit-unit-test bootstrap inside that fresh child
creates exactly one loopback-only socket *before* installing the exact
production audit-hook callable, then invokes the selected method after hook
installation. This bootstrap is not reachable from production `main`, whose
hook is always installed before runtime imports or socket creation. The
`socket_new` case instead constructs its `_socket.socket` only after installing
the hook and proves `socket.__new__` is denied. `scenario` selects one fake
behavior from `safe`,
`signature_mismatch`, `network_attempt`, every exact
`NETWORK_AUDIT_SCENARIOS` and `PROCESS_AUDIT_SCENARIOS` value defined below,
`downloader_attempt`, each of the
five `constructor_attempt_*` values, `torch_load_attempt`,
`torch_save_attempt`, `ssl_context_change`, `managed_cache_delta`,
`outside_write_attempt`, or `malformed_contract`. Any other value raises
`ValueError` in the fixture rather than reaching the probe.

Every audit scenario expects exactly one deduplicated counter increment and
verifies absence of the attempted side effect: no network packet or accepted
connection, no DNS result, no marker file, no executed program, and no
surviving child. Any parent-side loopback observer is explicitly excluded by
`close_fds=True` and `pass_fds=()`; the probe child receives only its declared
stdin/stdout/stderr configuration. The named operation scenarios plus
`sys.audit("socket.future_test")` exercise the exact event handlers and the
future `socket.` prefix. Platform-missing operations are a hard fixture/setup
failure, not a skip or xfail, on the pinned macOS evidence platform.

```python
def test_network_attempt_is_a_guard_violation(fake_probe: FakeProbe) -> None:
    result = fake_probe.run("network_attempt")
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["guards"]["network_attempt_count"] == 1
    assert report["outcome"] == "FAIL"


def test_required_check_mismatch_is_contract_failure(fake_probe: FakeProbe) -> None:
    result = fake_probe.run("signature_mismatch")
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["verification"]["failed"] == 1
    assert report["guards"]["network_attempt_count"] == 0


def test_safe_probe_has_every_pass_guard_invariant(fake_probe: FakeProbe) -> None:
    result = fake_probe.run("safe")
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["outcome"] == "PASS"
    guards = report["guards"]
    for count_field, attempts_field in (
        ("network_attempt_count", "network_attempts"),
        ("torch_load_count", "torch_load_attempts"),
        ("torch_save_count", "torch_save_attempts"),
        ("model_constructor_count", "model_constructor_attempts"),
        ("process_spawn_count", "process_spawn_attempts"),
    ):
        assert guards[count_field] == 0
        assert guards[attempts_field] == []
    assert guards["model_directory_before_sha256"] == guards[
        "model_directory_after_sha256"
    ]
    assert guards["managed_root_hashes_before"] == guards[
        "managed_root_hashes_after"
    ]
    assert guards["unapproved_filesystem_deltas"] == []
    assert guards["ssl_context_unchanged"] is True


def test_no_startup_hook_precedes_the_probe_guard(fake_probe: FakeProbe) -> None:
    result = fake_probe.run("safe")
    assert result.returncode == 0
    assert all(not marker.exists() for marker in fake_probe.startup_hook_markers)
    assert fake_probe.audit_order_marker.read_text(encoding="utf-8") == (
        "audit-hook-installed\nfirst-site-packages-import\n"
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "constructor_attempt_cellpose_model",
        "constructor_attempt_cellpose",
        "constructor_attempt_size_model",
        "constructor_attempt_denoise_model",
        "constructor_attempt_cellpose_denoise_model",
    ],
)
def test_every_model_constructor_is_blocked(
    fake_probe: FakeProbe,
    scenario: str,
) -> None:
    result = fake_probe.run(scenario)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["guards"]["model_constructor_count"] == 1


NETWORK_AUDIT_SCENARIOS = (
    "socket_new",
    "direct__socket_connect",
    "socket_connect",
    "socket_connect_ex",
    "socket_bind",
    "udp_sendto",
    "socket_sendmsg",
    "dns_getaddrinfo",
    "dns_gethostbyname",
    "dns_gethostbyaddr",
    "dns_getnameinfo",
    "future_socket_prefix",
)

PROCESS_AUDIT_SCENARIOS = (
    "subprocess_popen",
    "os_system",
    "os_posix_spawn",
    "os_posix_spawnp",
    "os_exec",
    "os_fork",
    "os_forkpty",
)


@pytest.mark.parametrize("scenario", NETWORK_AUDIT_SCENARIOS)
def test_audit_hook_blocks_python_network_bypasses(
    fake_probe: FakeProbe,
    scenario: str,
) -> None:
    result = fake_probe.run(scenario)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["guards"]["network_attempt_count"] == 1
    assert not fake_probe.side_effect_marker.exists()


@pytest.mark.parametrize("scenario", PROCESS_AUDIT_SCENARIOS)
def test_audit_hook_blocks_process_spawn_bypasses(
    fake_probe: FakeProbe,
    scenario: str,
) -> None:
    result = fake_probe.run(scenario)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["guards"]["process_spawn_count"] == 1
    assert not fake_probe.side_effect_marker.exists()


@pytest.mark.parametrize(
    "scenario",
    ["torch_save_attempt", "ssl_context_change", "managed_cache_delta"],
)
def test_remaining_safety_guards_fail_closed(
    fake_probe: FakeProbe,
    scenario: str,
) -> None:
    result = fake_probe.run(scenario)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["outcome"] == "FAIL"
    guards = report["guards"]
    if scenario == "torch_save_attempt":
        assert guards["torch_save_count"] == 1
    elif scenario == "ssl_context_change":
        assert guards["ssl_context_unchanged"] is False
    else:
        assert guards["managed_root_hashes_before"] != guards[
            "managed_root_hashes_after"
        ]
```

- [ ] **Step 2: Run RED**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 1 "PROBE_EXECUTABLE_MISSING" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_probe_engine.py -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/scripts/probe_cellpose_runtime.py"
```

Expected: failure because the executable is absent.

- [ ] **Step 3: Install guards before importing runtime packages**

The probe imports only stdlib modules at file import time and is executable only
under the exact `-B -I -S` sequence. In `main`, it:

1. requires `sys.flags.dont_write_bytecode == 1`, `sys.flags.isolated == 1`,
   `sys.flags.no_site == 1`, `"site" not in sys.modules`, and exact
   `sys.orig_argv` flags/order before doing any contract or runtime import;
2. creates all guard counters and installs one `sys.addaudithook` before any
   environment path is added or any Torch, Cellpose, packaging, NumPy, or other
   runtime-package import;
3. derives the lexical environment root only as
   `Path(sys.executable).parent.parent`, derives its exact
   `lib/pythonX.Y/site-packages`, validates both as non-symlink directories and
   the latter as a child of that root, and inserts only that site-packages path
   into `sys.path` without importing `site`, calling `site.addsitedir`, or
   processing `.pth`/`sitecustomize`/`usercustomize`; it rejects any repository path on
   `sys.path` and verifies the imported Cellpose distribution is beneath that
   exact directory;
4. parses and validates the TOML contract;
5. snapshots `ssl._create_default_https_context` and all managed cache roots;
6. installs defense-in-depth socket/urllib wrappers and the constructor/load/
   save wrappers described below;
7. imports Torch, wraps `torch.load`, `torch.save`, and Torch hub download
   helpers with counting functions that raise `GuardViolation`;
8. imports Cellpose, captures original callable objects, signatures, source
   paths, and source hashes, then wraps every discovered Cellpose downloader
   and all five prohibited constructors that exist in that runtime;
9. executes only the check registry named by the contract; and
10. compares cache snapshots and SSL context before choosing the exit code.

The fixture launches every fake probe with `-B -I -S`. A startup-hook
adversarial case places an executable `.pth` plus `sitecustomize.py` and
`usercustomize.py` in the fake
runtime site-packages, each attempting to create a sentinel before the probe.
The safe probe must still pass, all three sentinels must remain absent, `site`
must remain absent through bootstrap and the first runtime import, and an audit-order marker must prove the hook
was installed before the first import whose origin is beneath site-packages.
Pure startup-contract tests pass missing/reordered flag tuples to the same
validator used by `main` and require exit `4` before a fake runtime import.
They do not launch a wrong-flag interpreter beside executable startup hooks:
without `-S`, CPython could execute those hooks before Python code can reject
the command. The enforceable boundary is instead the runner's closed,
non-overridable exact command tuple plus the real correct-`-S` sentinel test;
the plan makes no retroactive-safety claim for an unsupported manually altered
interpreter command.
`user_site_enabled = false` is derived from `sys.flags.no_user_site == 1`; the
probe never imports `site` merely to compute that field.

The core guard is:

```python
class GuardViolation(RuntimeError):
    """One forbidden probe side effect."""


def blocked_call(kind: str, attempts: list[dict[str, str]]):
    def blocked(*args: object, **kwargs: object) -> NoReturn:
        attempts.append(
            {
                "kind": kind,
                "args": repr(args),
                "kwargs": repr(sorted(kwargs)),
            }
        )
        raise GuardViolation(f"forbidden probe operation: {kind}")

    return blocked
```

The early audit hook counts and raises `GuardViolation` for every event whose
name starts with `socket.`. The exact four DNS cases under test are
`socket.getaddrinfo`, `socket.gethostbyname`, `socket.gethostbyaddr`, and
`socket.getnameinfo`; direct `_socket.socket.connect` and UDP `sendto` emit
the audited `socket.connect` and `socket.sendto` events. It separately counts
and rejects every event whose name starts with `subprocess.`, plus exact
`os.system`, `os.posix_spawn`, `os.exec`, `os.fork`, and `os.forkpty` events.
Register
defense-in-depth wrappers for `socket.socket.connect`,
`socket.socket.connect_ex`, `socket.create_connection`,
`urllib.request.urlopen`, Cellpose downloader aliases, Torch hub helpers,
`torch.load`, and `torch.save`. A single attempted operation is deduplicated by
guard kind and call token if both a wrapper and audit event observe it, so its
counter is exactly one. The same audit hook allows writes only beneath the
declared scratch/cache roots and records then rejects every other write-capable
`open`, `os.mkdir`, `os.rename`, `os.replace`, `os.remove`, `os.rmdir`, and
`os.symlink` event.

This boundary is deliberately stated as cooperative trusted-process
instrumentation. The tests prove only that the enumerated audited CPython
`_socket`, UDP, DNS, and process-spawn paths increment the report counters and
fail. CPython exposes no audit event for every possible operation: for example,
direct `_socket._accept`, I/O on an already-connected stream/UDP socket, and a
direct private `_posixsubprocess.fork_exec` call may emit no usable event. The
runner therefore launches the probe with `close_fds=True`, `pass_fds=()`, and
`stdin=subprocess.DEVNULL`, inheriting no caller network descriptor; only its
declared stdout/stderr protocol pipes remain. The plan does not claim
containment of malicious native code, `ctypes`, private C APIs, kernel exploits,
or a hostile binary dependency, and no OS sandbox is required.

The five constructor targets are `models.CellposeModel`, `models.Cellpose`,
`models.SizeModel`, `denoise.DenoiseModel`, and
`denoise.CellposeDenoiseModel`. Absence is expected only where the selected
contract says so. Capture each present class's original `__init__` callable
and `str(inspect.signature(original_init))` before replacement. Signature
checks read only that immutable capture; they never inspect a wrapper. Tests
parameterize all five targets and assert wrapping does not change the captured
observation. Guarded stubs use `Class.__new__(Class)` and never call a wrapped
initializer.

- [ ] **Step 4: Implement deterministic source and synthetic utilities**

- `hash_managed_tree(root)` requires an absolute directory for which
  `root == root.resolve(strict=True)` and whose own `lstat` is a directory, then walks
  it without following symlinks. The probe owns a stdlib-only implementation;
  the controller runner owns an identical private implementation because the
  runner cannot import the copied probe. Both consume the same normative test
  vectors. Each emits one record for every descendant, ordered by the raw
  UTF-8 bytes of its relative POSIX path: directories use
  `{path, kind="directory"}`, regular files use
  `{path, kind="file", size, sha256}`, and symlinks use
  `{path, kind="symlink", target}` where `target` is the exact lexical
  `os.readlink` string. Paths are relative to `root`, never `.` or absolute,
  and must satisfy a stdlib-only `validate_relative_posix_path` predicate whose
  accepted/rejected vectors are identical to the controller's
  `RelativePosixPath`; the copied probe never imports Pydantic. Sockets,
  devices, FIFOs,
  undecodable paths, and a file changed between pre/open/post identity checks
  are fatal. Regular files are opened with no-follow semantics and their
  `(st_dev, st_ino, st_mode, st_size, st_mtime_ns)` values must agree across
  the initial `lstat`, both `fstat` calls around hashing, and final `lstat`.
  File mode, owner, mtime, inode, and symlink-target contents are not followed
  or hashed. The tree digest is SHA-256 over
  `json.dumps(records, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"`; an empty
  tree therefore hashes canonical `[]\n`. Tests create equal trees in opposite
  creation orders and with different mtimes/modes, then prove identical
  digests; a cross-implementation test requires both functions to return the
  same digest for every vector. Separate tests prove that changing a relative path, kind, file byte,
  file size, or lexical symlink target changes the digest, that an external
  symlink target is never read, and that special/racing files fail closed.
- `inspect.signature` produces signature observations.
- `packaging.tags.sys_tags()` in the isolated runtime emits the ordered
  compatible tag strings used by the controller to choose the one lock wheel.
- `inspect.getsourcefile` plus AST produces exact call/branch observations and
  one-based line numbers.
- Source hashes are calculated from installed package files. Each source path
  is first made relative to the selected distribution's canonical
  site-packages directory; reconstruction must resolve beneath that directory
  before hashing. A path relative to the repository or merely to `cellpose/`
  is malformed-contract exit `4`.
- Parse `RECORD` as CSV and first verify every row with a digest/size against
  the raw installed file. Reject unsupported hash algorithms, missing files,
  duplicate paths, malformed sizes, or unrecorded non-cache files beneath the
  installed `cellpose` package.
- Determine console scripts only from the installed distribution's
  `entry_points.txt`. A RECORD path outside site-packages may be normalized
  only when it is exactly `../../../bin/<declared-console-script>`. Its first
  line must be an absolute shebang beneath `runtime.environment_root` and is replaced
  with the literal `#!<ENV>/bin/python\n`; all remaining bytes are unchanged.
  Any other environment-external path or embedded environment prefix is a
  contract failure.
- Build `normalized_record_sha256` from compact sorted canonical JSON rows
  `{path,sha256,size}` after that console-script normalization, excluding
  `.pyc` rows and representing RECORD's self-row as null hash/size. Build
  `normalized_installed_tree_sha256` from sorted `path`, normalized byte
  length, and normalized bytes for the same rows except RECORD itself. Do not
  hash filesystem mode, absolute prefix, mtime, inode, or raw RECORD bytes.
- Parse compatible wheel tags for the selected interpreter. Require exactly
  one compatible Cellpose wheel in the lock, require its version to match the
  runtime, and record it as `selected_artifact`. Every provisioning command
  uses `uv sync --frozen --offline --no-build --no-python-downloads
  --no-config`, making the policy
  `uv-frozen-offline-no-build-no-python-downloads-no-config-unique-compatible-wheel`;
  a compatible-wheel count other
  than one fails closed.
- Tests build two synthetic installations with different absolute environment
  lengths and shebangs. Their raw scripts and raw RECORD SHA-256 values must
  differ, while both normalized hashes and selected-artifact identities must
  match. A changed post-shebang byte must change both normalized hashes.
- Synthetic output may be written only beneath `scratch/synthetic-output` and
  is removed before final filesystem comparison.
- A check registry maps every contract ID to one function; unknown or duplicate
  IDs are malformed-contract exit 4.

- [ ] **Step 5: Run GREEN, bind the tested bytes, and commit**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(scripts/probe_cellpose_runtime.py tests/contract/upstream/conftest.py tests/contract/upstream/test_probe_engine.py)
PROBE_COMMIT_SUBJECT="feat: add guarded Cellpose contract probe"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_probe_engine.py -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix scripts/probe_cellpose_runtime.py tests/contract/upstream/conftest.py tests/contract/upstream/test_probe_engine.py
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev mypy scripts/probe_cellpose_runtime.py
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
git diff --check
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

Expected: all tests and static checks pass.

- [ ] **Step 6: Verify the guarded-engine commit boundary**

Review the commit produced by Step 5; do not create a second commit.

### Task 4: Encode and test both pinned runtime contracts

**Files:**

- Create: `probes/upstream/cp4/contract.toml`
- Create: `probes/upstream/cp3/contract.toml`
- Create: `tests/contract/upstream/test_cp4_expectations.py`
- Create: `tests/contract/upstream/test_cp3_expectations.py`

- [ ] **Step 1: Write RED completeness tests first**

Define the ordered check-ID tuples in the test modules and require exact
equality with each contract, exact signatures above, exact CP4 model names,
the exact CP3 12-name subset, unique IDs, valid evidence kinds, source/hash
requirements, and the complete unresolved gate list.

Put this deterministic pair-existence test before either loader is called:

```python
def test_contract_files_exist() -> None:
    paths = (
        ROOT / "probes/upstream/cp4/contract.toml",
        ROOT / "probes/upstream/cp3/contract.toml",
    )
    assert all(path.is_file() for path in paths), "PROBE_CONTRACT_FILES_MISSING"
```

Both test modules use this exact loader:

```python
ROOT = Path(__file__).parents[3]


def load_contract(runtime: Literal["cp4", "cp3"]) -> dict[str, object]:
    path = ROOT / "probes" / "upstream" / runtime / "contract.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


def check_by_id(contract: dict[str, object], check_id: str) -> dict[str, object]:
    matches = [check for check in contract["checks"] if check["id"] == check_id]
    assert len(matches) == 1
    return matches[0]
```

```python
def test_cp4_contract_has_exact_required_check_order() -> None:
    contract = load_contract("cp4")
    assert tuple(contract["runtime"]["required_check_ids"]) == CP4_CHECK_IDS


def test_cp4_ignored_constructor_inputs_are_read_from_the_exact_descriptor() -> None:
    contract = load_contract("cp4")
    descriptor = check_by_id(contract, "cp4.models.legacy_constructor_args_ignored")
    assert descriptor["expected"] == {
        "diam_mean": "ignored_warning",
        "model_type": "ignored_warning",
        "nchan": "deprecated_ignored_warning",
    }


def test_cp3_restoration_subset_is_read_from_the_exact_descriptor() -> None:
    contract = load_contract("cp3")
    descriptor = check_by_id(contract, "cp3.denoise.required_base_model_names")
    assert tuple(descriptor["expected"]) == (
        "denoise_cyto3",
        "deblur_cyto3",
        "upsample_cyto3",
        "oneclick_cyto3",
        "denoise_cyto2",
        "deblur_cyto2",
        "upsample_cyto2",
        "oneclick_cyto2",
        "denoise_nuclei",
        "deblur_nuclei",
        "upsample_nuclei",
        "oneclick_nuclei",
    )
```

- [ ] **Step 2: Run RED**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 1 "PROBE_CONTRACT_FILES_MISSING" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_cp4_expectations.py tests/contract/upstream/test_cp3_expectations.py -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/probes/upstream/cp4/contract.toml"
test ! -e "$PROBE_ROOT/probes/upstream/cp3/contract.toml"
```

Expected: missing-contract failures.

- [ ] **Step 3: Write declarative contracts**

Each contract contains exactly `[runtime]`, `[upstream]`, and `[[checks]]`
sections. Every expected value has one authoritative location: the descriptor
for its exact check ID. The runtime
section pins ID, Python constraint,
Cellpose version, scope, exact required-check list, and the exact unresolved
gate string list from this plan. The upstream tables are exactly:

```toml
# CP4
[upstream]
repository = "https://github.com/MouseLand/cellpose"
tag = "v4.2.1.1"
tag_commit = "a54cb48849b7e225a81e8e43dcb042d42427f543"

# CP3
[upstream]
repository = "https://github.com/MouseLand/cellpose"
tag = "v3.1.1.3"
tag_commit = "e6eec1537501436c48a2c75d23f2aa61f8d715fd"
```

These appear in separate files; the comments only distinguish the two exact
tables. Each `[[checks]]` item records exactly `id`, `category`,
`evidence_kind`, `required = true`, an ordered `targets` array, TOML-native
`expected`, and an ordered `sources` array. Each target inline table contains
exactly `module` and `qualname`; each source inline table contains exactly
`path` and the expanded ascending integer `lines`. Only the two CP4 absence
descriptors have empty sources. The stdlib parser rejects any unknown key or missing item before
imports. Logical model IDs such
as `cpsam_v2` and `denoise_cyto3` are required contract data; checkpoint
filenames, local checkpoint paths, weight URLs, and executable source are
forbidden. Completeness tests locate every expectation through `check_by_id`,
require exactly one descriptor for that ID, and never maintain a second
expectation copy outside `[[checks]]`.

For every required ID, the registry function name is exactly
`check_` plus the ID with dots replaced by underscores. The contract's
`category` is the second dotted component and `required = true`. Its ordered
targets identify every callable or module-level property used by that check,
and the source expectations are exactly those in the descriptor matrices.
Evidence-kind assignment is exact:

- version, symbol presence, class absence, and model-name enumeration use
  `runtime_import`;
- every `*.signature` or `*.signatures` check uses `runtime_signature`;
- eval arity, argument forwarding, diameter, normalization, and combined
  restoration behavior use `runtime_stubbed_upstream`;
- download reachability, constructor branches, training layout/mutation/
  cancellation, and pickle-dependent record checks use `static_ast`;
- metric identity and transform-axis checks use `synthetic_pure`.

The tests require this mapping exactly, so a registry function cannot silently
substitute source inspection for a runtime signature or stubbed behavior.

- [ ] **Step 4: Implement every check registry function**

Add the CP4 and CP3 functions to `scripts/probe_cellpose_runtime.py`. Stub
fixtures replace transforms, `_run_net`, `_compute_masks`, fake size model,
fake restoration model, and fake segmentation model. Every fixture restores
the original module globals in `finally`, including CP4's mutable
`normalize_default`.

The CP4 diameter fixture calls the same unbound eval four times and records:

```python
{
    "none": 1.0,
    "zero": 1.0,
    "negative": 1.0,
    "positive_15": 2.0,
}
```

The CP3 combined stub records top-level arity four and verifies the fourth
item is the exact fake restored-array object returned by the fake denoiser.

- [ ] **Step 5: Run both real pinned probes offline to temporary stdout**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_RUN_SHA=$(git rev-parse --short=12 HEAD)
[[ $PROBE_RUN_SHA =~ ^[0-9a-f]{12}$ ]]
export PROBE_RUN_SHA
PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_UV_CACHE =~ ^/private/tmp/cellpose-mcp-probe-uv-cache-[0-9a-f]{64}$ ]]
export PROBE_UV_CACHE
CP4_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("probes/upstream/cp4/uv.lock").read_bytes()).hexdigest())')
[[ $CP4_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP4_LOCK_SHA
CP3_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("probes/upstream/cp3/uv.lock").read_bytes()).hexdigest())')
[[ $CP3_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP3_LOCK_SHA
export CP4_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp4-${CP4_LOCK_SHA}
export CP3_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp3-${CP3_LOCK_SHA}
export CP4_SCRATCH=/private/tmp/cellpose-mcp-probe-cp4-smoke-${PROBE_RUN_SHA}-${CP4_LOCK_SHA}
export CP3_SCRATCH=/private/tmp/cellpose-mcp-probe-cp3-smoke-${PROBE_RUN_SHA}-${CP3_LOCK_SHA}
test ! -e "$CP4_SCRATCH"
test ! -e "$CP3_SCRATCH"
install -d -m 700 "$CP4_SCRATCH" "$CP4_SCRATCH/home" "$CP4_SCRATCH/models" "$CP4_SCRATCH/torch" "$CP4_SCRATCH/xdg" "$CP4_SCRATCH/mpl" "$CP4_SCRATCH/numba" "$CP4_SCRATCH/tmp"
install -d -m 700 "$CP3_SCRATCH" "$CP3_SCRATCH/home" "$CP3_SCRATCH/models" "$CP3_SCRATCH/torch" "$CP3_SCRATCH/xdg" "$CP3_SCRATCH/mpl" "$CP3_SCRATCH/numba" "$CP3_SCRATCH/tmp"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$CP4_SCRATCH/home" CELLPOSE_LOCAL_MODELS_PATH="$CP4_SCRATCH/models" TORCH_HOME="$CP4_SCRATCH/torch" XDG_CACHE_HOME="$CP4_SCRATCH/xdg" MPLCONFIGDIR="$CP4_SCRATCH/mpl" NUMBA_CACHE_DIR="$CP4_SCRATCH/numba" TMPDIR="$CP4_SCRATCH/tmp" UV_CACHE_DIR="$PROBE_UV_CACHE" VIRTUAL_ENV="$CP4_PROBE_ENV" UV_PROJECT_ENVIRONMENT="$CP4_PROBE_ENV" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 "$CP4_PROBE_ENV/bin/python" -B -I -S "$PROBE_ROOT/scripts/probe_cellpose_runtime.py" --contract "$PROBE_ROOT/probes/upstream/cp4/contract.toml" --output -
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$CP3_SCRATCH/home" CELLPOSE_LOCAL_MODELS_PATH="$CP3_SCRATCH/models" TORCH_HOME="$CP3_SCRATCH/torch" XDG_CACHE_HOME="$CP3_SCRATCH/xdg" MPLCONFIGDIR="$CP3_SCRATCH/mpl" NUMBA_CACHE_DIR="$CP3_SCRATCH/numba" TMPDIR="$CP3_SCRATCH/tmp" UV_CACHE_DIR="$PROBE_UV_CACHE" VIRTUAL_ENV="$CP3_PROBE_ENV" UV_PROJECT_ENVIRONMENT="$CP3_PROBE_ENV" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 "$CP3_PROBE_ENV/bin/python" -B -I -S "$PROBE_ROOT/scripts/probe_cellpose_runtime.py" --contract "$PROBE_ROOT/probes/upstream/cp3/contract.toml" --output -
```

Expected: both exit 0, every required check passes, every guard counter is
zero, the model-directory before/after hashes match, user site is disabled,
and repository paths are absent from probe `sys.path`. If either environment
tries to create a model/cache file, connect, or load/save a checkpoint, stop
and preserve the FAIL report.

- [ ] **Step 6: Run GREEN and commit expectations**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(probes/upstream/cp4/contract.toml probes/upstream/cp3/contract.toml scripts/probe_cellpose_runtime.py tests/contract/upstream/test_cp4_expectations.py tests/contract/upstream/test_cp3_expectations.py tests/contract/upstream/test_probe_engine.py)
PROBE_COMMIT_SUBJECT="test: freeze pinned Cellpose probe expectations"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_cp4_expectations.py tests/contract/upstream/test_cp3_expectations.py tests/contract/upstream/test_probe_engine.py -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix scripts/probe_cellpose_runtime.py tests/contract/upstream
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
git diff --check
git diff --quiet -- tests/contract/upstream/conftest.py
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

### Task 5: Add the isolated runner and report generators

**Files:**

- Create: `src/cellpose_mcp/release/upstream_runner.py`
- Create: `scripts/generate_upstream_contract_evidence.py`
- Create: `scripts/generate_cellpose_stable_release_check.py`
- Create: `scripts/check_upstream_contract_evidence.py`
- Create: `tests/contract/upstream/test_runner_isolation.py`
- Modify: `tests/contract/upstream/conftest.py`
- Modify: `tests/packaging/test_distribution_contents.py`

- [ ] **Step 1: Write RED runner tests**

Cover exact argv, allowlisted environment, omitted `PYTHONPATH`, clean-commit
pre/post requirements, absolute environment path, lexical venv interpreter
and approved managed-target binding, pre/post-identical uv/controller/managed/
runtime Python bytes, probe/contract copy hashes, entry/
post-provision/post-probe cache hashes, timeout, stdout-only JSON, exit-code
mapping, atomic no-overwrite writes, detached digest format, official host
allowlist, redirect host revalidation, TLS verification unchanged,
response-size limit, tampered lock/source/report rejection, and one
payload/contract mismatch test for each of `category`, `evidence_kind`,
`required`, target module/qualname/order, `expected`, check order,
missing/extra ID, and
unresolved-gate content.

Add this packaging RED test before creating the runner module:

```python
def test_upstream_runner_paths_are_allowlisted() -> None:
    assert "cellpose_mcp/release/upstream_runner.py" in VALID_WHEEL_PATHS
    assert "src/cellpose_mcp/release/upstream_runner.py" in VALID_SDIST_PATHS
```

```python
def test_probe_command_is_frozen_offline_and_isolated(request: ProbeRequest) -> None:
    command = build_probe_command(
        request,
        Path("/private/tmp/probe.py"),
        Path("/private/tmp/contract.toml"),
    )
    assert command == (
        str(request.environment_dir / "bin" / "python"),
        "-B",
        "-I",
        "-S",
        "/private/tmp/probe.py",
        "--contract",
        "/private/tmp/contract.toml",
        "--output",
        "-",
    )


def test_runtime_provisioning_is_fresh_frozen_offline_and_wheel_only(
    request: ProbeRequest,
) -> None:
    assert build_provisioning_command(request) == (
        str(request.uv_path),
        "--quiet",
        "sync",
        "--project",
        str(request.project_dir),
        "--frozen",
        "--offline",
        "--no-build",
        "--no-python-downloads",
        "--no-config",
        "--python",
        str(request.python_path),
    )
    assert build_provisioning_environment(request) == {
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "HOME": str(request.provisioning_home),
        "TMPDIR": str(request.provisioning_tmp),
        "UV_PROJECT_ENVIRONMENT": str(request.environment_dir),
        "UV_CACHE_DIR": str(request.cache_dir),
    }


@pytest.mark.parametrize(
    ("runtime_id", "project_name"),
    [
        ("cp4", "cellpose-mcp-cp4-contract-probe"),
        ("cp3", "cellpose-mcp-cp3-contract-probe"),
    ],
)
def test_runner_uses_the_exact_virtual_project_exclusion(
    request: ProbeRequest,
    runtime_id: Literal["cp4", "cp3"],
    project_name: str,
) -> None:
    request = replace(request, runtime_id=runtime_id)
    assert expected_probe_project_name(request) == project_name


def test_cp4_request_uses_the_sealed_executable_policy(
    request: ProbeRequest,
) -> None:
    assert request.runtime_id == "cp4"
    assert request.approved_uv_sha256 == (
        "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
    )
    assert request.approved_python_sha256 == (
        "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
    )
    assert request.expected_python_version == "Python 3.12.12"


def test_provisioning_storage_is_private_bound_and_distinct_from_probe_scratch(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
) -> None:
    assert request.provisioning_home.parent == request.provisioning_tmp.parent
    assert request.provisioning_home != request.provisioning_tmp
    provisioning_root = request.provisioning_home.parent
    assert provisioning_root.parent == Path("/private/tmp")
    assert not provisioning_root.exists()
    assert not request.provisioning_home.exists()
    assert not request.provisioning_tmp.exists()
    report = run_probe(
        request,
        repo_root=request.project_dir.parents[2],
        output_path=output_path,
    )
    assert stat.S_IMODE(request.provisioning_home.stat().st_mode) == 0o700
    assert stat.S_IMODE(request.provisioning_tmp.stat().st_mode) == 0o700
    assert stat.S_IMODE(provisioning_root.lstat().st_mode) == 0o700
    assert not provisioning_root.is_symlink()
    assert report.provisioning.provisioning_home == str(
        request.provisioning_home.resolve(strict=True)
    )
    assert report.provisioning.provisioning_tmp == str(
        request.provisioning_tmp.resolve(strict=True)
    )
    assert (
        report.provisioning.provisioning_home_before_sha256
        == report.provisioning.provisioning_home_after_sha256
    )
    assert (
        report.provisioning.provisioning_tmp_before_sha256
        == report.provisioning.provisioning_tmp_after_sha256
    )
    assert report.command.environment["HOME"] != str(request.provisioning_home)
    assert report.command.environment["TMPDIR"] != str(request.provisioning_tmp)


def test_direct_private_tmp_siblings_are_rejected(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
) -> None:
    request = replace(
        request,
        provisioning_home=Path("/private/tmp/probe-home"),
        provisioning_tmp=Path("/private/tmp/probe-tmp"),
    )
    with pytest.raises(ProbeIsolationError, match="fresh provisioning parent"):
        run_probe(
            request,
            repo_root=request.project_dir.parents[2],
            output_path=output_path,
        )
    assert fake_process.calls == []


@pytest.mark.parametrize("storage_name", ["provisioning_home", "provisioning_tmp"])
def test_provisioning_storage_delta_stops_before_probe(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
    storage_name: str,
) -> None:
    root = getattr(request, storage_name)
    fake_process.mutate_provisioning_storage_on_provision(root / "unexpected")
    with pytest.raises(ProbeIsolationError, match="provisioning storage changed"):
        run_probe(
            request,
            repo_root=request.project_dir.parents[2],
            output_path=output_path,
        )
    assert not fake_process.measured_probe_was_called
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


def test_probe_environment_omits_inherited_python_paths(
    request: ProbeRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHONPATH", "/untrusted")
    environment = build_probe_environment(request, tmp_path)
    assert "PYTHONPATH" not in environment
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["KMP_DUPLICATE_LIB_OK"] == "TRUE"
    assert environment["OMP_NUM_THREADS"] == "1"
    assert environment["TMPDIR"].startswith(str(tmp_path))
    assert "HTTP_PROXY" not in environment
    assert "HTTPS_PROXY" not in environment


def test_run_probe_rejects_an_existing_runtime_before_spawning(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
) -> None:
    request.environment_dir.mkdir()
    with pytest.raises(ProbeIsolationError, match="environment.*already exists"):
        run_probe(request, repo_root=request.project_dir.parents[2], output_path=output_path)
    assert fake_process.calls == []
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


def test_failed_provisioning_writes_no_report_or_digest(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
) -> None:
    fake_process.queue(
        returncode=0,
        stdout="uv 0.10.4 (079e3fd05 2026-02-17)\n",
        stderr="",
    )
    fake_process.queue(
        returncode=0,
        stdout=request.expected_python_version + "\n",
        stderr="",
    )
    fake_process.queue(returncode=1, stdout="", stderr="offline cache miss\n")
    with pytest.raises(ProbeProvisioningError, match="offline cache miss"):
        run_probe(request, repo_root=request.project_dir.parents[2], output_path=output_path)
    assert [call.argv for call in fake_process.calls] == [
        (str(request.uv_path), "--version"),
        (str(request.python_path), "--version"),
        build_provisioning_command(request),
    ]
    assert not request.environment_dir.exists()
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


@pytest.mark.parametrize("repository_delta", ["tracked", "untracked"])
def test_post_run_repository_change_writes_no_report(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
    repository_delta: str,
) -> None:
    fake_process.mutate_repository_on_probe(repository_delta)
    with pytest.raises(ProbeIsolationError, match="repository changed during probe"):
        run_probe(request, repo_root=request.project_dir.parents[2], output_path=output_path)
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


def test_probe_process_cache_change_writes_no_report(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
) -> None:
    fake_process.mutate_cache_on_probe(request.cache_dir / "wrapper-delta")
    with pytest.raises(ProbeIsolationError, match="cache changed during probe"):
        run_probe(request, repo_root=request.project_dir.parents[2], output_path=output_path)
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


def test_post_provision_cache_change_stops_before_probe_and_writes_no_report(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
) -> None:
    fake_process.mutate_cache_on_provision(request.cache_dir / "provision-delta")
    with pytest.raises(ProbeIsolationError, match="cache changed during provisioning"):
        run_probe(request, repo_root=request.project_dir.parents[2], output_path=output_path)
    assert [call.argv for call in fake_process.calls] == [
        (str(request.uv_path), "--version"),
        (str(request.python_path), "--version"),
        build_provisioning_command(request),
    ]
    assert not request.environment_dir.exists()
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


@pytest.mark.parametrize(
    "forbidden",
    [
        "GITHUB_TOKEN",
        "HTTPS_PROXY",
        "PYTHONPATH",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "PIP_CERT",
    ],
)
def test_controller_environment_rejects_inherited_authority(
    monkeypatch: pytest.MonkeyPatch,
    forbidden: str,
) -> None:
    monkeypatch.setenv(forbidden, "untrusted")
    with pytest.raises(ProbeIsolationError, match=forbidden):
        require_sanitized_controller_environment()


def test_stable_command_binds_direct_python_and_complete_environment(
    clean_repo: Path,
    sanitized_controller_environment: Mapping[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = clean_repo / "scripts/generate_cellpose_stable_release_check.py"
    expected = (
        sys.executable,
        "-B",
        "-I",
        "-S",
        str(script),
        "--cp4-version",
        "4.2.1.1",
        "--cp3-version",
        "3.1.1.3",
        "--output",
        "/private/tmp/stable.json",
    )
    monkeypatch.setattr(sys, "orig_argv", list(expected))
    binding = bind_current_python_command(clean_repo)
    assert binding.argv == expected
    assert binding.executable_path == str(Path(sys.executable).resolve(strict=True))
    assert binding.environment == sanitized_controller_environment
    assert binding.cwd_repo_relative == "."


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_b",
        "missing_i",
        "missing_s",
        "reordered_b_i",
        "reordered_i_s",
        "wrong_script",
        "wrong_cp4_argument",
    ],
)
def test_stable_command_rejects_missing_or_reordered_startup_flags_before_http(
    clean_repo: Path,
    output_path: Path,
    fake_official_responses: FakeOfficialResponses,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    script = clean_repo / "scripts/generate_cellpose_stable_release_check.py"
    argv = [
        sys.executable, "-B", "-I", "-S", str(script),
        "--cp4-version", "4.2.1.1", "--cp3-version", "3.1.1.3",
        "--output", str(output_path),
    ]
    mutations = {
        "missing_b": lambda value: value.pop(1),
        "missing_i": lambda value: value.pop(2),
        "missing_s": lambda value: value.pop(3),
        "reordered_b_i": lambda value: value.__setitem__(slice(1, 3), ["-I", "-B"]),
        "reordered_i_s": lambda value: value.__setitem__(slice(2, 4), ["-S", "-I"]),
        "wrong_script": lambda value: value.__setitem__(4, str(script.with_name("other.py"))),
        "wrong_cp4_argument": lambda value: value.__setitem__(6, "4.2.1.0"),
    }
    mutations[mutation](argv)
    monkeypatch.setattr(sys, "orig_argv", argv)
    with pytest.raises(ProbeIsolationError, match="direct Python command"):
        generate_stable_release_check(
            repo_root=clean_repo,
            cp4_version="4.2.1.1",
            cp3_version="3.1.1.3",
            output_path=output_path,
            responses=fake_official_responses,
        )
    assert fake_official_responses.requested_urls == []
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


@pytest.mark.parametrize(
    ("executable_kind", "swap_checkpoint"),
    [
        ("uv", "after_provisioning"),
        ("controller_python", "after_provisioning"),
        ("managed_python", "after_provisioning"),
        ("runtime_python", "after_probe"),
    ],
)
def test_run_probe_rejects_an_executable_swap(
    request: ProbeRequest,
    output_path: Path,
    fake_process: FakeProcess,
    executable_kind: str,
    swap_checkpoint: str,
) -> None:
    fake_process.swap_executable_after_checkpoint(executable_kind, swap_checkpoint)
    with pytest.raises(ProbeIsolationError, match="executable changed"):
        run_probe(request, repo_root=request.project_dir.parents[2], output_path=output_path)
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()


def test_stable_metadata_rejects_controller_python_swap(
    clean_repo: Path,
    output_path: Path,
    fake_official_responses: FakeOfficialResponses,
) -> None:
    fake_official_responses.swap_controller_python_after_last_response()
    with pytest.raises(ProbeIsolationError, match="controller.*changed"):
        generate_stable_release_check(
            repo_root=clean_repo,
            cp4_version="4.2.1.1",
            cp3_version="3.1.1.3",
            output_path=output_path,
            responses=fake_official_responses,
        )
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".sha256").exists()
```

The CLI-construction tests build both runtime requests from user-visible
runtime/path/output arguments, require CP3 to receive the sealed 3.11.14
hash/version pair, and prove no CLI flag can override an approved digest or
version. Parameterized mutations of either approved hash, executable path, or
version stop before `FakeProcess` records a spawn.
An additional parameterized `test_contract_generator_rejects_invalid_startup_command_before_spawn`
monkeypatches `sys.orig_argv` for the offline generator with the same missing,
reordered, wrong-script, and wrong-argument mutations shown above; every case
raises `ProbeIsolationError`, leaves `FakeProcess.calls == []`, and creates no
report or digest.

Run both generator scripts as real subprocesses under the correct
`-B -I -S` command in a temporary controller environment containing an
executable `.pth`, `sitecustomize.py`, and `usercustomize.py`, each writing a
distinct marker. Dependency imports must resolve only beneath the manually
inserted controller site-packages, project imports only beneath the validated
clean `repo_root/src`, and all three markers must remain absent. This separate
bootstrap test proves the subprocess startup boundary that same-process
`sys.orig_argv` mutation cannot prove.

`tests/contract/upstream/conftest.py` defines `FakeOfficialResponses` as an
`OfficialResponseSource` containing the exact allowlisted response map and an
ordered `requested_urls` list that starts empty; its
`swap_controller_python_after_last_response()` test hook atomically replaces
the canonical controller target only after serving the last configured
response. The fixture creates that target beneath `tmp_path` and monkeypatches
`sys.executable` to its lexical path; it never changes the installed pytest
interpreter. Any unconfigured URL is an assertion failure. For every
`test_run_probe_rejects_an_executable_swap` parameter, the request/fake-process
fixtures likewise bind uv, controller Python, managed Python, and runtime
Python to private `tmp_path` stand-ins (including the lexical runtime symlink)
and mutate only the selected stand-in. Uv, controller-Python, and
managed-Python swaps occur immediately after the provisioning child returns;
the runtime-Python swap occurs immediately after the measured probe returns.
Both checkpoints precede the corresponding re-hash and any report write. The
existing fake-process fixture records every child argv and `Popen` keyword.
Identify the measured-probe call uniquely by its exact runtime-Python
`argv[0]`, `-B`, `-I`, `-S`, and copied-probe path, and require its complete
argv to equal `build_probe_command(request, copied_probe, copied_contract)`;
assert that call has `cwd == repo_root` and
`start_new_session is True`, `close_fds is True`, `pass_fds == ()`, and
`stdin is subprocess.DEVNULL`. Do not describe it as the sole call: a successful
run also has the uv-version preflight, managed-Python-version preflight, and
provisioning call. Assert the
provisioning call separately against `build_provisioning_command` and
`build_provisioning_environment`.

- [ ] **Step 2: Run RED**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 2 "No module named 'cellpose_mcp.release.upstream_runner'" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_runner_isolation.py tests/packaging/test_distribution_contents.py::test_upstream_runner_paths_are_allowlisted -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/src/cellpose_mcp/release/upstream_runner.py"
test ! -e "$PROBE_ROOT/scripts/generate_upstream_contract_evidence.py"
test ! -e "$PROBE_ROOT/scripts/generate_cellpose_stable_release_check.py"
test ! -e "$PROBE_ROOT/scripts/check_upstream_contract_evidence.py"
```

Expected: import failures for the missing runner and generators.

- [ ] **Step 3: Implement the private runner**

`build_provisioning_environment` returns exactly `PATH=/usr/bin:/bin`,
`LANG=C`, `LC_ALL=C`, `HOME=request.provisioning_home`,
`TMPDIR=request.provisioning_tmp`,
`UV_PROJECT_ENVIRONMENT=request.environment_dir`, and
`UV_CACHE_DIR=request.cache_dir`. It does not inherit any other variable.

`build_probe_environment` returns exactly
`PATH=/usr/bin:/bin`, `LANG=C`, `LC_ALL=C`,
`HOME`, `CELLPOSE_LOCAL_MODELS_PATH`, `TORCH_HOME`, `XDG_CACHE_HOME`,
`MPLCONFIGDIR`, `NUMBA_CACHE_DIR`, `TMPDIR`, `UV_CACHE_DIR`,
`VIRTUAL_ENV`,
`PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`,
`KMP_DUPLICATE_LIB_OK=TRUE`, `OMP_NUM_THREADS=1`, and the request's absolute
`UV_PROJECT_ENVIRONMENT`. Both `VIRTUAL_ENV` and `UV_PROJECT_ENVIRONMENT` are
exactly `request.environment_dir`. `UV_CACHE_DIR` is exactly the pre-populated
`request.cache_dir` and is read-only during probing; every home, application
cache, model, and temp value is a child of the new mode-0700 scratch root. The
runner creates each child before guard installation. It does not copy
arbitrary process variables, proxies, credentials, certificate overrides, or
Python paths.

`run_probe` requires:

- hash `sys.executable` (the direct controller Python), `request.uv_path`, and
  `request.python_path` before any child spawn; require the uv and managed
  Python digests to equal both their sealed runtime-policy constants and the
  request's approved hash fields, and require the controller's canonical target
  to equal the sealed CP4/controller Python path and digest; resolve each canonical path
  once, reject aliases that change identity, and require the same canonical
  path and bytes again after provisioning and after the probe child exits;
- map `request.runtime_id` through the total literal mapping
  `{"cp4": "cellpose-mcp-cp4-contract-probe", "cp3":
  "cellpose-mcp-cp3-contract-probe"}` and call
  `validate_transitive_lock_sources(request.project_dir / "uv.lock",
  excluded_project_name=expected_probe_project_name(request))` before the first
  preflight child and again immediately before the offline
  provisioning spawn; bind its returned digest and stop before uv on any
  source-policy violation;
- execute exactly `(str(request.uv_path), "--version")` after the initial uv
  hash and before provisioning, with `cwd=repo_root`, the exact
  `build_provisioning_environment(request)`, `close_fds=True`, `pass_fds=()`,
  `stdin=subprocess.DEVNULL`, and a 30-second timeout; require exit zero, empty
  stderr, and stdout exactly `uv 0.10.4 (079e3fd05 2026-02-17)\n`, then bind
  `runtime.uv_version = "0.10.4"`;
- next execute exactly `(str(request.python_path), "--version")` with the same
  sanitized environment, cwd, descriptor closure, stdin, and timeout; require
  exit zero, empty stderr, and stdout exactly the request's `Python 3.12.12\n`
  or `Python 3.11.14\n`. The controller's `/usr/bin/shasum` binding of that
  managed executable precedes this call; the managed interpreter never hashes
  or validates itself;
- the same clean product commit (`git status --porcelain` empty) before any
  subprocess and again after the probe child exits; tracked or untracked
  post-run deltas are fatal and no report is written;
- request paths resolve beneath that clone except the absolute environment,
  cache, provisioning HOME/TMP, managed Python, and uv executable;
- `generator_path` is the exact offline generator invoking `run_probe`; bind
  it and `Path(upstream_runner.__file__)` as repository-relative
  `ScriptBinding` records before subprocess launch;
- `environment_dir` does not exist at entry; before probing, run the exact
  provisioning command with only fixed PATH/locale,
  `UV_PROJECT_ENVIRONMENT=environment_dir`, and
  `UV_CACHE_DIR=request.cache_dir`, no proxies/credentials, `cwd=repo_root`,
  and no network authority;
- `provisioning_home` and `provisioning_tmp` are distinct absolute canonical
  paths, absent at entry, non-symlink siblings under one fresh runner-owned
  `/private/tmp` root, and distinct from the runtime, output, cache, repository,
  and measured-probe scratch paths. Create the root and both children fresh at
  mode 0700; reject pre-existence, aliasing, symlinks, or wrong modes before a
  child spawn;
- hash both provisioning trees immediately after their creation, after the
  provisioning child, and after the separately created measured-probe scratch
  child exits. All three hashes for each tree must match. Bind the two canonical
  paths and four before/after SHA-256 values in `ProvisioningBinding`; any delta
  stops before the measured child (or before report writing if detected after
  it), writes no report/digest, and preserves only diagnostic scratch;
- hash the complete warm-cache tree at run entry, immediately after
  provisioning, and after the direct runtime-Python probe child exits; all three hashes must be
  equal before report creation;
- quiet provisioning exits zero with no stderr and creates
  `environment_dir/bin/python` as a lexical in-environment symlink. The measured
  child runs with `-S`, so it must report `sys.flags.no_site == 1`, exact
  `sys.orig_argv` with `-B -I -S`, and `sys.prefix == sys.base_prefix` at the
  approved managed prefix rather than pretending the venv prefix was activated
  by `site`. `sys.executable` remains lexically the environment path; the child
  derives the lexical environment root from that path, manually inserts only
  its validated `lib/pythonX.Y/site-packages`, and imports Cellpose beneath that
  exact directory. The symlink's resolved target and
  `sys.base_prefix/bin/python3.<minor>` resolve to the explicitly approved
  `request.python_path`; immediately before and after the measured child,
  require the lexical symlink text, its canonical target, the base-prefix
  Python path, and the bytes of all three interpreter references to be
  unchanged, with all canonical targets equal to the pre-hashed approved
  managed Python;
- a fresh mode-0700 directory under `/private/tmp`;
- copied probe/contract bytes match their pre-copy hashes, and every bound
  runner/generator/probe/contract/lock source byte remains unchanged after the
  child exits; the controller, uv, managed-Python, and runtime-Python
  executable pre/post hashes must likewise remain identical;
- a 180-second subprocess timeout;
- `subprocess.Popen(..., cwd=repo_root, start_new_session=True,
  close_fds=True, pass_fds=(), stdin=subprocess.DEVNULL)` so `--project`
  is never involved and the probe cannot inherit the dirty caller's working
  directory, with timeout cleanup terminating and reaping the complete child
  process group;
- no stderr on success and exactly one JSON document on stdout;
- the contract/runtime/lock/version identities all agree; and
- an exclusive mode-0600 temporary report, `fsync`, no-overwrite atomic link,
  directory `fsync`, and matching detached digest.

No runner fallback imports Cellpose in the controller process.

Append exactly `cellpose_mcp/release/upstream_runner.py` to
`VALID_WHEEL_PATHS` and `src/cellpose_mcp/release/upstream_runner.py` to
`VALID_SDIST_PATHS`; retain exact-set equality.

Exit translation is exact: return `0` requires a valid PASS payload with all
required checks passing and zero safety counters; return `2` requires a valid
FAIL payload with at least one failed required check and zero guard counters;
return `3` requires a valid FAIL payload with at least one nonzero guard or
isolation violation. The latter two are written as canonical FAIL reports and
the generator exits with the same code. Return `4`, timeout, signal death,
malformed/multiple stdout JSON, or any return/payload mismatch raises
`ProbeProtocolError`, writes no final report or digest, and leaves only the
mode-0700 diagnostic scratch for review. A provisioning failure raises
`ProbeProvisioningError`, removes only the newly created partial
`environment_dir`, and writes neither a report nor a digest.
Adversarial tests cover pre-existing, symlinked, aliased, wrong-mode, and
mutated provisioning HOME/TMP paths, assert no measured-probe spawn on a
provisioning delta, and prove provisioning storage and measured scratch have
different parents and are independently hashed.

- [ ] **Step 4: Implement the official-metadata boundary**

The stable generator is the only network-capable script. It permits HTTPS
GETs, with the default verified SSL context, 30-second timeout, and 10 MiB
maximum body, only to:

```text
https://pypi.org/pypi/cellpose/json
https://api.github.com/repos/MouseLand/cellpose/git/ref/tags/v4.2.1.1
https://api.github.com/repos/MouseLand/cellpose/git/ref/tags/v3.1.1.3
https://api.github.com/repos/MouseLand/cellpose/git/tags/{annotated-tag-object-sha}
```

Disable automatic redirects and validate every initial URL and every resolved
`Location` before issuing its request. The PyPI URL and two ref URLs must equal
the three fixed strings above byte-for-byte, with no userinfo, explicit port,
query, or fragment. A dynamic tag URL is allowed only when it equals
`https://api.github.com/repos/MouseLand/cellpose/git/tags/<sha>` where `<sha>`
is the lowercase 40-hex object SHA from the immediately preceding validated
GitHub response; a path prefix is never sufficient. GitHub annotated tags are
dereferenced until a commit object is reached, with at most two dereferences.
Tests reject same-host wrong paths, prefix/suffix paths, query, fragment,
userinfo, explicit port, wrong host, malformed SHA, and a valid-looking SHA
not bound by the immediately preceding response, for both initial and redirect
URLs. PyPI release files must provide SHA-256 digests. The script never imports
Cellpose or Torch and never accesses a model host.

HTTP redirection is a separate closed state machine: at most three redirects
per initial request, no repeated normalized URL, exactly one nonempty
`Location` header on each 301/302/303/307/308 response, and no redirect for any
other status. Relative, scheme-relative, userinfo-bearing, explicit-port,
query, fragment, cyclic, fourth-hop, missing-Location, and duplicate-Location
responses fail before a follow-up request. Unit tests exercise the production
no-auto-redirect response source itself through an injected fake transport—not
only `FakeOfficialResponses`—for every initial and redirect allowlist branch,
TLS-context preservation, hop limit, cycle, status, and Location cardinality.

Store PyPI artifacts under exact `4.2.1.1` and `3.1.1.3` keys; every
`RegistryArtifact.version` must equal its key. Tests give the two versions a
same-named fake wheel with different hashes and prove cross-version swapping
fails. A metadata check's URL/hash pair must match exactly one retained source;
tests swap source/hash bindings between endpoints and require rejection.

Use `packaging.version.Version` from the checked root lock to select the
greatest valid PyPI release for which `is_prerelease` and `is_devrelease` are
false and at least one file is not yanked. Tests include yanked-newer,
prerelease-newer, invalid-version, missing-digest, oversized-response,
redirected-host, redirected-wrong-path, redirected-query,
redirected-userinfo, annotated-tag, and mixed-yanked-file fixtures. The latter
proves that a non-yanked sdist does not authorize a yanked selected wheel.
Send a fixed product user agent
and no credential or cookie. Build an opener with `ProxyHandler({})`; never
read `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, `GITHUB_TOKEN`,
`GH_TOKEN`, netrc, cookies, or custom CA environment variables. Stable report
writes use the same exclusive, fsynced, no-overwrite canonical writer as
contract reports.

- [ ] **Step 5: Implement the offline verifier**

For each contract report, verify canonical JSON, detached digest, PASS status,
zero guards, complete required check order, and the exact product-owned probe,
contract, lock, and runner bytes as they existed at `product.commit_sha` using
read-only `git show COMMIT:PATH`. A report is stale if one of those
product-owned files at that commit does not hash to its report value. Upstream
Cellpose files are not product Git objects: require every check's complete
`sources` tuple to match
`installation.cellpose.source_file_hashes`, and require that map plus the
normalized RECORD/tree hashes to match the report. Verify the stable
report's official source list and policy checks but do not contact the network.
When all three reports are present, also require their `product.commit_sha`
values to match; require the stable report's observed tag commits to equal the
two contracts' declared tag commits; require each selected installed wheel to
equal one locked candidate; and require every complete
`(version, filename, URL, SHA-256, size)` locked/selected identity to occur
under the same version key in the official release-file observation with
`yanked is false`.
`--require-common-product-commit SHA` accepts only a lowercase 40-hex SHA,
typed-loads and detached-digest-verifies all three required reports, then
requires their common `product.commit_sha` to equal that exact argument.

Historical provenance is insufficient for freshness. For every reported
product-owned binding (`runner`, contract `generator`, stable-report `script`,
probe, contract, and lock), also
hash the path from `git show HEAD:PATH` and the current working-tree file and
require both to equal the report. Require the report's product commit to be an
ancestor of HEAD. Thus a later committed or uncommitted change to a bound file
invalidates the old report immediately and requires replacement evidence; an
unrelated later file does not. Parameterized tests commit and separately make
uncommitted one-byte mutations for each of the six binding kinds: runner,
contract generator, stable generator script, probe, contract, and lock.
`--require-all` must fail for every committed and worktree case, while a
mutation to an unrelated file remains accepted.
`--compare-invariants` removes only `generated_at_utc` and `report_id`, then
relocates the validated repository root, controller environment, runtime
environment, probe scratch root, provisioning parent/HOME/TMP, warm-cache root,
and output path to distinct
stable sentinel strings in `product.repository`, `provisioning.argv`,
`provisioning.cwd_repo_relative`, `provisioning.environment`,
`provisioning.provisioning_home`, `provisioning.provisioning_tmp`, `command.argv`,
`command.cwd_repo_relative`, `command.environment`, `runtime.environment_root`,
`runtime.site_packages_path`, `runtime.interpreter.lexical_path`, and
`runtime.imported_cellpose_path` before
requiring exact equality. It derives
those exact prefixes from typed path fields, preserves path boundaries, and
never masks a non-path substring. The provisioner's selected artifact and
policy, both normalized installation hashes, the provisioning HOME/TMP
before/after tree digests (which hash relative contents, not absolute roots),
all product commits, executable
hashes, runtime versions/platform/machine, locks, source hashes, guards,
checks, observations, and unresolved gates remain invariant. Tests reproduce
the same report beneath two unequal-length roots, prove the raw console-script
and RECORD bytes differ, explicitly assert that the two raw
`runtime.environment_root`, `runtime.site_packages_path`, and
`runtime.interpreter.lexical_path` values are pairwise unequal across runs.
Each lexical interpreter must equal its own environment's `bin/python`, and
each site-packages path must equal its own environment root's exact
`lib/pythonX.Y/site-packages` child. Require invariant comparison to pass only
because the specified path fields and normalized installation hashes are
handled as defined.

- [ ] **Step 6: Run GREEN and commit implementation**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(src/cellpose_mcp/release/upstream_runner.py scripts/generate_upstream_contract_evidence.py scripts/generate_cellpose_stable_release_check.py scripts/check_upstream_contract_evidence.py tests/contract/upstream/conftest.py tests/contract/upstream/test_runner_isolation.py tests/packaging/test_distribution_contents.py)
PROBE_COMMIT_SUBJECT="feat: add isolated upstream evidence runner"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_runner_isolation.py tests/contract/upstream/test_evidence_schema.py -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_distribution_contents.py::test_upstream_runner_paths_are_allowlisted -v
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix src/cellpose_mcp/release/upstream_evidence.py src/cellpose_mcp/release/upstream_runner.py scripts/generate_upstream_contract_evidence.py scripts/generate_cellpose_stable_release_check.py scripts/check_upstream_contract_evidence.py tests/contract/upstream
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev mypy src/cellpose_mcp/release/upstream_evidence.py src/cellpose_mcp/release/upstream_runner.py
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
git diff --check
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

Run all 21 distribution-content tests from this new commit. The clean-clone
wheel/sdist sets must now contain both upstream modules and no extra file.

### Task 6: Generate CP4 and CP3 evidence from a clean implementation commit

**Files:** Temporary reports under `/private/tmp`; no repository file until
Task 8.

- [ ] **Step 1: Prove the implementation commit is clean and create a clone**

```bash
set -euo pipefail
git diff --cached --quiet
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test ! -e "$PROBE_CLONE"
git clone --no-hardlinks --local . "$PROBE_CLONE"
git -C "$PROBE_CLONE" checkout --detach "$PROBE_IMPLEMENTATION_SHA"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
```

Expected: the detached clone is clean and contains no untracked user work.

- [ ] **Step 2: Realize the controller and reserve fresh runtime paths**

```bash
set -euo pipefail
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CLONE"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_CLONE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_CONTROLLER_ENV=/private/tmp/cellpose-mcp-probe-controller-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_HOME=/private/tmp/cellpose-mcp-probe-controller-home-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_TMP=/private/tmp/cellpose-mcp-probe-controller-tmp-${PROBE_IMPLEMENTATION_SHA}
CP4_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"probes/upstream/cp4/uv.lock").read_bytes()).hexdigest())' "$PROBE_CLONE")
[[ $CP4_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP4_LOCK_SHA
CP3_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"probes/upstream/cp3/uv.lock").read_bytes()).hexdigest())' "$PROBE_CLONE")
[[ $CP3_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP3_LOCK_SHA
export CP4_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp4-${PROBE_IMPLEMENTATION_SHA}-${CP4_LOCK_SHA}
export CP3_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp3-${PROBE_IMPLEMENTATION_SHA}-${CP3_LOCK_SHA}
test ! -e "$PROBE_CONTROLLER_ENV"
test ! -e "$PROBE_CONTROLLER_HOME"
test ! -e "$PROBE_CONTROLLER_TMP"
test ! -e "$CP4_PROBE_ENV"
test ! -e "$CP3_PROBE_ENV"
install -d -m 700 "$PROBE_CONTROLLER_HOME" "$PROBE_CONTROLLER_TMP"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" UV_PROJECT_ENVIRONMENT="$PROBE_CONTROLLER_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_CLONE" sync --project "$PROBE_CLONE" --frozen --offline --no-build --no-install-project --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev
PROBE_CONTROLLER_SITE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -c 'import site; paths=site.getsitepackages(); assert len(paths)==1; print(paths[0])')
[[ $PROBE_CONTROLLER_SITE == "$PROBE_CONTROLLER_ENV"/*/site-packages ]]
export PROBE_CONTROLLER_SITE
PROBE_CONTROLLER_PTH_SHA=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; target=Path(sys.argv[1]); payload=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.fchmod(fd,0o600); assert os.write(fd,payload)==len(payload); os.fsync(fd); os.close(fd); info=target.lstat(); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert target.read_bytes()==payload; print(hashlib.sha256(payload).hexdigest())' "$PROBE_CONTROLLER_SITE/cellpose_mcp_probe_source.pth" "$PROBE_CLONE/src")
[[ $PROBE_CONTROLLER_PTH_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_CONTROLLER_PTH_SHA
test -x "$PROBE_CONTROLLER_ENV/bin/python"
```

Expected: sync succeeds entirely from the checked lock and local cache without
building or installing the local project, and the exact controller source
binding points to `PROBE_CLONE/src`; both runtime paths remain
absent. Each generator call owns its runtime's fresh offline no-build,
no-Python-download, no-config sync and
records that command. If a controller artifact is absent from the cache, stop
and request narrow dependency-provisioning approval before rerunning only the
controller sync without `--offline`, using only this separately approved exact
retry (never an inherited shell environment):

```bash
set -euo pipefail
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CLONE"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_CLONE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_CONTROLLER_ENV=/private/tmp/cellpose-mcp-probe-controller-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_HOME=/private/tmp/cellpose-mcp-probe-controller-home-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_TMP=/private/tmp/cellpose-mcp-probe-controller-tmp-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CONTROLLER_HOME"
test -d "$PROBE_CONTROLLER_TMP"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" UV_PROJECT_ENVIRONMENT="$PROBE_CONTROLLER_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_CLONE" sync --project "$PROBE_CLONE" --frozen --no-build --no-install-project --no-python-downloads --no-config --default-index https://pypi.org/simple --keyring-provider disabled --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev
PROBE_CONTROLLER_SITE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -c 'import site; paths=site.getsitepackages(); assert len(paths)==1; print(paths[0])')
[[ $PROBE_CONTROLLER_SITE == "$PROBE_CONTROLLER_ENV"/*/site-packages ]]
export PROBE_CONTROLLER_SITE
PROBE_CONTROLLER_PTH_SHA=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; target=Path(sys.argv[1]); payload=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.fchmod(fd,0o600); assert os.write(fd,payload)==len(payload); os.fsync(fd); os.close(fd); info=target.lstat(); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert target.read_bytes()==payload; print(hashlib.sha256(payload).hexdigest())' "$PROBE_CONTROLLER_SITE/cellpose_mcp_probe_source.pth" "$PROBE_CLONE/src")
[[ $PROBE_CONTROLLER_PTH_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_CONTROLLER_PTH_SHA
```

The retry permits only `https://pypi.org/simple` and PyPI-declared
`files.pythonhosted.org` artifact traffic, disables keyring lookup, permits no
private/supplemental index, and inherits no proxy, token, credential, custom
certificate, config, or model-host authority.

- [ ] **Step 3: Run both offline generators from the clean clone**

```bash
set -euo pipefail
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CLONE"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"uv.lock").read_bytes()).hexdigest())' "$PROBE_CLONE")
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_CONTROLLER_ENV=/private/tmp/cellpose-mcp-probe-controller-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_HOME=/private/tmp/cellpose-mcp-probe-controller-home-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_TMP=/private/tmp/cellpose-mcp-probe-controller-tmp-${PROBE_IMPLEMENTATION_SHA}
CP4_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"probes/upstream/cp4/uv.lock").read_bytes()).hexdigest())' "$PROBE_CLONE")
[[ $CP4_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP4_LOCK_SHA
CP3_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"probes/upstream/cp3/uv.lock").read_bytes()).hexdigest())' "$PROBE_CLONE")
[[ $CP3_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export CP3_LOCK_SHA
export CP4_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp4-${PROBE_IMPLEMENTATION_SHA}-${CP4_LOCK_SHA}
export CP3_PROBE_ENV=/private/tmp/cellpose-mcp-probe-cp3-${PROBE_IMPLEMENTATION_SHA}-${CP3_LOCK_SHA}
export PROBE_OUTPUT=/private/tmp/cellpose-mcp-probe-output-${PROBE_IMPLEMENTATION_SHA}
test ! -e "$PROBE_OUTPUT"
install -d -m 700 "$PROBE_OUTPUT"
test ! -e "$PROBE_OUTPUT/cp4-4.2.1.1-contract.json"
test ! -e "$PROBE_OUTPUT/cp4-4.2.1.1-contract.json.sha256"
test ! -e "$PROBE_OUTPUT/cp3-3.1.1.3-contract.json"
test ! -e "$PROBE_OUTPUT/cp3-3.1.1.3-contract.json.sha256"
test -d "$PROBE_CONTROLLER_HOME"
test -d "$PROBE_CONTROLLER_TMP"
test "$(/usr/bin/readlink "$PROBE_CONTROLLER_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_CONTROLLER_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_CONTROLLER_PTH="$PROBE_CONTROLLER_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth"
PROBE_CONTROLLER_PTH_SHA_BEFORE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
[[ $PROBE_CONTROLLER_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
CP4_PROVISIONING_ROOT=/private/tmp/cellpose-mcp-probe-provisioning-${PROBE_IMPLEMENTATION_SHA}-cp4
CP3_PROVISIONING_ROOT=/private/tmp/cellpose-mcp-probe-provisioning-${PROBE_IMPLEMENTATION_SHA}-cp3
test ! -e "$CP4_PROVISIONING_ROOT"
test ! -e "$CP3_PROVISIONING_ROOT"
cd "$PROBE_CLONE"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S "$PROBE_CLONE/scripts/generate_upstream_contract_evidence.py" contract --runtime cp4 --environment "$CP4_PROBE_ENV" --cache "$PROBE_UV_CACHE" --provisioning-home "$CP4_PROVISIONING_ROOT/home" --provisioning-tmp "$CP4_PROVISIONING_ROOT/tmp" --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --uv /Users/suraj/.local/bin/uv --output "$PROBE_OUTPUT/cp4-4.2.1.1-contract.json"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S "$PROBE_CLONE/scripts/generate_upstream_contract_evidence.py" contract --runtime cp3 --environment "$CP3_PROBE_ENV" --cache "$PROBE_UV_CACHE" --provisioning-home "$CP3_PROVISIONING_ROOT/home" --provisioning-tmp "$CP3_PROVISIONING_ROOT/tmp" --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --uv /Users/suraj/.local/bin/uv --output "$PROBE_OUTPUT/cp3-3.1.1.3-contract.json"
PROBE_CONTROLLER_PTH_SHA_AFTER=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
test "$PROBE_CONTROLLER_PTH_SHA_AFTER" = "$PROBE_CONTROLLER_PTH_SHA_BEFORE"
```

For each sanitized direct-controller call, the runner first creates the absent
runtime with its recorded frozen, offline, no-build provisioning command,
verifies the cache is unchanged, and then invokes the environment's Python
directly in isolated mode. The reports and detached digest files are written
outside the probing clone.

- [ ] **Step 4: Inspect safety and identity fields**

```bash
set -euo pipefail
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CLONE"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_CLONE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_CONTROLLER_ENV=/private/tmp/cellpose-mcp-probe-controller-${PROBE_IMPLEMENTATION_SHA}
export PROBE_OUTPUT=/private/tmp/cellpose-mcp-probe-output-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_HOME=/private/tmp/cellpose-mcp-probe-controller-home-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_TMP=/private/tmp/cellpose-mcp-probe-controller-tmp-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CONTROLLER_HOME"
test -d "$PROBE_CONTROLLER_TMP"
test "$(/usr/bin/readlink "$PROBE_CONTROLLER_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_CONTROLLER_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_CONTROLLER_PTH="$PROBE_CONTROLLER_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth"
PROBE_CONTROLLER_PTH_SHA_BEFORE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
[[ $PROBE_CONTROLLER_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PROBE_OUTPUT="$PROBE_OUTPUT" PROBE_IMPLEMENTATION_SHA="$PROBE_IMPLEMENTATION_SHA" UV_PROJECT_ENVIRONMENT="$PROBE_CONTROLLER_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_CLONE" run --project "$PROBE_CLONE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I -c 'from pathlib import Path; from cellpose_mcp.release.upstream_evidence import load_upstream_report, verify_report_digest; import os; root=Path(os.environ["PROBE_OUTPUT"]); paths=[root/"cp4-4.2.1.1-contract.json",root/"cp3-3.1.1.3-contract.json"]; [verify_report_digest(p) for p in paths]; reports=[load_upstream_report(p) for p in paths]; assert all(r.outcome=="PASS" for r in reports); assert all(r.product.commit_sha==os.environ["PROBE_IMPLEMENTATION_SHA"] for r in reports); assert all(r.guards.network_attempt_count==r.guards.torch_load_count==r.guards.torch_save_count==r.guards.model_constructor_count==r.guards.process_spawn_count==0 for r in reports); assert all(not r.guards.unapproved_filesystem_deltas for r in reports)'
PROBE_CONTROLLER_PTH_SHA_AFTER=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
test "$PROBE_CONTROLLER_PTH_SHA_AFTER" = "$PROBE_CONTROLLER_PTH_SHA_BEFORE"
```

Expected: exit 0. Manually review the check/evidence-kind mapping and every
unresolved real-model gate before continuing.

### Task 7: Generate the official stable-version report

**Files:** Temporary report under `/private/tmp`; no repository file until
Task 8.

- [ ] **Step 1: Verify the recorded official-metadata approval**

The same pre-execution handoff separately identifies the exact allowlisted
PyPI/GitHub metadata endpoints in Task 5. Confirm that authority was approved;
it grants no package, model-host, or weight-download authority.

- [ ] **Step 2: Generate from the same clean implementation commit**

```bash
set -euo pipefail
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CLONE"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_CLONE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_CONTROLLER_ENV=/private/tmp/cellpose-mcp-probe-controller-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_HOME=/private/tmp/cellpose-mcp-probe-controller-home-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_TMP=/private/tmp/cellpose-mcp-probe-controller-tmp-${PROBE_IMPLEMENTATION_SHA}
export PROBE_OUTPUT=/private/tmp/cellpose-mcp-probe-output-${PROBE_IMPLEMENTATION_SHA}
test ! -e "$PROBE_OUTPUT/cellpose-stable-release-check.json"
test ! -e "$PROBE_OUTPUT/cellpose-stable-release-check.json.sha256"
test -d "$PROBE_CONTROLLER_HOME"
test -d "$PROBE_CONTROLLER_TMP"
test "$(/usr/bin/readlink "$PROBE_CONTROLLER_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_CONTROLLER_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_CONTROLLER_PTH="$PROBE_CONTROLLER_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth"
PROBE_CONTROLLER_PTH_SHA_BEFORE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
[[ $PROBE_CONTROLLER_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
cd "$PROBE_CLONE"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S "$PROBE_CLONE/scripts/generate_cellpose_stable_release_check.py" --cp4-version 4.2.1.1 --cp3-version 3.1.1.3 --output "$PROBE_OUTPUT/cellpose-stable-release-check.json"
PROBE_CONTROLLER_PTH_SHA_AFTER=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
test "$PROBE_CONTROLLER_PTH_SHA_AFTER" = "$PROBE_CONTROLLER_PTH_SHA_BEFORE"
```

The direct child metadata script is intentionally network-capable under the
separately approved exact endpoint allowlist. Its entire process environment
is the validated allowlist above, and its opener disables proxies and
credentials.

Expected: exit 0 only when PyPI still identifies `4.2.1.1` as the latest
non-yanked stable and both official tag commits match the expected refs. A
newer stable release or changed/missing official metadata produces a FAIL
report and pauses enum/runtime freezing for a major user decision.

- [ ] **Step 3: Verify the report offline**

```bash
set -euo pipefail
PROBE_IMPLEMENTATION_SHA=$(git rev-parse HEAD)
[[ $PROBE_IMPLEMENTATION_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_IMPLEMENTATION_SHA
export PROBE_CLONE=/private/tmp/cellpose-mcp-probe-clean-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CLONE"
test "$(git -C "$PROBE_CLONE" rev-parse HEAD)" = "$PROBE_IMPLEMENTATION_SHA"
test -z "$(git -C "$PROBE_CLONE" branch --show-current)"
test -z "$(git -C "$PROBE_CLONE" status --porcelain)"
PROBE_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$PROBE_CLONE/uv.lock" | /usr/bin/awk '{print $1}')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_CONTROLLER_ENV=/private/tmp/cellpose-mcp-probe-controller-${PROBE_IMPLEMENTATION_SHA}
export PROBE_OUTPUT=/private/tmp/cellpose-mcp-probe-output-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_HOME=/private/tmp/cellpose-mcp-probe-controller-home-${PROBE_IMPLEMENTATION_SHA}
export PROBE_CONTROLLER_TMP=/private/tmp/cellpose-mcp-probe-controller-tmp-${PROBE_IMPLEMENTATION_SHA}
test -d "$PROBE_CONTROLLER_HOME"
test -d "$PROBE_CONTROLLER_TMP"
test "$(/usr/bin/readlink "$PROBE_CONTROLLER_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_CONTROLLER_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_CONTROLLER_PTH="$PROBE_CONTROLLER_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth"
PROBE_CONTROLLER_PTH_SHA_BEFORE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
[[ $PROBE_CONTROLLER_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PROBE_OUTPUT="$PROBE_OUTPUT" PROBE_IMPLEMENTATION_SHA="$PROBE_IMPLEMENTATION_SHA" UV_PROJECT_ENVIRONMENT="$PROBE_CONTROLLER_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_CLONE" run --project "$PROBE_CLONE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I -c 'from pathlib import Path; from cellpose_mcp.release.upstream_evidence import load_upstream_report, verify_report_digest; import os; p=Path(os.environ["PROBE_OUTPUT"])/"cellpose-stable-release-check.json"; verify_report_digest(p); r=load_upstream_report(p); assert r.outcome=="PASS"; assert r.product.commit_sha==os.environ["PROBE_IMPLEMENTATION_SHA"]'
PROBE_CONTROLLER_PTH_SHA_AFTER=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_CONTROLLER_HOME" TMPDIR="$PROBE_CONTROLLER_TMP" "$PROBE_CONTROLLER_ENV/bin/python" -B -I -S -c 'from pathlib import Path; import hashlib,os,stat,sys; assert sys.flags.no_site==1 and "site" not in sys.modules; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_CONTROLLER_PTH" "$PROBE_CLONE/src")
test "$PROBE_CONTROLLER_PTH_SHA_AFTER" = "$PROBE_CONTROLLER_PTH_SHA_BEFORE"
```

Expected: exit 0 without another network request.

### Task 8: Commit immutable reports and reproduction documentation

**Files:**

- Create: `tests/contract/upstream/test_committed_reports.py`
- Create: `docs/evidence/upstream/README.md`
- Create: `docs/evidence/upstream/cp4-4.2.1.1-contract.json`
- Create: `docs/evidence/upstream/cp4-4.2.1.1-contract.json.sha256`
- Create: `docs/evidence/upstream/cp3-3.1.1.3-contract.json`
- Create: `docs/evidence/upstream/cp3-3.1.1.3-contract.json.sha256`
- Create: `docs/evidence/upstream/cellpose-stable-release-check.json`
- Create: `docs/evidence/upstream/cellpose-stable-release-check.json.sha256`

These are the exact eight Task 8 paths: one committed-report test, one README,
three canonical reports, and their three detached digests. No glob or implicit
"all evidence files" path is permitted.

- [ ] **Step 1: Add the committed-report test first**

The test requires exact filenames, verifies every digest and canonical record,
derives one shared implementation SHA from the three reports, proves it is an
ancestor of HEAD, verifies product-owned probe/contract/lock/runner/generator/stable-script hashes via
historical `git show`, current `HEAD`, and current working-tree bytes, verifies
installed upstream source hashes only through the normalized
RECORD/tree/source map, requires every safety counter zero, requires every
check ID and unresolved gate in exact order, cross-binds the stable tag/file
observations to both contract reports, and asserts no report claims a
real-model evidence kind. It never reads an ephemeral shell variable.

```python
def test_all_required_reports_are_present_and_valid() -> None:
    paths = (
        EVIDENCE / "cp4-4.2.1.1-contract.json",
        EVIDENCE / "cp3-3.1.1.3-contract.json",
        EVIDENCE / "cellpose-stable-release-check.json",
    )
    assert all(path.is_file() for path in paths), "EVIDENCE_MISSING"
    for path in paths:
        verify_report_digest(path)
        report = load_upstream_report(path)
        assert report.outcome == "PASS"
    reports = tuple(load_upstream_report(path) for path in paths)
    implementation_shas = {report.product.commit_sha for report in reports}
    assert len(implementation_shas) == 1
    implementation_sha = implementation_shas.pop()
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", implementation_sha, "HEAD"],
        cwd=ROOT,
        check=True,
    )
```

When the evidence paths are still untracked during GREEN, require
`implementation_sha == git rev-parse HEAD`. Once committed, locate the most
recent commit touching any of the three report paths or their three detached
digests. Require all six paths' individual latest-touch commit to be that same
atomic evidence-update commit, and require that commit's single first parent
to equal `implementation_sha`. Parameterize the assertion over all three
report/digest pairs. This proves the durable implementation-then-evidence
relationship after later commits and still permits a later implementation
commit followed immediately by one atomic six-file replacement-evidence
commit; it never relies on the immutable first-add commit.

- [ ] **Step 2: Run RED**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
[[ $PROBE_ROOT == /* && -d "$PROBE_ROOT" ]]
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
probe_expect_red() {
  PROBE_EXPECTED_RED_STATUS=$1
  PROBE_EXPECTED_RED_SIGNATURE=$2
  shift 2
  set +e
  PROBE_RED_OUTPUT=$("$@" 2>&1)
  PROBE_RED_STATUS=$?
  set -e
  test "$PROBE_RED_STATUS" -eq "$PROBE_EXPECTED_RED_STATUS"
  [[ $PROBE_RED_OUTPUT == *"$PROBE_EXPECTED_RED_SIGNATURE"* ]]
  printf '%s\n' "$PROBE_RED_OUTPUT"
}
probe_expect_red 1 "EVIDENCE_MISSING" /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream/test_committed_reports.py -v
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
test ! -e "$PROBE_ROOT/docs/evidence/upstream/cp4-4.2.1.1-contract.json"
test ! -e "$PROBE_ROOT/docs/evidence/upstream/cp4-4.2.1.1-contract.json.sha256"
test ! -e "$PROBE_ROOT/docs/evidence/upstream/cp3-3.1.1.3-contract.json"
test ! -e "$PROBE_ROOT/docs/evidence/upstream/cp3-3.1.1.3-contract.json.sha256"
test ! -e "$PROBE_ROOT/docs/evidence/upstream/cellpose-stable-release-check.json"
test ! -e "$PROBE_ROOT/docs/evidence/upstream/cellpose-stable-release-check.json.sha256"
```

Expected: failure with `EVIDENCE_MISSING`.

- [ ] **Step 3: Copy only the six verified report/digest files with `apply_patch`**

Derive `PROBE_OUTPUT=/private/tmp/cellpose-mcp-probe-output-${implementation_sha}`
from the shared SHA recorded in both contract reports. Add the canonical report
and digest bytes from that directory to the exact `docs/evidence/upstream/`
paths. Do not regenerate, pretty-print, or edit the JSON by hand.

Write `README.md` with:

- the no-weight/no-download scope;
- the exact eight Task 8 repository paths, distinguishing the six immutable
  report/digest artifacts from this README and the committed-report test;
- exact product commit, runtime versions, Python versions, and lock paths;
- exact offline contract-reproduction commands from Task 6 and the separately
  approved network-capable official-metadata command from Task 7; never call
  the Task 7 metadata fetch offline;
- the six evidence-kind definitions;
- the fact that every check source path is relative to the selected runtime's
  canonical site-packages directory;
- the trusted-process instrumentation scope: Python audit/wrapper guards cover
  the enumerated audited direct `_socket`, UDP, DNS, subprocess, constructor,
  and checkpoint calls from cooperative code, while unaudited private/native
  paths are outside the claim; the report is not an OS-sandbox or
  hostile-native-code containment claim;
- the complete unresolved real-model list;
- the rule that reports bind to the preceding implementation commit; and
- the rule that any runner, generator, stable script, probe, contract, or lock
  change invalidates its report and requires one atomic six-artifact
  replacement evidence commit whose parent is the newly measured clean
  implementation commit. The README's recorded commit/reproduction text must
  be updated in that same replacement commit when it changes.

- [ ] **Step 4: Run GREEN, bind the reports, and commit the exact evidence set**

```bash
set -euo pipefail
PROBE_ROOT=$(pwd -P)
test "$PROBE_ROOT" = "/Users/suraj/Documents/Tools/cellpose_mcp"
test "$(git rev-parse --show-toplevel)" = "$PROBE_ROOT"
test "$(git branch --show-current)" = "codex/cellpose-local-first"
git merge-base --is-ancestor 45021a21604328b268f75f09c4e026ae1cdabec2 HEAD
git diff --cached --quiet
PROBE_PRECOMMIT_HEAD=$(git rev-parse HEAD)
[[ $PROBE_PRECOMMIT_HEAD =~ ^[0-9a-f]{40}$ ]]
PROBE_COMMIT_PATHS=(docs/evidence/upstream/README.md docs/evidence/upstream/cp4-4.2.1.1-contract.json docs/evidence/upstream/cp4-4.2.1.1-contract.json.sha256 docs/evidence/upstream/cp3-3.1.1.3-contract.json docs/evidence/upstream/cp3-3.1.1.3-contract.json.sha256 docs/evidence/upstream/cellpose-stable-release-check.json docs/evidence/upstream/cellpose-stable-release-check.json.sha256 tests/contract/upstream/test_committed_reports.py)
PROBE_COMMIT_SUBJECT="evidence: record pinned Cellpose upstream contracts"
PROBE_REVIEWED_SHA256=$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")
export PROBE_ROOT
PROBE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest())')
[[ $PROBE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ROOT_LOCK_SHA
export PROBE_ROOT_ENV=/private/tmp/cellpose-mcp-probe-root-${PROBE_ROOT_LOCK_SHA}
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_HOME=/private/tmp/cellpose-mcp-probe-package-home-${PROBE_ROOT_LOCK_SHA}
export PROBE_PACKAGE_TMP=/private/tmp/cellpose-mcp-probe-package-tmp-${PROBE_ROOT_LOCK_SHA}
test -d "$PROBE_PACKAGE_HOME"
test -d "$PROBE_PACKAGE_TMP"
PROBE_ROOT_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
[[ $PROBE_ROOT_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I scripts/check_upstream_contract_evidence.py --root docs/evidence/upstream --require-all
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream tests/packaging/test_distribution_contents.py -v --forbid-nonpass-outcomes
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev ruff check --no-cache --no-fix src/cellpose_mcp/release scripts/probe_cellpose_runtime.py scripts/generate_upstream_contract_evidence.py scripts/generate_cellpose_stable_release_check.py scripts/check_upstream_contract_evidence.py tests/contract/upstream
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ROOT_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" run --project "$PROBE_ROOT" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev mypy src/cellpose_mcp/release/upstream_evidence.py src/cellpose_mcp/release/upstream_runner.py
PROBE_ROOT_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ROOT_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ROOT/src")
test "$PROBE_ROOT_PTH_SHA_AFTER" = "$PROBE_ROOT_PTH_SHA_BEFORE"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" lock --project "$PROBE_ROOT/probes/upstream/cp4" --check --offline --no-build --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_PACKAGE_HOME" TMPDIR="$PROBE_PACKAGE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ROOT" lock --project "$PROBE_ROOT/probes/upstream/cp3" --check --offline --no-build --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
git diff --check
test "$(/usr/bin/shasum -a 256 "${PROBE_COMMIT_PATHS[@]}")" = "$PROBE_REVIEWED_SHA256"
git add -- "${PROBE_COMMIT_PATHS[@]}"
git diff --cached --check
PROBE_EXPECTED_CACHED=$(printf '%s\n' "${PROBE_COMMIT_PATHS[@]}" | /usr/bin/sort)
test "$(git diff --cached --name-only | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
for PROBE_PATH in "${PROBE_COMMIT_PATHS[@]}"; do
  test "$(git hash-object "$PROBE_PATH")" = "$(git rev-parse ":$PROBE_PATH")"
done
git commit -m "$PROBE_COMMIT_SUBJECT"
test "$(git rev-parse HEAD^)" = "$PROBE_PRECOMMIT_HEAD"
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
test "$(git log -1 --format=%s)" = "$PROBE_COMMIT_SUBJECT"
test "$(git diff-tree --no-commit-id --name-only -r HEAD | /usr/bin/sort)" = "$PROBE_EXPECTED_CACHED"
git diff --cached --quiet
```

Expected: all commands exit 0 and required test collection has no skip, xfail,
xpass, or deselection.

- [ ] **Step 5: Verify the evidence commit boundary**

Review the single evidence commit produced by Step 4; do not stage or create a
second commit.

### Task 9: Clean-clone acceptance and Phase 1 probe handoff

**Files:** No repository files.

- [ ] **Step 1: Clone the evidence commit locally**

```bash
set -euo pipefail
PROBE_ACCEPTANCE_SHA=$(git rev-parse HEAD)
[[ $PROBE_ACCEPTANCE_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_ACCEPTANCE_SHA
export PROBE_ACCEPTANCE=/private/tmp/cellpose-mcp-probe-acceptance-${PROBE_ACCEPTANCE_SHA}
test ! -e "$PROBE_ACCEPTANCE"
git clone --no-hardlinks --local --no-checkout . "$PROBE_ACCEPTANCE"
git -C "$PROBE_ACCEPTANCE" checkout --detach "$PROBE_ACCEPTANCE_SHA"
test "$(git -C "$PROBE_ACCEPTANCE" rev-parse HEAD)" = "$PROBE_ACCEPTANCE_SHA"
test -z "$(git -C "$PROBE_ACCEPTANCE" branch --show-current)"
test -z "$(git -C "$PROBE_ACCEPTANCE" status --porcelain)"
```

Expected: clean clone; unrelated untracked user files are absent.

- [ ] **Step 2: Re-run every offline acceptance gate**

Verify the evidence commit from its own clean environment:

```bash
set -euo pipefail
PROBE_ACCEPTANCE_SHA=$(git rev-parse HEAD)
[[ $PROBE_ACCEPTANCE_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_ACCEPTANCE_SHA
export PROBE_ACCEPTANCE=/private/tmp/cellpose-mcp-probe-acceptance-${PROBE_ACCEPTANCE_SHA}
test -d "$PROBE_ACCEPTANCE"
test "$(git -C "$PROBE_ACCEPTANCE" rev-parse HEAD)" = "$PROBE_ACCEPTANCE_SHA"
test -z "$(git -C "$PROBE_ACCEPTANCE" branch --show-current)"
test -z "$(git -C "$PROBE_ACCEPTANCE" status --porcelain)"
PROBE_ACCEPTANCE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"uv.lock").read_bytes()).hexdigest())' "$PROBE_ACCEPTANCE")
[[ $PROBE_ACCEPTANCE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ACCEPTANCE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ACCEPTANCE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ACCEPTANCE_ROOT_LOCK_SHA}
export PROBE_ACCEPTANCE_ENV=/private/tmp/cellpose-mcp-probe-acceptance-controller-${PROBE_ACCEPTANCE_SHA}
export PROBE_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-probe-acceptance-home-${PROBE_ACCEPTANCE_SHA}
export PROBE_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-probe-acceptance-tmp-${PROBE_ACCEPTANCE_SHA}
test ! -e "$PROBE_ACCEPTANCE_ENV"
test ! -e "$PROBE_ACCEPTANCE_HOME"
test ! -e "$PROBE_ACCEPTANCE_TMP"
install -d -m 700 "$PROBE_ACCEPTANCE_HOME" "$PROBE_ACCEPTANCE_TMP"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 | /usr/bin/awk '{print $1}')" = "e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --version 2>&1)" = "Python 3.11.14"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" sync --project "$PROBE_ACCEPTANCE" --frozen --offline --no-build --no-install-project --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$PROBE_ACCEPTANCE_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_ACCEPTANCE_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" "$PROBE_ACCEPTANCE_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_ACCEPTANCE_SITE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" "$PROBE_ACCEPTANCE_ENV/bin/python" -B -I -c 'import site; paths=site.getsitepackages(); assert len(paths)==1; print(paths[0])')
[[ $PROBE_ACCEPTANCE_SITE == "$PROBE_ACCEPTANCE_ENV"/*/site-packages ]]
export PROBE_ACCEPTANCE_SITE
PROBE_ACCEPTANCE_PTH_SHA=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" "$PROBE_ACCEPTANCE_ENV/bin/python" -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; target=Path(sys.argv[1]); payload=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.fchmod(fd,0o600); assert os.write(fd,payload)==len(payload); os.fsync(fd); os.close(fd); info=target.lstat(); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert target.read_bytes()==payload; print(hashlib.sha256(payload).hexdigest())' "$PROBE_ACCEPTANCE_SITE/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
[[ $PROBE_ACCEPTANCE_PTH_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_ACCEPTANCE_PTH_SHA
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" run --project "$PROBE_ACCEPTANCE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I scripts/check_upstream_contract_evidence.py --root docs/evidence/upstream --require-all
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" run --project "$PROBE_ACCEPTANCE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev pytest -p no:cacheprovider tests/contract/upstream tests/packaging/test_distribution_contents.py -v --forbid-nonpass-outcomes
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" lock --project "$PROBE_ACCEPTANCE/probes/upstream/cp4" --check --offline --no-build --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" lock --project "$PROBE_ACCEPTANCE/probes/upstream/cp3" --check --offline --no-build --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PROBE_ACCEPTANCE_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ACCEPTANCE_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
test "$PROBE_ACCEPTANCE_PTH_SHA_AFTER" = "$PROBE_ACCEPTANCE_PTH_SHA"
```

Expected: every verifier, test, and lock command exits 0 with no skip, xfail,
xpass, or deselection.

Read the implementation commit from the CP4 report, then reproduce from that
exact clean commit rather than the later evidence commit:

```bash
set -euo pipefail
PROBE_ACCEPTANCE_SHA=$(git rev-parse HEAD)
[[ $PROBE_ACCEPTANCE_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_ACCEPTANCE_SHA
export PROBE_ACCEPTANCE=/private/tmp/cellpose-mcp-probe-acceptance-${PROBE_ACCEPTANCE_SHA}
test -d "$PROBE_ACCEPTANCE"
test "$(git -C "$PROBE_ACCEPTANCE" rev-parse HEAD)" = "$PROBE_ACCEPTANCE_SHA"
test -z "$(git -C "$PROBE_ACCEPTANCE" branch --show-current)"
test -z "$(git -C "$PROBE_ACCEPTANCE" status --porcelain)"
PROBE_ACCEPTANCE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"uv.lock").read_bytes()).hexdigest())' "$PROBE_ACCEPTANCE")
[[ $PROBE_ACCEPTANCE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ACCEPTANCE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ACCEPTANCE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ACCEPTANCE_ROOT_LOCK_SHA}
export PROBE_ACCEPTANCE_ENV=/private/tmp/cellpose-mcp-probe-acceptance-controller-${PROBE_ACCEPTANCE_SHA}
export PROBE_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-probe-acceptance-home-${PROBE_ACCEPTANCE_SHA}
export PROBE_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-probe-acceptance-tmp-${PROBE_ACCEPTANCE_SHA}
test -d "$PROBE_ACCEPTANCE_HOME"
test -d "$PROBE_ACCEPTANCE_TMP"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$PROBE_ACCEPTANCE_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_ACCEPTANCE_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" "$PROBE_ACCEPTANCE_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_ACCEPTANCE_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ACCEPTANCE_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
[[ $PROBE_ACCEPTANCE_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
PROBE_REPRO_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'import json,sys; from pathlib import Path; print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["product"]["commit_sha"])' "$PROBE_ACCEPTANCE/docs/evidence/upstream/cp4-4.2.1.1-contract.json")
[[ $PROBE_REPRO_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_REPRO_SHA
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" run --project "$PROBE_ACCEPTANCE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I scripts/check_upstream_contract_evidence.py --root docs/evidence/upstream --require-all --require-common-product-commit "$PROBE_REPRO_SHA"
test "$(git -C "$PROBE_ACCEPTANCE" rev-parse HEAD^)" = "$PROBE_REPRO_SHA"
test "$(git -C "$PROBE_ACCEPTANCE" rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" -eq 2
export PROBE_REPRO=/private/tmp/cellpose-mcp-probe-reproduction-${PROBE_REPRO_SHA}
export PROBE_REPRO_ENV=/private/tmp/cellpose-mcp-probe-reproduction-controller-${PROBE_REPRO_SHA}
export PROBE_REPRO_HOME=/private/tmp/cellpose-mcp-probe-reproduction-home-${PROBE_REPRO_SHA}
export PROBE_REPRO_TMP=/private/tmp/cellpose-mcp-probe-reproduction-tmp-${PROBE_REPRO_SHA}
export PROBE_REPRO_OUTPUT=/private/tmp/cellpose-mcp-probe-reproduction-output-${PROBE_REPRO_SHA}
test ! -e "$PROBE_REPRO"
test ! -e "$PROBE_REPRO_ENV"
test ! -e "$PROBE_REPRO_HOME"
test ! -e "$PROBE_REPRO_TMP"
test ! -e "$PROBE_REPRO_OUTPUT"
install -d -m 700 "$PROBE_REPRO_HOME" "$PROBE_REPRO_TMP"
test -d "$PROBE_ACCEPTANCE_HOME"
test -d "$PROBE_ACCEPTANCE_TMP"
PROBE_ACCEPTANCE_PTH_SHA_RECHECK=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ACCEPTANCE_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
test "$PROBE_ACCEPTANCE_PTH_SHA_RECHECK" = "$PROBE_ACCEPTANCE_PTH_SHA_BEFORE"
git clone --no-hardlinks --local "$PROBE_ACCEPTANCE" "$PROBE_REPRO"
git -C "$PROBE_REPRO" checkout --detach "$PROBE_REPRO_SHA"
test "$(git -C "$PROBE_REPRO" rev-parse HEAD)" = "$PROBE_REPRO_SHA"
test -z "$(git -C "$PROBE_REPRO" branch --show-current)"
test -z "$(git -C "$PROBE_REPRO" status --porcelain)"
PROBE_REPRO_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"uv.lock").read_bytes()).hexdigest())' "$PROBE_REPRO")
[[ $PROBE_REPRO_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_REPRO_ROOT_LOCK_SHA
test "$PROBE_REPRO_ROOT_LOCK_SHA" = "$PROBE_ACCEPTANCE_ROOT_LOCK_SHA"
PROBE_REPRO_CP4_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"probes/upstream/cp4/uv.lock").read_bytes()).hexdigest())' "$PROBE_REPRO")
[[ $PROBE_REPRO_CP4_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_REPRO_CP4_LOCK_SHA
PROBE_REPRO_CP3_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"probes/upstream/cp3/uv.lock").read_bytes()).hexdigest())' "$PROBE_REPRO")
[[ $PROBE_REPRO_CP3_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_REPRO_CP3_LOCK_SHA
export PROBE_REPRO_CP4_ENV=/private/tmp/cellpose-mcp-probe-reproduction-cp4-${PROBE_REPRO_SHA}-${PROBE_REPRO_CP4_LOCK_SHA}
export PROBE_REPRO_CP3_ENV=/private/tmp/cellpose-mcp-probe-reproduction-cp3-${PROBE_REPRO_SHA}-${PROBE_REPRO_CP3_LOCK_SHA}
PROBE_REPRO_CP4_PROVISIONING_ROOT=/private/tmp/cellpose-mcp-probe-repro-provisioning-${PROBE_REPRO_SHA}-cp4
PROBE_REPRO_CP3_PROVISIONING_ROOT=/private/tmp/cellpose-mcp-probe-repro-provisioning-${PROBE_REPRO_SHA}-cp3
test ! -e "$PROBE_REPRO_CP4_ENV"
test ! -e "$PROBE_REPRO_CP3_ENV"
test ! -e "$PROBE_REPRO_CP4_PROVISIONING_ROOT"
test ! -e "$PROBE_REPRO_CP3_PROVISIONING_ROOT"
install -d -m 700 "$PROBE_REPRO_OUTPUT"
test ! -e "$PROBE_REPRO_OUTPUT/cp4-4.2.1.1-contract.json"
test ! -e "$PROBE_REPRO_OUTPUT/cp4-4.2.1.1-contract.json.sha256"
test ! -e "$PROBE_REPRO_OUTPUT/cp3-3.1.1.3-contract.json"
test ! -e "$PROBE_REPRO_OUTPUT/cp3-3.1.1.3-contract.json.sha256"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/bin/uv | /usr/bin/awk '{print $1}')" = "392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" /Users/suraj/.local/bin/uv --version 2>&1)" = "uv 0.10.4 (079e3fd05 2026-02-17)"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --version 2>&1)" = "Python 3.12.12"
test "$(/usr/bin/shasum -a 256 /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 | /usr/bin/awk '{print $1}')" = "e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --version 2>&1)" = "Python 3.11.14"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" UV_PROJECT_ENVIRONMENT="$PROBE_REPRO_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_REPRO" sync --project "$PROBE_REPRO" --frozen --offline --no-build --no-install-project --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$PROBE_REPRO_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_REPRO_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" "$PROBE_REPRO_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_REPRO_SITE=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" "$PROBE_REPRO_ENV/bin/python" -B -I -c 'import site; paths=site.getsitepackages(); assert len(paths)==1; print(paths[0])')
[[ $PROBE_REPRO_SITE == "$PROBE_REPRO_ENV"/*/site-packages ]]
export PROBE_REPRO_SITE
PROBE_REPRO_PTH_SHA=$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" "$PROBE_REPRO_ENV/bin/python" -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; target=Path(sys.argv[1]); payload=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.fchmod(fd,0o600); assert os.write(fd,payload)==len(payload); os.fsync(fd); os.close(fd); info=target.lstat(); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert target.read_bytes()==payload; print(hashlib.sha256(payload).hexdigest())' "$PROBE_REPRO_SITE/cellpose_mcp_probe_source.pth" "$PROBE_REPRO/src")
[[ $PROBE_REPRO_PTH_SHA =~ ^[0-9a-f]{64}$ ]]
export PROBE_REPRO_PTH_SHA
test ! -e "$PROBE_REPRO_CP4_ENV"
test ! -e "$PROBE_REPRO_CP3_ENV"
cd "$PROBE_REPRO"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_REPRO_ENV/bin/python" -B -I -S "$PROBE_REPRO/scripts/generate_upstream_contract_evidence.py" contract --runtime cp4 --environment "$PROBE_REPRO_CP4_ENV" --cache "$PROBE_UV_CACHE" --provisioning-home "$PROBE_REPRO_CP4_PROVISIONING_ROOT/home" --provisioning-tmp "$PROBE_REPRO_CP4_PROVISIONING_ROOT/tmp" --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --uv /Users/suraj/.local/bin/uv --output "$PROBE_REPRO_OUTPUT/cp4-4.2.1.1-contract.json"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_REPRO_HOME" TMPDIR="$PROBE_REPRO_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 "$PROBE_REPRO_ENV/bin/python" -B -I -S "$PROBE_REPRO/scripts/generate_upstream_contract_evidence.py" contract --runtime cp3 --environment "$PROBE_REPRO_CP3_ENV" --cache "$PROBE_UV_CACHE" --provisioning-home "$PROBE_REPRO_CP3_PROVISIONING_ROOT/home" --provisioning-tmp "$PROBE_REPRO_CP3_PROVISIONING_ROOT/tmp" --python /Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11 --uv /Users/suraj/.local/bin/uv --output "$PROBE_REPRO_OUTPUT/cp3-3.1.1.3-contract.json"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" run --project "$PROBE_ACCEPTANCE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I scripts/check_upstream_contract_evidence.py --compare-invariants docs/evidence/upstream/cp4-4.2.1.1-contract.json "$PROBE_REPRO_OUTPUT/cp4-4.2.1.1-contract.json"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" run --project "$PROBE_ACCEPTANCE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I scripts/check_upstream_contract_evidence.py --compare-invariants docs/evidence/upstream/cp3-3.1.1.3-contract.json "$PROBE_REPRO_OUTPUT/cp3-3.1.1.3-contract.json"
PROBE_ACCEPTANCE_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ACCEPTANCE_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
test "$PROBE_ACCEPTANCE_PTH_SHA_AFTER" = "$PROBE_ACCEPTANCE_PTH_SHA_BEFORE"
PROBE_REPRO_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_REPRO_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_REPRO/src")
test "$PROBE_REPRO_PTH_SHA_AFTER" = "$PROBE_REPRO_PTH_SHA"
```

Expected: both invariant comparisons exit 0. All check observations, hashes,
guards, versions, locks, source bindings, and unresolved gates match the
committed reports.

- [ ] **Step 3: Reconfirm the repository and release boundaries**

```bash
set -euo pipefail
git diff --cached --quiet
git status --short
PROBE_ACCEPTANCE_SHA=$(git rev-parse HEAD)
[[ $PROBE_ACCEPTANCE_SHA =~ ^[0-9a-f]{40}$ ]]
export PROBE_ACCEPTANCE_SHA
export PROBE_ACCEPTANCE=/private/tmp/cellpose-mcp-probe-acceptance-${PROBE_ACCEPTANCE_SHA}
test -d "$PROBE_ACCEPTANCE"
test "$(git -C "$PROBE_ACCEPTANCE" rev-parse HEAD)" = "$PROBE_ACCEPTANCE_SHA"
test -z "$(git -C "$PROBE_ACCEPTANCE" branch --show-current)"
test -z "$(git -C "$PROBE_ACCEPTANCE" status --porcelain)"
PROBE_ACCEPTANCE_ROOT_LOCK_SHA=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,sys; print(hashlib.sha256((Path(sys.argv[1])/"uv.lock").read_bytes()).hexdigest())' "$PROBE_ACCEPTANCE")
[[ $PROBE_ACCEPTANCE_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
test "$PROBE_ACCEPTANCE_ROOT_LOCK_SHA" = "dff524cf92d715606b0ac29f7ace5209558184d683b179ad19d32620b2f2fc6b"
export PROBE_ACCEPTANCE_ROOT_LOCK_SHA
export PROBE_UV_CACHE=/private/tmp/cellpose-mcp-probe-uv-cache-${PROBE_ACCEPTANCE_ROOT_LOCK_SHA}
export PROBE_ACCEPTANCE_ENV=/private/tmp/cellpose-mcp-probe-acceptance-controller-${PROBE_ACCEPTANCE_SHA}
export PROBE_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-probe-acceptance-home-${PROBE_ACCEPTANCE_SHA}
export PROBE_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-probe-acceptance-tmp-${PROBE_ACCEPTANCE_SHA}
test -d "$PROBE_ACCEPTANCE_HOME"
test -d "$PROBE_ACCEPTANCE_TMP"
test "$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve(strict=True))' "$PROBE_ACCEPTANCE_ENV/bin/python")" = "/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"
test "$(/usr/bin/shasum -a 256 "$PROBE_ACCEPTANCE_ENV/bin/python" | /usr/bin/awk '{print $1}')" = "6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483"
test "$(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" "$PROBE_ACCEPTANCE_ENV/bin/python" --version 2>&1)" = "Python 3.12.12"
PROBE_ACCEPTANCE_PTH_SHA_BEFORE=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ACCEPTANCE_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
[[ $PROBE_ACCEPTANCE_PTH_SHA_BEFORE =~ ^[0-9a-f]{64}$ ]]
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$PROBE_ACCEPTANCE_HOME" TMPDIR="$PROBE_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT="$PROBE_ACCEPTANCE_ENV" UV_CACHE_DIR="$PROBE_UV_CACHE" /Users/suraj/.local/bin/uv --directory "$PROBE_ACCEPTANCE" run --project "$PROBE_ACCEPTANCE" --frozen --offline --no-sync --no-python-downloads --no-config --python /Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 --extra test --extra dev python -B -I -c 'from cellpose_mcp.release.feature_manifest import BOOTSTRAP_BLOCKER,CORE_TOOLS,load_feature_manifest,release_gate_failures; failures=release_gate_failures(load_feature_manifest()); expected=(("unresolved_core_matrix",BOOTSTRAP_BLOCKER),)+tuple(("missing_stable_tool",tool) for tool in CORE_TOOLS); assert tuple((item.code,item.subject) for item in failures)==expected and len(failures)==14'
PROBE_ACCEPTANCE_PTH_SHA_AFTER=$(/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 -B -I -c 'from pathlib import Path; import hashlib,os,stat,sys; path=Path(sys.argv[1]); info=path.lstat(); expected=(str(Path(sys.argv[2]).resolve(strict=True))+"\n").encode("utf-8"); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid==os.getuid(); assert stat.S_IMODE(info.st_mode)==0o600; assert path.read_bytes()==expected; print(hashlib.sha256(expected).hexdigest())' "$PROBE_ACCEPTANCE_ENV/lib/python3.12/site-packages/cellpose_mcp_probe_source.pth" "$PROBE_ACCEPTANCE/src")
test "$PROBE_ACCEPTANCE_PTH_SHA_AFTER" = "$PROBE_ACCEPTANCE_PTH_SHA_BEFORE"
```

Expected: empty index, all pre-existing user work remains unstaged, and the
bootstrap feature manifest still exits 1 with 14 blockers. Contract reports do
not promote any tool.

- [ ] **Step 4: Stop before domain-contract implementation**

Summarize the observed CP4 and CP3 boundary, list every unresolved real-model
gate, and request review before the separate domain-contract plan freezes
runtime-dependent enums. Do not construct or download a model, implement a
worker, delete legacy code, publish GitHub artifacts, or upload to PyPI.

## Definition of done

- [ ] Phase 0 remains green from a clean clone and the bootstrap release gate
  remains blocked.
- [ ] Probe projects are private, disjoint, exact-version, exact-Python, checked
  locks with registry artifact hashes and no root/product editable source.
- [ ] Final CP4 and CP3 evidence comes only from runner-owned fresh isolated
  environments created by recorded frozen, offline, no-build,
  no-Python-download, no-config syncs and probed
  by the environment's absolute Python in isolated mode, without a resolver or
  sync wrapper.
- [ ] The repository root and `src/` are absent from runtime `sys.path`; user
  site is disabled; imported Cellpose paths live beneath the selected
  environment.
- [ ] Audited network and process-spawn attempts, model constructor calls,
  checkpoint loads/saves,
  model-cache changes, unapproved writes, and SSL-context changes are all zero.
- [ ] Every required CP4 and CP3 check ID executes and passes with a truthful
  evidence kind and installed-source hash/line binding.
- [ ] Canonical CP4, CP3, and stable-version reports plus detached digests are
  committed and bind to the preceding clean implementation commit.
- [ ] The official report confirms or fails closed on the current stable CP4
  and both required official tag commits.
- [ ] Every real inference, training, restoration, cancellation, MPS, DINO,
  installed-product, and scientific-correctness requirement remains explicitly
  unresolved.
- [ ] No current user file is deleted, moved, overwritten, staged, or claimed
  as supported by these probes.
- [ ] Packaging tests may build only disposable local artifacts; no release
  artifact is retained, uploaded, tagged, or published.
