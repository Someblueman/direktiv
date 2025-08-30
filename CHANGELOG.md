# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and the project adheres to Semantic Versioning.

## 0.3.0 - 2025-08-30

- Feature: Unified “Add Documents” flow with multi-select.
  - Space toggles selection for files and directories.
  - Enter confirms only when items are selected; otherwise opens folders.
  - Selecting a directory imports all `.md` files recursively into the chosen category.
- Feature: Hidden toggle now applies to Add/Import modals via a filtered directory tree.
- Refactor: Introduced `FilteredDirectoryTree` to support hiding dotfiles.
- UX: Updated key bindings — `a` now opens “Add Documents” (removed separate `i` import in TUI).
- Fix: Avoided `TreeNode.clear()` (not in Textual 5.3.0); use `remove_children()`.

## 0.2.0 - 2025-08-01

- Initial alpha release: TUI library browser, markdown viewer, basic add/import flows.

