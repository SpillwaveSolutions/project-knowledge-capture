---
name: pkc-setup
description: Check PKC toolchain (python, ripgrep, SQLite FTS5) and optionally install ripgrep after the user consents. Use when search/pack is slow, rg is missing, or the user asks to set up PKC.
---

# PKC Setup

Ripgrep is an **accelerator**, not a dependency. Search and pack full-scan when `rg` is missing. Never install packages from a hook.

## Process

1. Detect:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_setup.py" --check
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_doctor.py" --repo . --json
   ```
2. If `rg` is found, stop. Report the path.
3. If `rg` is missing, **show the user** the platform command and wait for consent:
   - macOS: `brew install ripgrep`
   - Debian/Ubuntu: `sudo apt-get install -y ripgrep`
   - Fedora: `sudo dnf install -y ripgrep`
   - Windows: `winget install BurntSushi.ripgrep.MSVC`
   - any (Rust): `cargo install ripgrep`
4. Only after the user agrees, run:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_setup.py" --install-rg --yes
   ```
   Without `--yes` the script prints the command and exits 2.
5. Override path with `PKC_RG_PATH` / `OKF_RG_PATH` if rg is installed off PATH.

## Never

- Do not run `--install-rg --yes` from `SessionStart`, `PostToolUse`, or any other hook.
- Do not `pip install` anything. PKC stays zero-dep; `rg` on PATH is the only extra.
- Do not install Ruby, and do not add a Ruby implementation.

## Done when

- Toolchain report shown
- rg found, or user declined install and knows the full-scan fallback still works
