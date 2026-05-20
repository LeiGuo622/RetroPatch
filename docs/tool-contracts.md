# Tool Contracts

RetroPatch exposes repository operations to the LLM through LangChain tools. These contracts are important because prompt wording, agent behavior, and validation logic all depend on the same assumptions.

## Main Backporting Tools

The main backporting tools are created by `Project.get_tools()` in `src/tools/project.py`.

```python
viewcode, locate_symbol, validate, git_history, git_show = project.get_tools()
```

### `viewcode(ref, path, startline, endline)`

**Purpose:** Inspect source code from a specific Git ref.

Inputs:

- `ref`: commit hash or ref in `project_dir`
- `path`: repository-relative file path
- `startline`: 1-based first line to show
- `endline`: 1-based last line to show

Output:

- selected file lines with a short preface
- an error string if the file does not exist at the ref

Important behavior:

- The tool reads from the Git object database, not necessarily from the checked-out working tree.
- If `endline` exceeds file length, the tool shifts the start line backward and reports the adjusted range.
- The prompt instructs the agent to copy patch context from `viewcode` output rather than from the newer patch.

Use when:

- validating the exact target-version context for a generated hunk
- inspecting symbols returned by `locate_symbol`
- checking candidate locations from history or file-move feedback

### `locate_symbol(ref, symbol)`

**Purpose:** Locate a function, struct, variable, or other ctags-visible symbol in a specific ref.

Inputs:

- `ref`: commit hash or ref
- `symbol`: symbol name to search

Output:

- one or more `file:line` entries
- if exact lookup fails, a message containing a similar symbol when available

Important behavior:

- The first lookup for a ref checks out that ref and runs `ctags --excmd=number -R .`.
- Results are cached in `Project.symbol_map`.
- Similar-symbol fallback uses Levenshtein distance.

Use when:

- the hunk header names a function
- a symbol was renamed between versions
- the agent needs a stable starting point before calling `viewcode`

### `git_history()`

**Purpose:** Retrieve commit history for the line range associated with the current hunk.

Inputs:

- no direct tool arguments
- uses `Project.now_hunk`, `Project.now_hunk_num`, `target_release`, and `new_patch_parent`

Output:

- truncated Git `-L` history for the hunk range
- instructions telling the agent how to reason about the last commit and whether to use `git_show`

Important behavior:

- Computes the merge base between `target_release` and `new_patch_parent`.
- Runs line-history analysis from the merge base to the newer vulnerable revision.
- Stores hunk-related commit IDs for later `git_show()`.

Use when:

- context changed and the agent needs to understand why
- symbol lookup is not enough
- a hunk may correspond to moved or newly introduced code

### `git_show()`

**Purpose:** Inspect the last relevant commit found by `git_history()`.

Inputs:

- no direct tool arguments
- depends on previous `git_history()` state

Output:

- short commit stat
- a summarized explanation of whether the code appears to be moved, changed, or newly introduced
- candidate file and line information when a similar context is found

Important behavior:

- Returns a generic error message if `git_history()` was not run first or produced no usable state.
- Uses context similarity to identify likely moved code blocks.
- The output is advisory; the agent should confirm with `viewcode`.

Use when:

- `git_history()` suggests the hunk's code originated in a previous commit
- the relevant function does not exist in the target version under the same name
- the agent needs to decide between backporting to another location and marking a hunk as not needed

### `validate(ref, patch)`

**Purpose:** Apply a candidate hunk or validate a complete patch, depending on workflow state.

Inputs:

- `ref`: target commit or ref
- `patch`: unified diff text, or text containing `need not ported` for a hunk that should not be backported

Output:

- success text when the patch applies or validation passes
- context mismatch feedback
- file-move feedback
- compile/test/PoC failure feedback in full-patch mode

Important behavior:

- In hunk mode, `validate` delegates to `_apply_hunk()`.
- In full-patch mode, `validate` delegates through `_compile_patch()`, `_run_testcase()`, and `_run_poc()`.
- If `patch` contains `need not ported` before all hunks are complete, the current hunk is treated as succeeded.
- Validation mutates and resets the target working tree.

Use when:

- every generated hunk must be checked before it is accepted
- the complete patch must be tested against build/test/PoC hooks
- the agent needs concrete feedback instead of guessing

## Patch Feedback Semantics

`_apply_hunk()` classifies common failures:

- `No such file`: Triggers file-move handling. RetroPatch tries Git rename history, symbol lookup, and similar filenames, then returns candidate paths and apply feedback.
- `corrupt patch`: Returns a formatting-oriented error message.
- Context mismatch: Finds the most similar target code block, compares patch context against target context line by line, and returns a context diff for the agent.

After repeated context mismatches, `revise_context=True` enables more aggressive context correction in `utils.revise_patch()`.

## Prejudge Tools

The prejudge LLM agent uses a smaller tool set from `src/prejudge/judge_tools.py`.

### `locate_symbol(symbol)`

**Purpose:** Search the target kernel tree for a symbol.

Inputs:

- `symbol`: key function, variable, struct, or macro-like name from the patch

Output:

- candidate locations in the target project
- a not-found response when no symbol is found

Use when:

- deciding whether vulnerable code exists in the target kernel
- finding a target-side file before calling `view_code`

### `view_code(file_path, start_line, end_line)`

**Purpose:** Inspect target-kernel source code around a known file and line range.

Inputs:

- `file_path`: target-project-relative path
- `start_line`: first line
- `end_line`: last line

Output:

- source lines from the target project
- error feedback if the file or range cannot be read

Use when:

- confirming that a vulnerable pattern exists
- checking whether similar code has already been fixed or removed

## Contract Maintenance Rules

When changing tool behavior:

- update `src/agent/prompt.py` if main tool inputs or outputs change
- update `src/prejudge/judge_prompt.py` if prejudge tool behavior changes
- preserve compact verdict strings in prejudge unless intentionally changing downstream interfaces
- add or update tests around failure text that the agent depends on
- keep tool outputs concise enough for LLM context limits
