# Configuration Reference

The main backporting CLI reads a YAML file through `load_yml()` in `src/backporting.py`.

Run:

```shell
python src/backporting.py --config case.yml
```

or:

```shell
python src/backporting.py --config case.yml --debug
```

## Example

```yaml
project: libtiff
project_url: https://github.com/libsdl-org/libtiff
new_patch: 881a070194783561fd209b7c789a4e75566f7f37
new_patch_parent: 6bb0f1171adfcccde2cd7931e74317cccb7db845
target_release: 13f294c3d7837d630b3e9b08089752bc07b730e6
sanitizer: LeakSanitizer
error_message: "ERROR: LeakSanitizer"
tag: CVE-2023-3576
openai_key: sk-...
project_dir: dataset/libsdl-org/libtiff
patch_dataset_dir: ~/backports/patch_dataset/libtiff/CVE-2023-3576/

use_azure: false
# azure_endpoint: "https://your-resource.openai.azure.com/"
# azure_deployment: "gpt-5"
# azure_api_version: "2024-12-01-preview"
```

## Required Fields

- `project`: Human-readable project name used in log filenames.
- `project_url`: Upstream repository URL passed to the LLM as project context.
- `project_dir`: Local Git repository that contains `new_patch`, `new_patch_parent`, and `target_release`. This directory is mutated during runtime.
- `patch_dataset_dir`: Case directory containing optional validation hooks and receiving a copy of the runtime log.
- `new_patch`: Upstream fixed commit. RetroPatch reads this commit with `git show` and splits the resulting patch into hunks.
- `new_patch_parent`: Parent or vulnerable-side commit for `new_patch`. This gives the agent a newer vulnerable reference for history tracing.
- `target_release`: Older revision that should receive the backported fix.
- `openai_key`: API key used by the main backporting LLM path. Azure mode also reads this field as the Azure OpenAI key.

## Optional Fields

- `tag`: Case identifier used in log filenames. Common values are CVE IDs or bug IDs.
- `sanitizer`: Metadata describing the sanitizer used by the case. The current main workflow does not make decisions from this field.
- `error_message`: Text expected in `poc.sh` output when the bug is still triggered. If this field is empty, `Project` uses a placeholder value and the run logs a warning.
- `use_azure`: Boolean selecting the Azure OpenAI client path. Defaults to `false`.
- `azure_endpoint`: Azure OpenAI endpoint. Required when `use_azure: true`.
- `azure_deployment`: Azure OpenAI deployment name. Defaults to `gpt-4` in the loader if omitted.
- `azure_api_version`: Azure OpenAI API version. Defaults to `2024-12-01-preview`.

## Path Rules

`project_dir` and `patch_dataset_dir` are expanded with `os.path.expanduser()`.

If either path does not end with `/`, the loader appends `/` internally. This means string concatenation in the current code assumes trailing slash behavior.

Both directories must already exist. The loader exits if either is missing.

## Commit Rules

The loader verifies these values against `project_dir`:

- `new_patch`
- `new_patch_parent`
- `target_release`

Each value must resolve to a valid commit in the target repository. After validation, the loader replaces each value with its full hash via `git rev-parse`.

## Main LLM Selection

The current main workflow has two model paths:

- regular OpenAI, configured in `src/agent/invoke_llm.py`
- Azure OpenAI, selected with `use_azure: true`

Regular OpenAI currently uses a hard-coded model and base URL in code. Azure mode reads deployment and endpoint fields from YAML.

## Prejudge Configuration

The prejudge pipeline does not use this YAML file.

Prejudge is invoked with CLI arguments:

```shell
python src/prejudge/prejudge.py <commit-id> <kernel-source-dir> <target-project-dir>
```

The LLM-backed prejudge path expects `OPENROUTER_API_KEY` in the environment and model provider settings from `src/prejudge/judge_agent.py`.

## Validation Hook Contract

The case directory can provide:

- `build.sh`
- `test.sh`
- `poc.sh`

Before full validation, files from `patch_dataset_dir` are copied into the target repository root.

If a hook is missing, the corresponding stage is treated as passed. Provide hooks deliberately based on the assurance level needed for the case.

## Pre-Run Checklist

Before running:

```shell
python3 skills/retropatch-engineering/scripts/check_setup.py --config case.yml
git -C <project_dir> status --short
```

Confirm:

- `project_dir` is a disposable clone
- all three commit fields resolve
- `patch_dataset_dir` exists
- validation scripts are intentionally named and safe to copy
- the selected API credentials are available
