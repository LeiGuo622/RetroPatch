# Runtime Safety

RetroPatch is designed to run against disposable target repositories. The main workflow performs destructive Git cleanup inside the configured `project_dir`; do not run it against a working tree that contains valuable uncommitted work.

## What Can Be Modified

During an end-to-end backporting run, RetroPatch may:

- run `git reset --hard` inside `project_dir`
- run `git clean -fdx` inside `project_dir`
- checkout different commits inside `project_dir`
- apply candidate hunks and full patches inside `project_dir`
- copy files from `patch_dataset_dir` into the root of `project_dir`
- remove same-named files in `project_dir` before copying validation scripts
- create runtime logs under `../logs` relative to the current working directory
- copy the final log file into `patch_dataset_dir`

These behaviors are useful for repeatable validation, but they are unsafe for a repository that is also used for normal development.

## Required Workspace Discipline

Use this pattern for real runs:

```shell
git clone <project-url> dataset/<project-name>
python src/backporting.py --config case.yml
```

The clone referenced by `project_dir` should be treated as scratch space. Keep your real development clone somewhere else.

Before running the main workflow, check:

```shell
git -C <project_dir> status --short
git -C <project_dir> rev-parse --is-inside-work-tree
```

The first command should produce no output unless you are intentionally allowing those changes to be deleted.

## Dataset Script Copying

Before full validation, RetroPatch copies every file from `patch_dataset_dir` into `project_dir`.

Typical files are:

```text
patch_dataset_dir/
  build.sh
  test.sh
  poc.sh
```

If a file with the same name already exists in the target repository root, it may be removed and replaced. Keep validation scripts in a dedicated case directory and avoid using generic names for unrelated files in the target root.

## Validation Hooks

Validation hooks execute from `project_dir`:

- `build.sh` builds the patched target project
- `test.sh` runs regression or functionality tests
- `poc.sh` runs a bug trigger or proof of concept

If a hook is absent, RetroPatch treats that stage as passed. This is convenient for partial validation but can make a patch look safer than it really is. For security-sensitive cases, provide at least `build.sh` and the strongest available testcase or PoC.

## Secrets And Logs

Avoid placing API keys directly in shared config files. The current YAML contract supports `openai_key`, but operationally it is safer to keep secrets out of version control and load them from local-only config or environment-specific wrappers.

Logs may contain:

- commit IDs
- repository paths
- generated patches
- tool feedback
- compile and test errors
- model outputs

Do not publish logs from private repositories without review.

## Safe Commands

Use the setup checker before a real run:

```shell
python3 skills/retropatch-engineering/scripts/check_setup.py --config path/to/case.yml
```

Use syntax checks for code-only edits:

```shell
python3 -m compileall -q src test
```

Use end-to-end backporting only when the configured `project_dir` and `patch_dataset_dir` are intentionally prepared for mutation.

## Common Unsafe Situations

Avoid these situations:

- `project_dir` points to your main development clone
- `project_dir` has uncommitted source changes
- `project_dir` contains important untracked files
- `patch_dataset_dir` contains files that should not be copied into the target root
- `build.sh`, `test.sh`, or `poc.sh` run commands that assume a different working directory
- multiple RetroPatch runs target the same `project_dir` concurrently

When in doubt, create a fresh clone and a fresh case directory.

