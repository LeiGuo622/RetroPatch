# Prompt Design

RetroPatch prompts are designed to make the LLM behave like a tool-using backporting assistant rather than a standalone code generator. The model should inspect the target repository, reason from concrete tool output, generate a patch, validate it, and revise based on feedback.

The prompt definitions live in `src/agent/prompt.py`.

## Design Principles

1. Give the model a precise task.
2. Define the available tools and their arguments.
3. Require target-version context before generating patch context.
4. Split the workflow into hunk-level adaptation and full-patch repair.
5. Treat validation feedback as authoritative.
6. Keep retrieved context focused enough to fit within model limits.
7. Permit `need not ported` when the target version does not contain the relevant code.

## Two Prompt Stages

RetroPatch uses two main prompt stages.

### Stage 1: Hunk Adaptation

**Goal:** Make a single hunk apply to the target revision, or decide that the hunk does not need to be ported.

Inputs include:

- project URL
- newer vulnerable ref
- target ref
- current hunk
- similar target-side code block from failed apply feedback

Available tools:

- `viewcode`
- `locate_symbol`
- `git_history`
- `git_show`
- `validate`

Expected model behavior:

1. Review the hunk and similar target block.
2. Use `git_history` to understand how the hunk context changed.
3. Optionally use `git_show` when history indicates moved or newly introduced code.
4. Use `locate_symbol` to find relevant functions or data structures.
5. Use `viewcode` to inspect target-version context.
6. Generate a unified diff for the target version.
7. Call `validate` on the generated hunk.
8. Revise until validation succeeds or a no-port decision is justified.

### Stage 2: Full-Patch Repair

**Goal:** Validate and revise the joined patch after all hunks individually apply.

Inputs include:

- original upstream patch
- target revision
- joined complete patch
- compile/test/PoC feedback from validation

Available tools:

- `viewcode`
- `locate_symbol`
- `validate`

Expected model behavior:

1. Inspect validation failure output.
2. Locate missing or renamed symbols if compilation failed.
3. Use `viewcode` to understand target-side definitions and constraints.
4. Revise the complete patch, preserving unrelated hunks.
5. Call `validate` again.

This stage catches integration problems that hunk-level apply checks cannot detect, such as missing fields, renamed locks, unavailable macros, and incomplete cleanup paths.

## Why Hunk-Level Prompting

Large patches often exceed the amount of useful context that should be given to a model at once. Hunk-level prompting keeps each conflict focused:

- The model sees one local problem.
- Tool feedback stays relevant.
- `git_history` can target a specific line range.
- Successful simple hunks do not consume extra LLM budget.

The tradeoff is that dependencies between hunks can be missed. The full-patch repair stage partially compensates for that by validating the combined result.

## Tool-First Reasoning

The prompts intentionally discourage patch generation from memory. The model is told to use:

- `git_history` for provenance and namespace changes
- `git_show` for moved or newly introduced code
- `locate_symbol` for navigation
- `viewcode` for exact target context
- `validate` for authoritative apply/build/test/PoC feedback

This matters because the newer patch context may not exist in the target version. Context lines in the generated patch must match the target source code.

## Patch Formatting Requirements

Prompts require unified diff format:

```diff
--- a/path/to/file.c
+++ b/path/to/file.c
@@ -10,6 +10,9 @@
 context line
-removed line
+added line
 context line
```

Patch lines must begin with:

- `+` for additions
- `-` for deletions
- a single space for unchanged context

The prompt asks for at least three lines of context at the beginning and end of a hunk when possible. The patch must not use placeholders such as `...`.

## `need not ported`

Some hunks are not relevant to the target version. This can happen when:

- the code was introduced after the target branch
- the vulnerable helper does not exist in the target
- the target already implements the fix differently
- a hunk only adjusts code that is absent from the target

In hunk mode, the model may pass `need not ported` to `validate`. The tool then treats the current hunk as complete. This should be used only after tool-backed investigation.

## Feedback-Driven Revision

Validation feedback is part of the prompt loop.

Context mismatch feedback tells the model:

- where similar target code was found
- which patch context lines differ from target source
- how to align the next patch attempt

File-not-found feedback tells the model:

- candidate renamed or similar files
- whether applying to those files succeeded
- which path should be used in the next patch

Compile/test/PoC feedback tells the model:

- which symbol, field, macro, or behavior failed
- whether the failure is mechanical or semantic
- where to inspect next with `locate_symbol` or `viewcode`

The model should not repeat the same patch after feedback identifies a concrete mismatch.

## Prompt Maintenance Guidelines

When editing prompts:

- keep tool names and argument descriptions synchronized with `src/tools/project.py`
- keep stage-specific workflows short enough to be followed
- avoid adding broad repository summaries that increase context without guiding action
- preserve the instruction to validate generated patches
- preserve the instruction to use target-side context from `viewcode`
- update this document when adding, removing, or renaming tools

Prompt changes should be tested on at least one case where:

- the original hunk applies directly
- context mismatch requires a rewritten hunk
- a symbol rename must be resolved
- full-patch validation exposes a compile error
