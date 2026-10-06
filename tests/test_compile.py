import dataclasses
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from vimdiomas import compile as compile_module
from vimdiomas.compile import (
    _pair_hanzi_pinyin,
    compile_all,
    compile_file,
    notebook_path_for,
    render_markdown,
)
from vimdiomas.languages import ALPHABETICAL, CHARACTER_PHONETIC
from vimdiomas.models import Category, Deck, Entry, Subtitle
from vimdiomas.parser import parse


def test_render_markdown_table_structure_and_tone_marks():
    deck = Deck(
        title="Food",
        uncategorized=[Entry(word="苹果", reading="ping2guo3", translation="apple")],
        categories=[
            Category(
                name="Meat",
                entries=[Entry(word="牛肉", reading="niu2rou4", translation="beef")],
            )
        ],
    )

    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)

    assert "title: Food" in markdown
    assert "{\\Large 苹果} & pínguǒ & apple \\\\" not in markdown  # sanity: not garbled (wrong tone)
    assert "{\\Large 苹果} & píngguǒ & apple \\\\" in markdown
    assert "## Meat" in markdown
    assert "{\\Large 牛肉} & niúròu & beef \\\\" in markdown
    assert "```{=latex}" in markdown
    assert r"\begin{longtable}{l@{\hspace{2em}}l@{\hspace{2em}}l}" in markdown
    assert "Hanzi" not in markdown
    assert "Pinyin" not in markdown
    assert "\\toprule" not in markdown


def test_render_markdown_inlines_note():
    deck = Deck(
        title="Food",
        categories=[
            Category(
                name="Vegetables",
                entries=[
                    Entry(
                        word="番茄",
                        reading="fan1qie2",
                        translation="tomato",
                        note="sometimes called 西红柿 in the north",
                    )
                ],
            )
        ],
    )

    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)
    assert r"tomato \textit{(sometimes called 西红柿 in the north)}" in markdown


def test_render_markdown_omits_tags_section():
    deck = Deck(title="Food", tags=["food", "travel"])
    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)
    assert "Tags" not in markdown
    assert "food" not in markdown


def test_render_markdown_escapes_latex_special_characters():
    deck = Deck(
        title="Food",
        uncategorized=[
            Entry(word="百分之五十", reading="bai3fen1zhi5wushi2", translation="50% & up_front #1 {x} $5")
        ],
    )

    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)

    assert r"50\% \& up\_front \#1 \{x\} \$5" in markdown


def test_render_markdown_empty_category_is_bare_heading():
    deck = Deck(
        title="Food",
        categories=[Category(name="New Category", entries=[])],
    )

    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)

    assert "## New Category" in markdown
    assert "longtable" not in markdown


# -- hanzi/pinyin pairing (Sprint 5 M6) ----------------------------------


def test_pair_hanzi_pinyin_pairs_each_character_in_order():
    assert _pair_hanzi_pinyin("天气", "tian1qi4") == [("天", "tiān"), ("气", "qì")]


def test_pair_hanzi_pinyin_non_hanzi_characters_get_no_syllable():
    assert _pair_hanzi_pinyin("...", "") == [(".", ""), (".", ""), (".", "")]


def test_pair_hanzi_pinyin_neutral_tone():
    assert _pair_hanzi_pinyin("好啦", "hao3la5") == [("好", "hǎo"), ("啦", "la")]


def test_pair_hanzi_pinyin_extra_hanzi_past_syllable_list_does_not_raise():
    assert _pair_hanzi_pinyin("你好吗", "ni3hao3") == [
        ("你", "nǐ"),
        ("好", "hǎo"),
        ("吗", ""),
    ]


# -- grammar mode (Sprint 5 M5) ------------------------------------------


def test_render_markdown_emits_subtitle_headings_after_category_entries():
    deck = Deck(
        title="Grammar",
        categories=[
            Category(
                name="Conjunctions",
                entries=[Entry(word="...", reading="", translation="ellipsis")],
                subtitles=[
                    Subtitle(
                        name="copulative conjunction",
                        entries=[Entry(word="和", reading="he2", translation="and")],
                    ),
                    Subtitle(name="disjunctive conjunction", entries=[]),
                ],
            )
        ],
    )

    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)

    ellipsis_index = markdown.index("ellipsis")
    copulative_index = markdown.index("### copulative conjunction")
    entry_index = markdown.index("& hé & and")
    disjunctive_index = markdown.index("### disjunctive conjunction")
    assert ellipsis_index < copulative_index < entry_index < disjunctive_index
    # The empty subtitle is a bare heading: no table follows it.
    assert "longtable" not in markdown[disjunctive_index:]


def test_render_markdown_vocabulary_deck_has_no_subtitle_headings():
    deck, _ = parse("# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n", "Food", kind=CHARACTER_PHONETIC, grammar=False)
    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)
    assert "###" not in markdown


def _conjunctions_deck():
    """Shaped like the dev's real Grammar/Conjunctions.md: a plain category,
    an entry with no reading, an entry with a note, and a subtitle."""
    return Deck(
        title="Grammar",
        categories=[
            Category(
                name="Conjunctions",
                entries=[
                    Entry(word="...", reading="", translation="ellipsis"),
                    Entry(word="好啦", reading="hao3la5", translation="ok then", note="test none"),
                ],
                subtitles=[
                    Subtitle(
                        name="new cat",
                        entries=[Entry(word="和", reading="he2", translation="and")],
                    ),
                ],
            )
        ],
    )


def test_render_markdown_grammar_mode_emits_hanzipinyin_not_longtable():
    markdown = render_markdown(_conjunctions_deck(), kind=CHARACTER_PHONETIC, grammar=True)

    assert r"\HanziPinyin" in markdown
    assert "longtable" not in markdown
    assert f"\\\\[{compile_module.GRAMMAR_PINYIN_GAP}]" in markdown
    assert f"\\\\[{compile_module.GRAMMAR_ENTRY_GAP}]" in markdown


def test_render_markdown_grammar_mode_note_gets_its_own_line():
    """The note sits on its own line below the translation, not beside it
    (M6, second manual pass), and closes the entry with the large gap."""
    lines = render_markdown(_conjunctions_deck(), kind=CHARACTER_PHONETIC, grammar=True).splitlines()

    translation = lines.index(r"ok then \\")
    assert lines[translation + 1].startswith(r"\textit{(test none)}")


def test_render_markdown_grammar_mode_block_ends_paragraph_with_entry_gap():
    """Each entries block's last entry ends the paragraph with the entry gap
    as a plain \\vspace, not a trailing \\\\[...] — that would add an empty
    line, making the gap before the next subtitle larger than between two
    entries (M6, third manual pass)."""
    markdown = render_markdown(_conjunctions_deck(), kind=CHARACTER_PHONETIC, grammar=True)
    gap = compile_module.GRAMMAR_ENTRY_GAP

    for block in markdown.split("```{=latex}")[1:]:
        last_line = block.split("```")[0].rstrip().splitlines()[-1]
        assert last_line.endswith(rf"\par\vspace{{{gap}}}")


def test_render_markdown_grammar_mode_each_entries_block_is_noindent():
    """A grammar entries block is one raw LaTeX paragraph (M6) — unlike
    `_render_table`'s `longtable`, it's subject to \\parindent, so each
    block starts with an explicit \\noindent rather than relying on
    whatever heading (if any) precedes it."""
    markdown = render_markdown(_conjunctions_deck(), kind=CHARACTER_PHONETIC, grammar=True)

    for block in markdown.split("```{=latex}")[1:]:
        assert block.lstrip().startswith(r"\noindent")


def test_render_markdown_grammar_mode_no_reading_entry_has_three_empty_pairs():
    markdown = render_markdown(_conjunctions_deck(), kind=CHARACTER_PHONETIC, grammar=True)

    assert markdown.count(r"\HanziPinyin{.}{}") == 3


def test_render_markdown_grammar_mode_false_is_byte_for_byte_vocabulary_output():
    deck = Deck(
        title="Food",
        uncategorized=[Entry(word="苹果", reading="ping2guo3", translation="apple")],
        categories=[
            Category(name="Meat", entries=[Entry(word="牛肉", reading="niu2rou4", translation="beef")])
        ],
    )

    assert render_markdown(deck, kind=CHARACTER_PHONETIC) == render_markdown(deck, kind=CHARACTER_PHONETIC, grammar=False)
    assert r"\begin{longtable}" in render_markdown(deck, kind=CHARACTER_PHONETIC, grammar=False)


def test_compile_file_passes_grammar_flag_to_render_markdown(tmp_path, monkeypatch):
    render_calls = []
    original_render_markdown = compile_module.render_markdown

    def _recording_render_markdown(deck, **kwargs):
        render_calls.append(kwargs.get("grammar", False))
        return original_render_markdown(deck, **kwargs)

    monkeypatch.setattr(compile_module, "render_markdown", _recording_render_markdown)
    monkeypatch.setattr(compile_module.subprocess, "run", lambda args, **kwargs: None)

    source_file = tmp_path / "G.md"
    source_file.write_text("# G\n\n和\the2\tand\n", encoding="utf-8")
    notebook_file = tmp_path / "G.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC, grammar=True)
    assert render_calls == [True]


@pytest.mark.integration
def test_compile_all_grammar_conjunctions_shape_produces_pdf_with_content(tmp_path):
    pypdf = pytest.importorskip("pypdf")

    tree_root = tmp_path / "tree-Chinese"
    (tree_root / "Grammar").mkdir(parents=True)
    grammar_source = tree_root / "Grammar" / "Conjunctions.md"
    grammar_source.write_text(
        "# Conjunctions\n\n"
        "## Conjunctions\n\n"
        "...\t\tellipsis\n"
        "好啦\thao3la5\tok then\n\n"
        "### new cat\n\n"
        "和\the2\tand\n",
        encoding="utf-8",
    )

    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled

    notebook_file = tree_root / "Grammar" / "Conjunctions.pdf"
    assert compiled == [notebook_file]
    assert notebook_file.exists()

    reader = pypdf.PdfReader(str(notebook_file))
    text = "".join(page.extract_text() for page in reader.pages)
    # Each hanzi character sits in its own \HanziPinyin box, so extracted
    # text has them on separate lines rather than as a contiguous "好啦".
    assert "好" in text
    assert "啦" in text
    assert "hǎo" in text
    assert "ok then" in text


def test_compile_file_passes_grammar_flag_to_parse(tmp_path, monkeypatch):
    parse_calls = []
    original_parse = compile_module.parse

    def _recording_parse(text, stem, **kwargs):
        parse_calls.append(kwargs.get("grammar", False))
        return original_parse(text, stem, **kwargs)

    monkeypatch.setattr(compile_module, "parse", _recording_parse)
    monkeypatch.setattr(
        compile_module.subprocess, "run", lambda args, **kwargs: None
    )

    source_file = tmp_path / "G.md"
    source_file.write_text("# G\n\n## Cat\n\n### Sub\n\n你好\tni3hao3\thello\n", encoding="utf-8")
    notebook_file = tmp_path / "G.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC, grammar=True)
    assert parse_calls == [True]


def test_compile_all_parses_grammar_folder_with_flag_and_vocabulary_without(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    (tree_root / "Grammar").mkdir(parents=True)
    (tree_root / "Vocabulary").mkdir(parents=True)
    grammar_source = tree_root / "Grammar" / "G.md"
    grammar_source.write_text(
        "# G\n\n## Cat\n\n### Sub\n\n你好\tni3hao3\thello\n", encoding="utf-8"
    )
    vocab_source = tree_root / "Vocabulary" / "V.md"
    vocab_source.write_text("# V\n\n再见\tzai4jian4\tbye\n", encoding="utf-8")

    grammar_flags = {}

    def _fake_compile(src, dst, *, grammar=False, **kwargs):
        grammar_flags[src] = grammar
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile.compile_file", _fake_compile)

    compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert grammar_flags[grammar_source] is True
    assert grammar_flags[vocab_source] is False


@pytest.mark.integration
def test_compile_all_grammar_subtitle_produces_pdf(tmp_path):
    tree_root = tmp_path / "tree-Chinese"
    (tree_root / "Grammar").mkdir(parents=True)
    grammar_source = tree_root / "Grammar" / "G.md"
    grammar_source.write_text(
        "# G\n\n## Conjunctions\n\n### copulative conjunction\n\n和\the2\tand\n",
        encoding="utf-8",
    )

    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled

    notebook_file = tree_root / "Grammar" / "G.pdf"
    assert compiled == [notebook_file]
    assert notebook_file.exists()
    assert notebook_file.stat().st_size > 0


def test_notebook_path_for_maps_nested_md_to_pdf(tmp_path):
    source_path = tmp_path / "tree-Chinese" / "Vocabulary" / "Food.md"

    assert notebook_path_for(source_path) == (
        tmp_path / "tree-Chinese" / "Vocabulary" / "Food.pdf"
    )


def _make_source(tree_root, text="# Food\n\n牛肉\tniu2rou4\tbeef\n"):
    (tree_root / "Vocabulary").mkdir(parents=True, exist_ok=True)
    source_file = tree_root / "Vocabulary" / "Food.md"
    source_file.write_text(text, encoding="utf-8")
    notebook_file = tree_root / "Vocabulary" / "Food.pdf"
    return source_file, notebook_file


def test_compile_all_compiles_on_first_run_even_if_pdf_already_exists(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)
    notebook_file.write_bytes(b"%PDF fake")

    calls = []
    monkeypatch.setattr(
        "vimdiomas.compile.compile_file", lambda src, dst, **kwargs: calls.append((src, dst))
    )

    # No cache entry yet -> stale by construction, even though the PDF exists.
    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled
    assert compiled == [notebook_file]
    assert calls == [(source_file, notebook_file)]


def test_compile_all_skips_second_run_with_nothing_changed(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)

    calls = []

    def _fake_pandoc(markdown, dst, kind):
        calls.append(dst)
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake_pandoc)

    first = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled
    assert first == [notebook_file]
    assert len(calls) == 1

    second = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled
    assert second == []
    assert len(calls) == 1  # compile_file not called again


def test_compile_all_recompiles_when_renderer_output_changes(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)

    calls = []

    def _fake_pandoc(markdown, dst, kind):
        calls.append(dst)
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake_pandoc)

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert len(calls) == 1

    # Simulate a renderer change (e.g. _render_table) with the source untouched.
    monkeypatch.setattr(
        "vimdiomas.compile.render_markdown", lambda deck, **kwargs: "different output"
    )

    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled
    assert compiled == [notebook_file]
    assert len(calls) == 2


def test_compile_all_recompiles_when_template_changes(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)

    calls = []

    def _fake_pandoc(markdown, dst, kind):
        calls.append(dst)
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake_pandoc)
    monkeypatch.setattr("vimdiomas.compile._template_bytes", lambda: b"template v1")

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert len(calls) == 1

    # Simulate a templates/xecjk.tex edit with source and renderer untouched.
    monkeypatch.setattr("vimdiomas.compile._template_bytes", lambda: b"template v2")

    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled
    assert compiled == [notebook_file]
    assert len(calls) == 2


def test_compile_all_force_recompiles_even_when_nothing_changed(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)

    calls = []

    def _fake_pandoc(markdown, dst, kind):
        calls.append(dst)
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake_pandoc)

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert len(calls) == 1

    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC, force=True).compiled
    assert compiled == [notebook_file]
    assert len(calls) == 2


def test_compile_all_missing_cache_file_is_treated_as_empty(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    _make_source(tree_root)
    monkeypatch.setattr("vimdiomas.compile.compile_file", lambda src, dst, **kwargs: dst.write_bytes(b"x"))

    assert not compile_module.CACHE_PATH.exists()
    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled  # no exception
    assert len(compiled) == 1


def test_compile_all_corrupt_cache_file_is_treated_as_empty(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    _make_source(tree_root)
    compile_module.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    compile_module.CACHE_PATH.write_text("not json{{{", encoding="utf-8")

    monkeypatch.setattr("vimdiomas.compile.compile_file", lambda src, dst, **kwargs: dst.write_bytes(b"x"))

    compiled = compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled  # no exception
    assert len(compiled) == 1


@pytest.mark.integration
def test_compile_file_produces_real_pdf_with_hanzi_and_tone_marks(tmp_path):
    pypdf = pytest.importorskip("pypdf")

    source_file = tmp_path / "Food.md"
    source_file.write_text(
        "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n", encoding="utf-8"
    )
    notebook_file = tmp_path / "Food.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)

    assert notebook_file.exists()
    assert notebook_file.stat().st_size > 0

    reader = pypdf.PdfReader(str(notebook_file))
    text = reader.pages[0].extract_text()
    assert "牛肉" in text
    assert "niúròu" in text


def test_compile_file_passes_cjk_font_to_pandoc(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        compile_module.subprocess,
        "run",
        lambda args, **kwargs: calls.append(args),
    )

    source_file = tmp_path / "Food.md"
    source_file.write_text("# Food\n\n牛肉\tniu2rou4\tbeef\n", encoding="utf-8")
    notebook_file = tmp_path / "Food.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)

    assert len(calls) == 1
    args = calls[0]
    assert "-V" in args
    assert f"cjkfont={CHARACTER_PHONETIC.cjk_font}" in args


# -- Sprint 6 M2 · #12: a compile failure is per file ----------------------


def _good_and_bad(tree_root):
    """A good file and one xelatex rejects: a NUL byte in a hand-edited row,
    which the form cannot produce (M1, #15) and xelatex refuses outright.
    (M2 used #13's `C:\\new` heading here, until M3 fixed it.)"""
    vocab = tree_root / "Vocabulary"
    vocab.mkdir(parents=True, exist_ok=True)
    good = vocab / "A-good.md"
    good.write_text("# A-good\n\n牛肉\tniu2rou4\tbeef\n", encoding="utf-8")
    bad = vocab / "B-bad.md"
    bad.write_text("# B-bad\n\n字\tzi4\tch\x00ar\n", encoding="utf-8")
    return good, bad


def _fake_compile_failing_on(bad_source):
    import subprocess

    calls = []

    bad_pdf = notebook_path_for(bad_source)

    def _fake(markdown, dst, kind):
        calls.append(dst)
        if dst == bad_pdf:
            raise subprocess.CalledProcessError(
                43, ["pandoc"], stderr=b"noise\n\n! Undefined control sequence.\nl.12 C:\\new\n"
            )
        dst.write_bytes(b"%PDF fake")

    return _fake, calls


def test_compile_all_keeps_going_past_a_failure(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    good, bad = _good_and_bad(tree_root)
    # The bad file sorts first, so a raise would stop the good one compiling.
    bad = bad.rename(bad.with_name("0-bad.md"))
    fake, _ = _fake_compile_failing_on(bad)
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", fake)

    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert report.compiled == [notebook_path_for(good)]
    assert [f.source for f in report.failed] == [bad]
    assert notebook_path_for(good).exists()


def test_failure_message_is_the_tail_of_stderr(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    _, bad = _good_and_bad(tree_root)
    fake, _ = _fake_compile_failing_on(bad)
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", fake)

    [failure] = compile_all(tree_root, kind=CHARACTER_PHONETIC).failed

    assert failure.message == "noise\n! Undefined control sequence.\nl.12 C:\\new"


def test_failure_message_keeps_only_the_last_lines(tmp_path, monkeypatch):
    import subprocess

    exc = subprocess.CalledProcessError(
        1, ["pandoc"], stderr="\n".join(f"line {i}" for i in range(50)).encode()
    )
    message = compile_module.failure_message(exc)
    lines = message.splitlines()
    assert len(lines) == compile_module.STDERR_TAIL_LINES
    assert lines[-1] == "line 49"


def test_failure_message_without_stderr_falls_back_to_the_exception():
    assert compile_module.failure_message(FileNotFoundError("pandoc")) == "pandoc"


def test_the_good_stamp_is_saved_and_only_the_failure_retried(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    good, bad = _good_and_bad(tree_root)
    fake, calls = _fake_compile_failing_on(bad)
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", fake)

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert compile_module.CACHE_PATH.exists()
    calls.clear()

    second = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert calls == [notebook_path_for(bad)]
    assert second.compiled == []
    assert [f.source for f in second.failed] == [bad]


def test_a_run_where_everything_fails_records_no_stamps(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    _, bad = _good_and_bad(tree_root)
    (tree_root / "Vocabulary" / "A-good.md").unlink()
    fake, _ = _fake_compile_failing_on(bad)
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", fake)

    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert report.compiled == []
    assert compile_module._load_cache() == {}


def test_the_cache_is_saved_even_when_an_unexpected_error_escapes(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    good, bad = _good_and_bad(tree_root)

    def _fake(markdown, dst, kind):
        if dst == notebook_path_for(bad):
            raise RuntimeError("not anticipated")
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake)

    with pytest.raises(RuntimeError):
        compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert str(good) in compile_module._load_cache()


@pytest.mark.integration
def test_real_xelatex_failure_is_reported_next_to_a_real_success(tmp_path):
    tree_root = tmp_path / "tree-Chinese"
    good, bad = _good_and_bad(tree_root)

    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert report.compiled == [notebook_path_for(good)]
    assert notebook_path_for(good).stat().st_size > 0
    [failure] = report.failed
    assert failure.source == bad
    assert "invalid character" in failure.message


# -- Sprint 6 M3 · #10: single-pass LaTeX escaping -------------------------


def test_escape_a_backslash_once():
    assert compile_module._escape("a\\b") == r"a\textbackslash{}b"


def test_escape_a_backslash_next_to_braces_the_user_typed():
    assert compile_module._escape("a\\{b}") == r"a\textbackslash{}\{b\}"


def test_escape_every_special_character_at_once():
    assert compile_module._escape("\\&%$#_{}~^") == (
        r"\textbackslash{}\&\%\$\#\_\{\}\textasciitilde{}\textasciicircum{}"
    )


# -- Sprint 6 M3 · #13 and #5: headings and the title ----------------------

_PUNCTUATED_NAMES = ["Food {#drinks}", "Level 2 #", "*Very* common", "C:\\new words", "a_b_c", "100$"]


@pytest.mark.parametrize(
    "name, escaped",
    [
        ("Food {#drinks}", r"Food \{\#drinks\}"),
        ("Level 2 #", r"Level 2 \#"),
        ("*Very* common", r"\*Very\* common"),
        ("C:\\new words", r"C\:\\new words"),
        ("a_b_c", r"a\_b\_c"),
        ("100$", r"100\$"),
        ("[x](y)", r"\[x\]\(y\)"),
    ],
)
def test_escape_markdown(name, escaped):
    assert compile_module._escape_markdown(name) == escaped


def test_escape_markdown_leaves_smart_typography_alone():
    """`'`, `"`, `-` and `.` are never markup in a heading, and escaping
    them would stop pandoc printing ’ “” – …"""
    assert compile_module._escape_markdown('Don\'t -- stop... "now"') == 'Don\'t -- stop... "now"'


def test_headings_are_markdown_escaped():
    deck = Deck(
        title="Food",
        categories=[Category(name="*Very* common", subtitles=[Subtitle(name="Level 2 #")])],
    )
    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC, grammar=True)
    assert "## \\*Very\\* common\n" in markdown
    assert "### Level 2 \\#\n" in markdown


@pytest.mark.parametrize(
    "title, rendered",
    [
        ("Food", "Food"),
        ("Frutas y verduras", "Frutas y verduras"),
        ("Food: fruit", '"Food\\\\: fruit"'),
        ("Food # drink", '"Food \\\\# drink"'),
        ('say "hi" \\', '"say \\"hi\\" \\\\\\\\"'),
        ("HSK 1", '"HSK 1"'),
        ("True", '"True"'),
    ],
)
def test_yaml_title(title, rendered):
    assert compile_module._yaml_title(title) == rendered


def test_ordinary_output_is_unchanged():
    """No punctuation in the title or headings: the intermediate markdown is
    exactly what it was before M3, so ordinary files keep their stamps."""
    deck = Deck(
        title="Food",
        categories=[Category(name="Meat", entries=[Entry("牛肉", "niu2rou4", "beef")])],
    )
    assert render_markdown(deck, kind=CHARACTER_PHONETIC) == (
        "---\ntitle: Food\n---\n\n## Meat\n\n```{=latex}\n"
        "\\begin{longtable}{l@{\\hspace{2em}}l@{\\hspace{2em}}l}\n"
        "{\\Large 牛肉} & niúròu & beef \\\\\n\\end{longtable}\n```\n"
    )


def _pdf_text(pdf_path):
    pypdf = pytest.importorskip("pypdf")
    return "\n".join(page.extract_text() for page in pypdf.PdfReader(str(pdf_path)).pages)


@pytest.mark.integration
def test_punctuated_category_names_print_verbatim(tmp_path):
    body = "".join(f"## {name}\n\n字\tzi4\tchar\n\n" for name in _PUNCTUATED_NAMES)
    source_file = tmp_path / "Food.md"
    source_file.write_text(f"# Food\n\n{body}", encoding="utf-8")
    notebook_file = tmp_path / "Food.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)

    text = _pdf_text(notebook_file)
    for name in _PUNCTUATED_NAMES:
        assert name in text


@pytest.mark.integration
def test_punctuated_subtitle_names_print_verbatim(tmp_path):
    body = "".join(f"### {name}\n\n字\tzi4\tchar\n\n" for name in _PUNCTUATED_NAMES)
    source_file = tmp_path / "G.md"
    source_file.write_text(f"# G\n\n## Cat\n\n{body}", encoding="utf-8")
    notebook_file = tmp_path / "G.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC, grammar=True)

    text = _pdf_text(notebook_file)
    for name in _PUNCTUATED_NAMES:
        assert name in text


@pytest.mark.integration
@pytest.mark.parametrize(
    "title, printed",
    [
        ("Food: fruit", "Food: fruit"),
        ("Food # drink", "Food # drink"),
        # Straight quotes print curled, as they do in every other title.
        ('a "b", c\\d [e] *f*: g', "a “b”, c\\d [e] *f*: g"),
    ],
)
def test_punctuated_titles_print_verbatim(tmp_path, title, printed):
    source_file = tmp_path / "Food.md"
    source_file.write_text(f"# {title}\n\n字\tzi4\tchar\n", encoding="utf-8")
    notebook_file = tmp_path / "Food.pdf"

    # The deck's title is the file's stem, not its header.
    source_file = source_file.rename(tmp_path / f"{title.replace('/', '')}.md")
    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)

    assert printed in _pdf_text(notebook_file)


@pytest.mark.integration
def test_a_literal_backslash_prints_as_a_backslash(tmp_path):
    source_file = tmp_path / "Food.md"
    source_file.write_text("# Food\n\n字\tzi4\ta\\b\n", encoding="utf-8")
    notebook_file = tmp_path / "Food.pdf"

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)

    text = _pdf_text(notebook_file)
    assert "a\\b" in text
    assert "{}" not in text


# -- Sprint 6 M3 · #4 and #19 through the renderer -------------------------


def test_pair_hanzi_pinyin_leaves_latin_unpaired():
    from vimdiomas.pinyin import guess

    assert _pair_hanzi_pinyin("T恤", guess("T恤")) == [("T", ""), ("恤", "xù")]
    assert _pair_hanzi_pinyin("T恤", "Txu4") == [("T", ""), ("恤", "xù")]
    assert _pair_hanzi_pinyin("3D打印", guess("3D打印")) == [
        ("3", ""),
        ("D", ""),
        ("打", "dǎ"),
        ("印", "yìn"),
    ]


def test_render_collects_unsupported_syllables_in_both_layouts():
    deck = Deck(title="Food", uncategorized=[Entry("字", "x4", "char")])
    for grammar in (False, True):
        unsupported = []
        render_markdown(deck, kind=CHARACTER_PHONETIC, grammar=grammar, unsupported=unsupported)
        assert unsupported == ["x4"]


def test_compile_all_reports_an_unsupported_syllable_as_a_warning(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root, "# Food\n\n字\tx4\tchar\n")
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", lambda md, dst, kind: dst.write_bytes(b"x"))

    first = compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert first.compiled == [notebook_file]
    [warning] = first.warnings
    assert warning.source == source_file
    assert "x4" in warning.message

    # Up to date, and still warned about: the warning is the source's.
    second = compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert second.compiled == []
    assert [w.source for w in second.warnings] == [source_file]


@pytest.mark.integration
@pytest.mark.parametrize("folder, grammar", [("Vocabulary", False), ("Grammar", True)])
def test_syllabic_consonants_and_mixed_words_compile(tmp_path, folder, grammar):
    from vimdiomas.pinyin import guess

    tree_root = tmp_path / "tree-Chinese"
    (tree_root / folder).mkdir(parents=True)
    source_file = tree_root / folder / "Words.md"
    rows = "".join(f"{h}\t{guess(h)}\t{g}\n" for h, g in [("嗯", "uh-huh"), ("T恤", "t-shirt")])
    source_file.write_text(f"# Words\n\n{rows}", encoding="utf-8")

    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert report.failed == [] and report.warnings == []
    text = _pdf_text(notebook_path_for(source_file))
    assert "ń" in text
    assert "xù" in text
    assert "Txù" not in text


# -- Sprint 6 M3 · #11: every compile path records its stamp ---------------


def test_compile_file_alone_records_its_stamp(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)
    calls = []

    def _fake_pandoc(markdown, dst, kind):
        calls.append(dst)
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake_pandoc)

    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)
    assert str(source_file) in compile_module._load_cache()

    assert compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled == []
    assert calls == [notebook_file]


def test_compile_file_that_fails_records_nothing(tmp_path, monkeypatch):
    import subprocess

    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root)

    def _failing(markdown, dst, kind):
        raise subprocess.CalledProcessError(43, ["pandoc"])

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _failing)

    with pytest.raises(subprocess.CalledProcessError):
        compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)
    assert compile_module._load_cache() == {}


def test_compile_autocompile_revert_compile_rebuilds(tmp_path, monkeypatch):
    """The report's reproduction: compile_all, then a changed source rebuilt
    on its own (the autocompile path), then the source reverted — the last
    compile_all used to find the old stamp and skip a stale PDF."""
    tree_root = tmp_path / "tree-Chinese"
    original = "# Food\n\n牛肉\tniu2rou4\tbeef\n"
    source_file, notebook_file = _make_source(tree_root, original)
    rendered = []

    def _fake_pandoc(markdown, dst, kind):
        rendered.append(markdown)
        dst.write_text(markdown, encoding="utf-8")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _fake_pandoc)

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    source_file.write_text(original + "猪肉\tzhu1rou4\tpork\n", encoding="utf-8")
    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)
    source_file.write_text(original, encoding="utf-8")

    assert compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled == [notebook_file]
    assert "pork" not in notebook_file.read_text(encoding="utf-8")


@pytest.mark.integration
def test_compile_autocompile_revert_compile_rebuilds_for_real(tmp_path):
    tree_root = tmp_path / "tree-Chinese"
    original = "# Food\n\n牛肉\tniu2rou4\tbeef\n"
    source_file, notebook_file = _make_source(tree_root, original)

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    source_file.write_text(original + "猪肉\tzhu1rou4\tpork\n", encoding="utf-8")
    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)
    assert "pork" in _pdf_text(notebook_file)
    source_file.write_text(original, encoding="utf-8")

    assert compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled == [notebook_file]
    assert "pork" not in _pdf_text(notebook_file)


# -- Sprint 6 M5: the compiler takes the language's kind ---------------------


def test_the_stamp_of_a_chinese_render_is_what_it_was_before_kinds():
    """The digest was computed on `main`, before the kind existed: no existing
    stamp may change, or every file in every tree would rebuild. A kind with
    the font spelled out stands in for Chinese, so the literal doesn't depend
    on which platform's font `CHARACTER_PHONETIC` resolves to."""
    songti = dataclasses.replace(CHARACTER_PHONETIC, cjk_font="Songti SC")
    assert compile_module._stamp_for("md", b"tmpl", songti) == (
        "a62c1578874de66bf195064f6686b7d44b3192ec08c600ee2cbba581a59fe992"
    )


def test_the_stamp_changes_with_the_kinds_font():
    other = dataclasses.replace(CHARACTER_PHONETIC, cjk_font="Another Font")
    assert compile_module._stamp_for("md", b"t", other) != compile_module._stamp_for(
        "md", b"t", dataclasses.replace(CHARACTER_PHONETIC, cjk_font="Songti SC")
    )


# -- Sprint 6 M6: the alphabetical renderer ---------------------------------


def _german_deck():
    return Deck(
        title="Essen",
        uncategorized=[Entry(word="Haus", reading="", translation="house")],
        categories=[
            Category(
                name="Obst",
                entries=[
                    Entry(word="der Apfel", reading="", translation="the apple", note="masculine"),
                ],
            )
        ],
    )


def test_alphabetical_vocabulary_is_a_two_column_table_with_no_reading():
    markdown = render_markdown(_german_deck(), kind=ALPHABETICAL)

    assert r"\begin{longtable}{l@{\hspace{2em}}l}" in markdown
    assert r"{\Large Haus} & house \\" in markdown
    assert r"{\Large der Apfel} & the apple \textit{(masculine)} \\" in markdown
    assert "HanziPinyin" not in markdown
    assert "& &" not in markdown


def test_chinese_vocabulary_keeps_its_three_column_table():
    deck = Deck(title="Food", uncategorized=[Entry("牛肉", "niu2rou4", "beef")])
    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC)
    assert r"\begin{longtable}{l@{\hspace{2em}}l@{\hspace{2em}}l}" in markdown
    assert r"{\Large 牛肉} & niúròu & beef \\" in markdown


def test_alphabetical_grammar_is_a_stacked_unit_with_no_pinyin_row():
    deck = Deck(
        title="Konjunktionen",
        categories=[
            Category(
                name="Nebensätze",
                entries=[
                    Entry("weil", "", "because", note="verb last"),
                    Entry("obwohl", "", "although"),
                ],
            )
        ],
    )

    markdown = render_markdown(deck, kind=ALPHABETICAL, grammar=True)

    gap, entry_gap = compile_module.GRAMMAR_PINYIN_GAP, compile_module.GRAMMAR_ENTRY_GAP
    assert (
        "\\noindent%\n"
        f"\\GrammarWord{{weil}} \\\\[{gap}]\n"
        "because \\\\\n"
        f"\\textit{{(verb last)}} \\\\[{entry_gap}]\n"
        f"\\GrammarWord{{obwohl}} \\\\[{gap}]\n"
        f"although\\par\\vspace{{{entry_gap}}}\n"
    ) in markdown
    assert "HanziPinyin" not in markdown


def test_alphabetical_word_is_latex_escaped_like_hanzi():
    deck = Deck(
        title="X",
        uncategorized=[Entry("R&D_50%", "", "a & b")],
        categories=[Category(name="C", entries=[Entry("R&D_50%", "", "x")])],
    )
    table = render_markdown(deck, kind=ALPHABETICAL)
    assert r"{\Large R\&D\_50\%} & a \& b \\" in table
    grammar = render_markdown(deck, kind=ALPHABETICAL, grammar=True)
    assert r"\GrammarWord{R\&D\_50\%}" in grammar


def test_alphabetical_render_carries_no_unsupported_pinyin():
    unsupported = []
    render_markdown(_german_deck(), kind=ALPHABETICAL, unsupported=unsupported)
    assert unsupported == []


def _argv_of_a_compile(tmp_path, monkeypatch, kind):
    calls = []
    monkeypatch.setattr(
        compile_module.subprocess, "run", lambda args, **kwargs: calls.append(args)
    )
    source_file = tmp_path / "Essen.md"
    source_file.write_text("# Essen\n\nHaus\thouse\n", encoding="utf-8")
    compile_file(source_file, tmp_path / "Essen.pdf", kind=kind)
    assert len(calls) == 1
    return calls[0]


def test_pandoc_gets_no_cjk_font_for_an_alphabetical_kind(tmp_path, monkeypatch):
    argv = _argv_of_a_compile(tmp_path, monkeypatch, ALPHABETICAL)
    assert "-V" not in argv
    assert not any("cjkfont" in arg for arg in argv)


def test_pandoc_still_gets_the_cjk_font_for_a_character_kind(tmp_path, monkeypatch):
    songti = dataclasses.replace(CHARACTER_PHONETIC, cjk_font="Songti SC")
    argv = _argv_of_a_compile(tmp_path, monkeypatch, songti)
    assert argv[argv.index("-V") + 1] == "cjkfont=Songti SC"


def test_the_stamp_of_an_alphabetical_render_does_not_raise_and_differs_from_chinese():
    german = compile_module._stamp_for("md", b"t", ALPHABETICAL)
    chinese = compile_module._stamp_for("md", b"t", CHARACTER_PHONETIC)
    assert german != chinese


def test_the_template_loads_xecjk_only_when_a_cjk_font_is_given():
    template = compile_module._template_bytes().decode("utf-8")
    start, end = template.index("$if(cjkfont)$"), template.index("$endif$")
    guarded = template[start:end]
    assert r"\usepackage{xeCJK}" in guarded
    assert r"\setCJKmainfont{$cjkfont$}" in guarded
    assert template.count("xeCJK}") == 1  # nowhere outside the conditional
    assert r"\newcommand{\GrammarWord}" in template


@pytest.mark.integration
def test_german_vocabulary_compiles_for_real_in_latin_modern(tmp_path):
    german = Path(__file__).parent / "fixtures" / "german" / "Essen.md"
    notebook_file = tmp_path / "Essen.pdf"

    compile_file(german, notebook_file, kind=ALPHABETICAL)

    text = _pdf_text(notebook_file)
    assert "Haus" in text and "house" in text
    assert "der Apfel" in text and "masculine, nominative" in text
    assert "Getränke" in text


@pytest.mark.integration
def test_german_grammar_compiles_for_real_and_a_long_phrase_wraps(tmp_path):
    german = Path(__file__).parent / "fixtures" / "german" / "Grammar" / "Konjunktionen.md"
    notebook_file = tmp_path / "Konjunktionen.pdf"

    compile_file(german, notebook_file, kind=ALPHABETICAL, grammar=True)

    text = _pdf_text(notebook_file)
    assert "Kausal" in text and "Konzessiv" in text
    assert "weil" in text and "because" in text
    # The long phrase is on the page, wrapped over more than one line.
    assert "Ich bleibe zu Hause" in text
    assert "aufstehen muss" in text


@pytest.mark.integration
def test_a_german_file_with_umlauts_and_sharp_s_prints_them(tmp_path):
    source_file = tmp_path / "Wörter.md"
    source_file.write_text("# Wörter\n\nStraße\tstreet\nÜbung\texercise\n", encoding="utf-8")
    notebook_file = tmp_path / "Wörter.pdf"

    compile_file(source_file, notebook_file, kind=ALPHABETICAL)

    text = _pdf_text(notebook_file)
    assert "Straße" in text and "Übung" in text


# -- Sprint 6 M6: a row too long for the columns is an exception, for every kind


_LONG_WORD = "Donaudampfschifffahrtsgesellschaftskapitänsmütze"
_SPAN_2 = r"\multicolumn{2}{p{\dimexpr\linewidth-2\tabcolsep\relax}}"
_SPAN_3 = r"\multicolumn{3}{p{\dimexpr\linewidth-2\tabcolsep\relax}}"


def _table(kind, *entries):
    return render_markdown(Deck(title="X", uncategorized=list(entries)), kind=kind)


def _german_table(*entries):
    return _table(ALPHABETICAL, *entries)


def test_exception_rows_of_a_table_that_fits_is_empty():
    assert compile_module._exception_rows([[3.0, 5.0], [10.0, 20.0]]) == set()
    assert compile_module._exception_rows([]) == set()


def test_exception_rows_takes_a_word_wider_than_the_cap_even_if_the_table_fits():
    widths = [[2.0, 5.0], [compile_module.WORD_CAP_EM + 0.1, 3.0], [4.0, 6.0]]
    assert compile_module._exception_rows(widths) == {1}


def test_exception_rows_takes_the_row_that_makes_the_table_too_wide_and_only_it():
    # Available: 39 - 1 - 2 = 36em for two columns.
    widths = [[3.0, 10.0], [4.0, 34.0], [5.0, 12.0]]  # 5 + 34 > 36
    assert compile_module._exception_rows(widths) == {1}


def test_exception_rows_takes_as_few_rows_as_make_the_table_fit():
    widths = [[10.0, 5.0], [3.0, 30.0], [11.0, 6.0]]  # 11 + 30 = 41 > 36
    assert compile_module._exception_rows(widths) == {1}
    widths = [[10.0, 25.0], [3.0, 30.0], [11.0, 20.0]]  # still 11 + 30 > 36
    assert compile_module._exception_rows(widths) == {1}


def test_exception_rows_uses_the_three_column_budget_for_a_reading():
    # 39 - 1 - 4 = 34em: 9 + 10 + 15 fits, 9 + 10 + 15.1 does not.
    assert compile_module._exception_rows([[9.0, 10.0, 15.0]]) == set()
    assert compile_module._exception_rows([[9.0, 10.0, 15.1]]) == {0}


def test_width_counts_wide_characters_as_a_full_em():
    assert compile_module._width_em("ab") == 1.0
    assert compile_module._width_em("你好") == 2.0
    assert compile_module._width_em("你a") == 1.5


def test_a_short_alphabetical_row_is_an_ordinary_row():
    markdown = _german_table(Entry("Haus", "", "house"))
    assert "multicolumn" not in markdown
    assert r"{\Large Haus} & house \\" in markdown


def test_a_long_word_is_an_exception_row_across_both_columns():
    markdown = _german_table(Entry(_LONG_WORD, "", "captain's cap"))
    assert _SPAN_2 in markdown
    assert rf"{{\Large {_LONG_WORD}}}\hspace{{2em}}captain's cap}} \\" in markdown
    assert r"\hangindent=1.5em\hangafter=1" in markdown
    assert r"\raggedright" in markdown
    exception_line = next(line for line in markdown.splitlines() if "multicolumn" in line)
    assert "&" not in exception_line  # one cell


def test_a_long_translation_is_an_exception_row_even_with_a_short_word():
    markdown = _german_table(Entry("Haus", "", "a" * 80), Entry("Tisch", "", "table"))
    assert markdown.count("multicolumn") == 1
    assert r"{\Large Tisch} & table \\" in markdown


def test_the_note_counts_towards_a_rows_length():
    translation = "a" * 60
    assert "multicolumn" not in _german_table(Entry("Haus", "", translation))
    assert "multicolumn" in _german_table(Entry("Haus", "", translation, note="a" * 20))


def test_the_exception_row_keeps_its_note_and_escapes_its_text():
    markdown = _german_table(Entry(_LONG_WORD + "&", "", "x", note="n_1"))
    assert r"{\Large " + _LONG_WORD + r"\&}\hspace{2em}x \textit{(n\_1)}}" in markdown


def test_exception_rows_sit_among_ordinary_ones_in_order():
    markdown = _german_table(
        Entry("Haus", "", "house"), Entry(_LONG_WORD, "", "cap"), Entry("Tisch", "", "table")
    )
    assert markdown.index("Haus") < markdown.index(_LONG_WORD) < markdown.index("Tisch")
    assert markdown.count("multicolumn") == 1


def test_a_long_chinese_row_is_an_exception_spanning_three_columns():
    long_gloss = "a very long gloss " * 6
    markdown = _table(
        CHARACTER_PHONETIC,
        Entry("你好", "ni3hao3", "hello"),
        Entry("天气", "tian1qi4", long_gloss.strip()),
    )
    assert markdown.count("multicolumn") == 1
    assert _SPAN_3 in markdown
    assert r"{\Large 天气}\hspace{2em}tiānqì\hspace{2em}" + long_gloss.strip() in markdown
    assert r"{\Large 你好} & nǐhǎo & hello \\" in markdown


def test_a_chinese_exception_row_with_no_reading_adds_no_empty_gap():
    markdown = _table(CHARACTER_PHONETIC, Entry("字" * 11, "", "gloss"))
    assert r"\hspace{2em}gloss}" in markdown
    assert r"\hspace{2em}\hspace{2em}" not in markdown


def test_chinese_rows_that_fit_are_never_exceptions():
    entries = [
        Entry("你好", "ni3hao3", "hello"),
        Entry("再见", "zai4jian4", "goodbye, see you later"),
        Entry("...", "", "ellipsis"),
    ]
    assert "multicolumn" not in _table(CHARACTER_PHONETIC, *entries)


def _compile_real(tmp_path, kind, text, grammar=False):
    source_file = tmp_path / "Lang.md"
    source_file.write_text(text, encoding="utf-8")
    notebook_file = tmp_path / "Lang.pdf"
    compile_file(source_file, notebook_file, kind=kind, grammar=grammar)
    return notebook_file


def _right_edge_pt(pdf_path):
    """The rightmost extent of any word on any page, from poppler."""
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext (poppler) not installed")
    boxes = subprocess.run(
        ["pdftotext", "-bbox", str(pdf_path), "-"], check=True, capture_output=True, text=True
    ).stdout
    return max(float(m) for m in re.findall(r'xMax="([0-9.]+)"', boxes))


_INSIDE_THE_MARGIN = 540 + 1  # a 612pt page, 1in margins


@pytest.mark.integration
def test_a_long_german_word_compiles_for_real_and_wraps_inside_the_margins(tmp_path):
    notebook_file = _compile_real(
        tmp_path,
        ALPHABETICAL,
        "# Lang\n\nHaus\thouse\n"
        f"{_LONG_WORD}\tcaptain's cap of the Danube steamship company, "
        "a translation long enough that it has to wrap onto a second line\n"
        "Tisch\ttable\n",
    )
    assert _LONG_WORD in _pdf_text(notebook_file)
    assert "second line" in _pdf_text(notebook_file)
    # Without the exception row the translation ran to ~617pt.
    assert _right_edge_pt(notebook_file) <= _INSIDE_THE_MARGIN


@pytest.mark.integration
def test_a_long_chinese_gloss_compiles_for_real_inside_the_margins(tmp_path):
    notebook_file = _compile_real(
        tmp_path,
        CHARACTER_PHONETIC,
        "# Lang\n\n你好\tni3hao3\thello\n"
        "天气\ttian1qi4\t" + "a gloss long enough to run past the right margin, " * 3 + "end\n",
    )
    assert "tiānqì" in _pdf_text(notebook_file)
    assert _right_edge_pt(notebook_file) <= _INSIDE_THE_MARGIN


@pytest.mark.integration
def test_a_long_chinese_grammar_phrase_wraps_inside_the_margins(tmp_path):
    phrase = "我今天早上八点钟起床然后去学校上课下午回家做作业晚上和朋友一起吃饭聊天看电视"
    pinyin = "wo3jin1tian1zao3shang4ba1dian3zhong1qi3chuang2ran2hou4qu4xue2xiao4shang4ke4"
    notebook_file = _compile_real(
        tmp_path,
        CHARACTER_PHONETIC,
        f"# Lang\n\n## Frases\n\n{phrase}\t{pinyin}\ta long sentence\n",
        grammar=True,
    )
    assert "a long sentence" in _pdf_text(notebook_file)
    assert _right_edge_pt(notebook_file) <= _INSIDE_THE_MARGIN


def test_forget_tree_drops_only_entries_under_the_root(tmp_path):
    root = tmp_path / "tree-Chinese"
    cache = {
        str(root / "Vocabulary" / "Food.md"): "a",
        str(root / "Grammar" / "Particles.md"): "b",
        str(tmp_path / "tree-Chinese2" / "Food.md"): "c",
        str(tmp_path / "tree-German" / "Essen.md"): "d",
    }
    compile_module._save_cache(cache)

    compile_module.forget_tree(root)

    assert compile_module._load_cache() == {
        str(tmp_path / "tree-Chinese2" / "Food.md"): "c",
        str(tmp_path / "tree-German" / "Essen.md"): "d",
    }


def test_forget_tree_with_no_cache_file_is_a_no_op(tmp_path):
    assert not compile_module.CACHE_PATH.exists()

    compile_module.forget_tree(tmp_path / "tree-Chinese")

    assert not compile_module.CACHE_PATH.exists()


def test_forget_tree_does_not_rewrite_an_unaffected_cache(tmp_path):
    compile_module._save_cache({str(tmp_path / "tree-German" / "Essen.md"): "d"})
    before = compile_module.CACHE_PATH.stat().st_mtime_ns

    compile_module.forget_tree(tmp_path / "tree-Chinese")

    assert compile_module.CACHE_PATH.stat().st_mtime_ns == before


# -- Sprint 6 M9: a hand-edited file compiles, and says what it holds --------


WARNED_SOURCE = (
    "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\tjunk\n\n| word | gloss |\n"
)


def test_a_file_outside_the_format_still_compiles_and_is_reported(tmp_path, monkeypatch):
    """Nothing is blocked: the PDF is written and the warnings come with it
    (requirements.md §6)."""
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root, WARNED_SOURCE)

    monkeypatch.setattr(
        "vimdiomas.compile._run_pandoc",
        lambda markdown, dst, kind: dst.write_bytes(b"%PDF fake"),
    )

    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert report.compiled == [notebook_file]
    assert report.failed == []
    assert [w.source for w in report.warnings] == [source_file, source_file]
    assert [w.message for w in report.warnings] == [
        "line 5: extra column(s) never rendered: junk\n    牛肉\tniu2rou4\tbeef\tjunk",
        "line 7: unrecognized line\n    | word | gloss |",
    ]


def test_warnings_are_reported_again_when_nothing_is_rebuilt(tmp_path, monkeypatch):
    """A warning describes the source, not the run (M3's rule): an up-to-date
    tree still reports what its files hold."""
    tree_root = tmp_path / "tree-Chinese"
    _make_source(tree_root, WARNED_SOURCE)
    monkeypatch.setattr(
        "vimdiomas.compile._run_pandoc",
        lambda markdown, dst, kind: dst.write_bytes(b"%PDF fake"),
    )

    first = compile_all(tree_root, kind=CHARACTER_PHONETIC)
    second = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert second.compiled == []
    assert [w.message for w in second.warnings] == [w.message for w in first.warnings]


def test_a_file_level_warning_has_no_line_number(tmp_path, monkeypatch):
    tree_root = tmp_path / "tree-Chinese"
    _make_source(tree_root, "## Meat\n\n牛肉\tniu2rou4\tbeef\n")
    monkeypatch.setattr(
        "vimdiomas.compile._run_pandoc",
        lambda markdown, dst, kind: dst.write_bytes(b"%PDF fake"),
    )

    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert [w.message for w in report.warnings] == ["no '# Food' header line"]


def test_a_renamed_category_rebuilds_the_file(tmp_path, monkeypatch):
    """A non-trivial hand change reaches the PDF, because every Compile
    re-renders every file and the stamp is of the markdown (M4, M9 §3)."""
    tree_root = tmp_path / "tree-Chinese"
    source_file, notebook_file = _make_source(tree_root, "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n")
    calls = []
    monkeypatch.setattr(
        "vimdiomas.compile._run_pandoc",
        lambda markdown, dst, kind: (calls.append(markdown), dst.write_bytes(b"%PDF fake")),
    )

    compile_all(tree_root, kind=CHARACTER_PHONETIC)
    assert len(calls) == 1
    assert compile_all(tree_root, kind=CHARACTER_PHONETIC).compiled == []

    source_file.write_text(
        source_file.read_text(encoding="utf-8").replace("## Meat", "## Protein"),
        encoding="utf-8",
    )
    report = compile_all(tree_root, kind=CHARACTER_PHONETIC)

    assert report.compiled == [notebook_file]
    assert "## Protein" in calls[-1] and report.warnings == []


# -- Sprint 7 M2: curly-quote spacing


@pytest.mark.parametrize(
    "field, curled",
    [
        ('a "b" c', "a “b” c"),
        ('"b" c', "“b” c"),
        ('("b")', "(“b”)"),
        ('say "hi."', "say “hi.”"),
        ('a-"b"-c', "a-“b”-c"),
        ('a "b"', "a “b”"),
        ("a “b” c", "a “b” c"),
        ("it's", "it's"),
        ('他说"你好"再见', "他说“你好”再见"),
        ('他说"你好', "他说“你好"),
        ('你好" a', "你好” a"),
        ('"', "“"),
        ("", ""),
    ],
)
def test_curl_quotes(field, curled):
    assert compile_module._curl_quotes(field) == curled


def _quoted_deck():
    return Deck(
        title="Food",
        uncategorized=[Entry(word='a "b" c', reading="", translation='a "b" c', note='"b" c')],
    )


@pytest.mark.parametrize("kind", [ALPHABETICAL, CHARACTER_PHONETIC])
@pytest.mark.parametrize("grammar", [False, True])
def test_an_entrys_straight_quotes_are_curled_in_every_field(kind, grammar):
    deck = _quoted_deck()
    if kind.has_reading:
        deck.uncategorized[0].reading = "a"
    markdown = render_markdown(deck, kind=kind, grammar=grammar)
    assert '"' not in markdown
    assert r"\textit{(“b” c)}" in markdown
    assert markdown.count("a “b” c") == (1 if grammar and kind.has_reading else 2)


def test_a_grammar_word_is_curled_whole_before_it_is_split_into_units():
    deck = Deck(
        title="G",
        uncategorized=[Entry(word='他说"你好"', reading="ta1shuo1ni3hao3", translation="x")],
    )
    markdown = render_markdown(deck, kind=CHARACTER_PHONETIC, grammar=True)
    assert r"\HanziPinyin{“}{}\HanziPinyin{你}" in markdown
    assert r"\HanziPinyin{好}{hǎo}\HanziPinyin{”}{}" in markdown
    assert r"\HanziPinyin{”}{}\HanziPinyin{“}" not in markdown


def test_an_alphabetical_grammar_word_is_curled_whole():
    deck = Deck(title="G", uncategorized=[Entry(word='a "b" c', reading="", translation="x")])
    markdown = render_markdown(deck, kind=ALPHABETICAL, grammar=True)
    assert r"\GrammarWord{a “b” c}" in markdown


def test_curling_leaves_latex_escaping_beside_it_alone():
    deck = Deck(
        title="Food",
        uncategorized=[Entry(word="x", reading="", translation='"50%" & _y_ {z}')],
    )
    markdown = render_markdown(deck, kind=ALPHABETICAL)
    assert r"“50\%” \& \_y\_ \{z\}" in markdown


def test_an_entry_with_no_double_quote_renders_as_it_did():
    deck = Deck(
        title="Food",
        categories=[Category(name="Meat", entries=[Entry("牛肉", "niu2rou4", "it's beef")])],
    )
    assert "{\\Large 牛肉} & niúròu & it's beef \\\\" in render_markdown(
        deck, kind=CHARACTER_PHONETIC
    )


def _pdf_tokens(pdf_path):
    """The words of a PDF, as poppler's `-bbox` splits them: two are separate
    when a space or a gap divides them."""
    import html

    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext (poppler) not installed")
    boxes = subprocess.run(
        ["pdftotext", "-bbox", str(pdf_path), "-"], check=True, capture_output=True, text=True
    ).stdout
    return [html.unescape(word) for word in re.findall(r">([^<>]+)</word>", boxes)]


def _compile_text(tmp_path, kind, text, *, name="Lang", grammar=False):
    source_file = tmp_path / f"{name}.md"
    source_file.write_text(text, encoding="utf-8")
    notebook_file = tmp_path / f"{name}.pdf"
    compile_file(source_file, notebook_file, kind=kind, grammar=grammar)
    return notebook_file


@pytest.mark.integration
@pytest.mark.parametrize(
    "where",
    ["title", "heading", "subtitle", "category-entry", "typed-entry", "straight-entry"],
)
def test_a_chinese_pdf_keeps_the_space_after_a_closing_quote(tmp_path, where):
    name, body, grammar = "Lang", "字\tzi4\tchar\n", False
    if where == "title":
        name = 'a "b" c'
    elif where == "heading":
        body = '## a "b" c\n\n' + body
    elif where == "subtitle":
        body, grammar = '## Cat\n\n### a "b" c\n\n' + body, True
    elif where == "category-entry":
        body = '## Cat\n\n字\tzi4\ta “b” c\n'
    elif where == "typed-entry":
        body = "字\tzi4\ta “b” c\n"
    else:
        body = '字\tzi4\ta "b" c\n'
    pdf = _compile_text(
        tmp_path, CHARACTER_PHONETIC, f"# {name}\n\n{body}", name=name, grammar=grammar
    )
    tokens = _pdf_tokens(pdf)
    assert "“b”" in tokens
    assert not any(token.startswith("“b”") and token != "“b”" for token in tokens)
    assert tokens[tokens.index("“b”") + 1] == "c"


@pytest.mark.integration
@pytest.mark.parametrize("dash", ["--", "---"])
def test_a_chinese_heading_keeps_the_space_after_a_dash(tmp_path, dash):
    pdf = _compile_text(
        tmp_path, CHARACTER_PHONETIC, f"# Lang\n\n## a {dash} b\n\n字\tzi4\tchar\n"
    )
    tokens = _pdf_tokens(pdf)
    assert tokens[tokens.index("a") + 1] in {"–", "—"}
    assert tokens[tokens.index("a") + 2] == "b"


@pytest.mark.integration
def test_a_chinese_heading_ellipsis_is_the_latin_one(tmp_path):
    # Poppler runs the Latin ellipsis into its neighbours (`a…b`, as it does
    # in a plain LaTeX document), so the glyph is what is checked: xeCJK set
    # it as the CJK font's mid-height `⋯` and, before it, swallowed the space.
    pdf = _compile_text(tmp_path, CHARACTER_PHONETIC, "# Lang\n\n## a ... b\n\n字\tzi4\tchar\n")
    text = " ".join(_pdf_tokens(pdf))
    assert "…" in text and "⋯" not in text


@pytest.mark.integration
def test_a_chinese_entry_keeps_a_typed_space_after_full_width_punctuation(tmp_path):
    pdf = _compile_text(tmp_path, CHARACTER_PHONETIC, "# Lang\n\n字\tzi4\t一，二。 b\n")
    tokens = _pdf_tokens(pdf)
    assert tokens[tokens.index("b") - 1].endswith("。")


@pytest.mark.integration
@pytest.mark.parametrize("where", ["heading", "translation"])
def test_genuine_chinese_quotes_get_no_gap_added(tmp_path, where):
    if where == "heading":
        body = "## 他说“你好”再见\n\n字\tzi4\tchar\n"
    else:
        body = "字\tzi4\t他说“你好”再见\n"
    tokens = _pdf_tokens(_compile_text(tmp_path, CHARACTER_PHONETIC, f"# Lang\n\n{body}"))
    assert "他说“你好”再见" in tokens


@pytest.mark.integration
def test_a_german_entry_curls_its_quotes_and_keeps_the_space(tmp_path):
    pdf = _compile_text(tmp_path, ALPHABETICAL, '# Lang\n\nHaus\ta "b" c\n')
    tokens = _pdf_tokens(pdf)
    assert tokens[tokens.index("“b”") + 1] == "c"
    assert "”b”" not in tokens


@pytest.mark.integration
def test_a_german_heading_with_quotes_prints_as_it_did(tmp_path):
    pdf = _compile_text(tmp_path, ALPHABETICAL, '# Lang\n\n## a "b" c\n\nHaus\thouse\n')
    tokens = _pdf_tokens(pdf)
    assert tokens[tokens.index("“b”") + 1] == "c"


def test_the_xecjk_patch_is_inside_the_cjk_conditional():
    template = compile_module._template_bytes().decode("utf-8")
    start, end = template.index("$if(cjkfont)$"), template.index("$endif$")
    guarded = template[start:end]
    assert "xeCJK_FullRight_and_Boundary:" in guarded
    assert "xeCJKDeclareCharClass" in guarded
    assert "xeCJK_FullRight_and_Boundary:" not in template[:start] + template[end:]
    assert "xeCJKDeclareCharClass" not in template[:start] + template[end:]
