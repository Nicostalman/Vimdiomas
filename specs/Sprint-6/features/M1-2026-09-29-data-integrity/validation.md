# M1 · Data integrity — validation

Grounded in the roadmap's done-when condition, made concrete. The roadmap's bar
is "each of the seven findings has a regression test matching the report's
*Regression coverage* line"; with #7 added at spec time it is **eight**.

## Regression coverage, finding by finding

Each row is the report's own *Regression coverage* line, and the test that
satisfies it. Every one of these is **written failing first**, against the
current code, to confirm the finding is still live.

| # | Report's coverage line | Tests, as written |
|---|---|---|
| 1 | delete → rename ancestor → leave; reuse the old path and verify its replacement survives | `test_tui_inspect_tree.py`: `test_renaming_the_parent_does_not_undelete_the_file`, `test_the_marked_file_is_the_one_that_goes_after_a_rename` (the P1 reproduction in full), `test_renaming_an_ancestor_two_levels_up_remaps_the_pending_path`, `test_deleting_a_directory_under_a_renamed_parent_removes_it`, `test_a_replaced_file_is_left_alone_and_the_user_is_told`, `test_a_file_deleted_externally_is_dropped_silently`, `test_undo_after_a_rename_leaves_everything_in_place`, `test_renaming_the_deleted_file_itself_remaps_the_pending_path` |
| 2 | save/reload empty translation, whitespace-only translation, empty leading/trailing fields; both vocabulary and grammar forms | `test_parser.py`: `test_entry_with_empty_translation_parses` (the P1 reproduction), `…empty_leading_field…`, `…both_trailing_fields_empty…`, `test_whitespace_only_translation_parses_as_empty`, `test_space_indented_entry_row_parses_unchanged`, `test_space_padded_fields_are_stripped_individually`, `test_tab_indented_entry_row_reads_as_an_empty_first_field`, `test_extra_fields_beyond_three_still_collected`, `test_extra_fields_may_be_empty`. `test_writer.py`: `test_entry_with_an_empty_field_round_trips` (4 cases). `test_tui_entry_screen.py`: `test_entry_with_an_empty_translation_saves_and_reloads` and its grammar twin. `test_store.py`: `test_walk_survives_every_bad_line_in_the_data_integrity_tier` |
| 3 | parse → write → parse for apostrophes, double quotes, backslashes, and whitespace in tags | `test_writer.py`: `test_rendered_tag_parses_back_to_itself` — the `_parse_tags_line(_render_tag(t)) == [t]` property over a 14-tag corpus — plus `test_apostrophe_tag_round_trips_through_a_whole_file` (the report's `#"don't"` case), `test_tags_already_in_the_tree_are_written_byte_identically` and `test_tags_fixture_round_trips_byte_identically`. `test_parser.py`: `test_unclosed_quote_in_tags_line_warns_instead_of_raising`, `test_quoted_apostrophe_tag_parses` |
| 6 | save/load strings containing both quote types, backslashes, and control characters | `test_config.py`: `test_apostrophe_in_user_name_survives_a_save` (the reproduction), `test_both_quote_characters_and_a_backslash_round_trip` (the done-when case), `test_control_characters_in_user_name_round_trip`, `test_root_path_with_a_quote_and_a_backslash_round_trips`, `test_language_fields_with_quotes_round_trip`, `test_an_ordinary_config_is_written_byte_identically_to_before`, `test_a_broken_encoder_raises_and_leaves_the_existing_config_alone` |
| 7 | finish setup with a relative root, change working directory, then reopen and compile the same notebook | `test_tui_wizard.py`: `test_a_relative_root_is_stored_absolute`, `test_the_tree_is_found_from_a_different_working_directory` (the reproduction). `test_config.py`: `test_relative_root_loads_identically_from_any_working_directory`, `test_a_relative_root_is_not_rewritten_on_load`, `test_an_absolute_root_is_left_exactly_as_stored` |
| 8 | reserved-name creation through vocabulary and grammar forms, with a user-visible validation message and no file mutation | `test_tui_entry_screen.py`: `test_reserved_category_name_is_refused` (`Tags` and `  Tags  `, error notification asserted, file bytes unchanged, no new leaf), `test_reserved_category_name_is_refused_in_a_grammar_file`, `test_lowercase_tags_is_an_ordinary_category_name` (accepted, and an entry added to it straight away doesn't raise the report's `StopIteration`) |
| 15 | paste a tab into each form field, create, reload, assert the fields are unchanged apart from the removed tab | `test_tui_panels.py`: `test_pasted_tab_becomes_a_space_in_the_field`, `test_every_control_character_becomes_a_space`, `test_ordinary_text_and_edge_spaces_are_untouched`, `test_typed_tab_never_reaches_the_value_and_keeps_the_cursor_put`, `test_changed_message_carries_the_sanitised_value`. `test_tui_entry_screen.py`: `test_pasted_tab_in_hanzi_keeps_the_row_three_columns` (the `苹果<TAB>apple` reproduction), `test_pasted_tab_in_any_word_field_becomes_a_space` (hanzi/translation/note), `…in_category_name…`, `…in_subtitle_name…`. `test_writer.py`: the writer's own refusal, per field and per character |
| 18 | duplicate category creation in vocabulary and grammar files | `test_tui_entry_screen.py`: `test_duplicate_category_name_selects_the_existing_category` (nothing written, no second heading, cursor and `_active_target` on the existing leaf, notification asserted, a following entry lands under it), `test_duplicate_category_name_selects_existing_in_a_grammar_file`, `test_category_names_differing_only_in_case_are_both_created` |

**Every test above was run against the unfixed source before the fix landed**
(`git stash push src/idiomas`), and each one that asserts changed behaviour
failed there. The ones that passed both before and after are the deliberate
locks on behaviour that must *not* change — the byte-identical tag and config
output, `tags` as an ordinary category name, two names differing only in case,
`u` after a rename, and a target deleted externally.

## Automated

- `.venv/bin/python -m pytest -q` — the full suite passes. The report's own
  baseline was **696 passed**, confirmed at the start of this branch. **No
  existing test was modified or removed**: all 696 pass against the fixed
  source unchanged, and the new tests are additions.
- The two **P1 reproductions no longer reproduce**, run exactly as the report
  states them:
  - #1: the delete → rename → recreate → leave sequence removes the file that
    was marked, not the one that replaced it.
  - #2: an entry saved with an empty translation re-parses instead of raising
    `ValueError: not enough values to unpack`.
- **No existing file is reformatted.** `test_writer.py` asserts `_render_tag`
  is byte-identical to today's output for a plain and a whitespace-quoted tag
  and that the `Food.md` fixture's tag line survives a rewrite unchanged;
  `test_config.py` asserts `_toml_lines` is byte-identical to `!r`'s output for
  a config with no special characters.
- **The tree survives every bad input in this tier**: `store.walk()` over a
  fixture tree containing a row with an empty field, an unparseable tag line and
  a malformed row returns a tree and a warning per bad line, and raises nothing.

## Manual, by the dev

Against the real tree (`~/Documents/Idiomas/tree-Chinese`). Nothing here needs a
throwaway config except where it says so.

- [ ] **#2.** *Enter vocabulary* → any category. Type a hanzi, leave Translation
      empty, Create. The entry is added. Leave and re-open Entry: the tree still
      builds and the file is intact. Open *Inspect tree*: it opens.
- [ ] **#15.** Copy a row from a spreadsheet (or any two tab-separated words) and
      paste it into Hanzi. The tab shows as a **space** in the field, right away,
      before pressing anything. Create; open the file in MD mode — the row has
      three columns, not five, and the pinyin is not glued to anything.
- [ ] **#8.** `(new category)` → type `Tags` → Create. An error notification
      appears, nothing is added to the tree, and the file is unchanged in MD
      mode. Type `tags` instead: it is created normally.
- [ ] **#18.** `(new category)` → type the name of a category the file already
      has → Create. The cursor jumps to that existing category, a notification
      says it was selected, and the file gains no second heading. Add an entry
      straight away: it lands under the existing heading.
- [ ] **#3.** In MD mode, hand-edit a file's Tags line to include
      `#"don't"`. Back in Entry, add an unrelated entry to that file. Re-open the
      file: the tag is still there and still parses, and Browse's tag filter
      still finds the file.
- [ ] **#1.** *Inspect tree* on a scratch directory: create `Old/` with a file in
      it, delete the file (`d`, confirm) — it disappears. Rename `Old` to `New`
      (`r`). The file **does not reappear**. Leave the screen: `New/` no longer
      has it.
- [ ] **#1, the dangerous half.** Repeat, but after renaming, create a new file
      at the old path (`Old/`, same name) with different content before leaving.
      On leaving, the new file **survives**, and a warning notification names the
      one that was left alone if the identity check fired.
- [ ] **#6 and #7, on a throwaway config only.** Move `~/.config/idiomas/config.toml`
      aside, run `idiomas wizard`, and answer the name step with
      `O'Brien "Nico"\test` and the tree-location step with a **relative** path
      (e.g. `notebooks`). Finish. Then: relaunch `idiomas` from a *different*
      directory — it launches, the name is intact, and it finds the same tree.
      Restore the real config afterwards.
- [ ] **Nothing else changed.** Add a normal entry, a normal category and a
      grammar subtitle; compile; the PDFs are as before.

## Merge bar

All automated checks pass, the eight regression tests above are present and
green, the two P1 reproductions no longer reproduce, and the dev confirms the
manual list.
