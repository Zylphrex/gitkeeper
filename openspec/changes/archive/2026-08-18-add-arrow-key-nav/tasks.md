## 1. Bindings

- [x] 1.1 Add `up`/`down`/`left`/`right` entries to `GitkeeperApp.BINDINGS` in `gitkeeper/ui/app.py`, adjacent to their `jk`/`hl` counterparts, mapping to the existing `vim_up`/`vim_down`/`focus_left`/`focus_right` actions with `show=False`

## 2. Tests

- [x] 2.1 Add a test asserting arrow `down`/`up` move the PR list highlight (mirroring `test_vim_jk_moves_pr_list` in `tests/test_ui.py`)
- [x] 2.2 Add a test asserting `right`/`left` move focus across panes per the focus graph (mirroring `test_vim_h_l_focus_movement`)
- [x] 2.3 Add a test asserting focus stays put at focus-graph boundaries when using arrows (mirroring `test_vim_h_l_boundary`)
- [x] 2.4 Add a test asserting arrows inside a modal text input move the text cursor and do not change the underlying pane focus (`test_vim_keys_do_not_fire_in_modal` covers the Vim-key case)

## 3. Verification

- [x] 3.1 Run `pytest` and confirm the full suite passes