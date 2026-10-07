import platform
import re
import subprocess
from pathlib import Path

import pytest

from vimdiomas import doctor
from vimdiomas.platform import CJK_FONT_NAME, input_switcher

on_macos = pytest.mark.skipif(platform.system() != "Darwin", reason="macOS parity")

SWITCHER_NAME = input_switcher()[0]

LATEX_NAMES = [name for name, _ in doctor.LATEX_PACKAGES]


def _by_name(checks, name):
    return next(check for check in checks if check.name == name)


def _all_missing(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    monkeypatch.setattr(doctor, "_missing_latex_packages", lambda: list(LATEX_NAMES))
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: False)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: False)
    monkeypatch.setattr(doctor, "pdftoppm_available", lambda: False)


def _latex(monkeypatch, missing):
    monkeypatch.setattr(doctor, "_missing_latex_packages", lambda: missing)


def test_run_reports_all_required_ok_on_this_machine():
    # The dev's Mac and the Linux verification image both carry every
    # required dependency (Sprint 4 M4; Sprint 5 M7's docker/Dockerfile).
    checks = doctor.run()
    assert all(check.ok for check in checks if check.required)


@on_macos
def test_run_reports_all_ok_on_this_mac():
    # This machine has pandoc, xelatex, xeCJK, the CJK font, macism and nvim
    # installed and verified (see specs/Sprint-4/features/
    # M4-2026-09-13-install-groundwork/requirements.md).
    checks = doctor.run()
    assert all(check.ok for check in checks)


def test_required_checks_are_pandoc_xelatex_and_the_latex_packages():
    checks = doctor.run()
    required_names = {check.name for check in checks if check.required}
    assert required_names == {"pandoc", "xelatex", "LaTeX packages"}


def test_xecjk_and_the_font_are_needed_for_chinese_only():
    checks = doctor.run()
    for name in ("xeCJK", CJK_FONT_NAME):
        check = _by_name(checks, name)
        assert not check.required
        assert check.needed_for == ("Chinese",)
    assert {check.name for check in checks if check.needed_for} == {"xeCJK", CJK_FONT_NAME}


def test_optional_checks_are_the_switcher_nvim_and_pdftoppm():
    checks = doctor.run()
    optional_names = {
        check.name for check in checks if not check.required and not check.needed_for
    }
    assert optional_names == {SWITCHER_NAME, "nvim", "pdftoppm"}


def test_a_check_carries_the_platforms_install_command(monkeypatch):
    _all_missing(monkeypatch)
    _as_linux_arch(monkeypatch)

    checks = doctor.run()

    assert _by_name(checks, "xeCJK").install == "sudo pacman -S texlive-langchinese"
    assert _by_name(checks, "Noto Serif CJK SC").install == "sudo pacman -S noto-fonts-cjk"


def test_a_check_with_no_platform_command_has_an_empty_install(monkeypatch):
    _all_missing(monkeypatch)
    _as_linux_arch(monkeypatch)
    monkeypatch.setattr(doctor, "install_hint", lambda dependency: None)

    assert _by_name(doctor.run(), "xeCJK").install == ""


# --- missing_for: what blocks which install (Sprint 6 M7) ------------------


def _names(checks):
    return [check.name for check in checks]


def test_missing_for_german_ignores_a_missing_xecjk_and_font(monkeypatch):
    _all_missing(monkeypatch)
    _latex(monkeypatch, [])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")

    assert doctor.missing_for(doctor.run(), ["German"]) == []


def test_missing_for_chinese_returns_the_cjk_pair(monkeypatch):
    _all_missing(monkeypatch)
    _latex(monkeypatch, [])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")

    missing = doctor.missing_for(doctor.run(), ["German", "Chinese"])

    assert _names(missing) == ["xeCJK", CJK_FONT_NAME]


def test_missing_for_always_returns_a_missing_required_check(monkeypatch):
    _all_missing(monkeypatch)

    expected = ["pandoc", "xelatex", "LaTeX packages"]
    assert _names(doctor.missing_for(doctor.run(), ["German"])) == expected
    assert _names(doctor.missing_for(doctor.run(), [])) == expected


def test_missing_for_ignores_a_check_that_is_ok(monkeypatch):
    _latex(monkeypatch, [])
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: True)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: False)

    assert _names(doctor.missing_for(doctor.run(), ["Chinese"])) == [CJK_FONT_NAME]


# --- labels ----------------------------------------------------------------


def test_label_is_required_optional_or_the_languages():
    assert doctor.label(doctor.Check("a", required=True, ok=True)) == "required"
    assert doctor.label(doctor.Check("a", required=False, ok=True)) == "optional"
    assert (
        doctor.label(doctor.Check("a", required=False, ok=True, needed_for=("Chinese",)))
        == "Chinese"
    )
    assert (
        doctor.label(
            doctor.Check("a", required=False, ok=True, needed_for=("Chinese", "Japanese"))
        )
        == "Chinese, Japanese"
    )


def test_reports_missing_xecjk_with_actionable_message(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: False)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: True)

    check = _by_name(doctor.run(), "xeCJK")
    assert not check.ok
    assert check.message


def test_reports_missing_pandoc(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None if name == "pandoc" else "/usr/bin/x")
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: True)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: True)

    check = _by_name(doctor.run(), "pandoc")
    assert not check.ok
    assert "pandoc" in check.message


def test_reports_missing_font_by_its_name(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: True)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: False)

    check = _by_name(doctor.run(), CJK_FONT_NAME)
    assert not check.ok
    assert CJK_FONT_NAME in check.message


def test_reports_missing_switcher_as_optional(monkeypatch):
    monkeypatch.setattr(doctor, "input_switcher", lambda: (SWITCHER_NAME, False, ""))
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: True)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: True)

    check = _by_name(doctor.run(), SWITCHER_NAME)
    assert not check.required
    assert not check.ok


def test_reports_missing_nvim_as_optional(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None if name == "nvim" else "/usr/bin/x")
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: True)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: True)

    check = _by_name(doctor.run(), "nvim")
    assert not check.required
    assert not check.ok


def test_pandoc_url_points_at_its_github_repo():
    check = _by_name(doctor.run(), "pandoc")
    assert check.url == "https://github.com/jgm/pandoc"


# --- macOS parity (Sprint 5 M7) ------------------------------------------
# Moving the font, the switcher and the install commands into the platform
# layer must leave macOS's doctor output exactly as it was.


@on_macos
def test_every_check_but_the_font_carries_a_url_on_macos():
    checks = doctor.run()
    with_url = {check.name for check in checks if check.url}
    # `LaTeX packages` has none: a line that names packages has no room for one.
    assert with_url == {"pandoc", "xelatex", "xeCJK", "macism", "nvim", "pdftoppm"}
    # The CJK font ships with macOS — there's no repo to point at.
    assert _by_name(checks, CJK_FONT_NAME).url == ""


@on_macos
def test_macos_messages_are_unchanged(monkeypatch):
    _all_missing(monkeypatch)

    checks = doctor.run()

    assert [(c.name, c.required, c.message, c.url) for c in checks] == [
        (
            "pandoc",
            True,
            "pandoc not found: install it (e.g. `brew install pandoc`)",
            "https://github.com/jgm/pandoc",
        ),
        (
            "xelatex",
            True,
            "xelatex not found: install a TeX Live distribution",
            "https://github.com/TeX-Live/texlive-source",
        ),
        (
            "LaTeX packages",
            True,
            "LaTeX packages missing: fontspec, geometry, longtable, caption, array, "
            "xcolor, lmodern, lmodern fonts (e.g. `sudo tlmgr install fontspec geometry "
            "tools caption xcolor lm`)",
            "",
        ),
        (
            "xeCJK",
            False,
            "sudo tlmgr install xecjk",
            "https://github.com/texjporg/xecjk",
        ),
        (
            "Songti SC",
            False,
            "CJK font not found at /System/Library/Fonts/Supplemental/Songti.ttc (Songti SC)",
            "",
        ),
        (
            "macism",
            False,
            "macism not found: input-method switching will be a no-op "
            "(e.g. `brew install laishulu/homebrew/macism`)",
            "https://github.com/laishulu/macism",
        ),
        (
            "nvim",
            False,
            "nvim not found: Inspect Tree's MD mode won't be able to open files "
            "(e.g. `brew install neovim`)",
            "https://github.com/neovim/neovim",
        ),
        (
            "pdftoppm",
            False,
            "pdftoppm not found: Inspect Tree's PDF preview will be "
            "degraded (e.g. `brew install poppler`)",
            "https://poppler.freedesktop.org/",
        ),
    ]


# --- Linux's shape, runnable anywhere --------------------------------------


def _as_linux_arch(monkeypatch):
    from vimdiomas.platform import linux

    monkeypatch.setattr(doctor, "install_hint", linux.install_hint)
    monkeypatch.setattr(doctor, "latex_install_hint", linux.latex_install_hint)
    monkeypatch.setattr(doctor, "CJK_FONT_NAME", linux.CJK_FONT_NAME)
    monkeypatch.setattr(doctor, "CJK_FONT_PATH", linux.CJK_FONT_PATH)
    monkeypatch.setattr(doctor, "CJK_FONT_URL", linux.CJK_FONT_URL)
    monkeypatch.setattr(
        doctor, "input_switcher", lambda: ("fcitx5 or ibus", False, "https://github.com/fcitx/fcitx5")
    )


def test_linux_messages_carry_pacman_commands_and_no_brew(monkeypatch):
    _all_missing(monkeypatch)
    _as_linux_arch(monkeypatch)

    checks = doctor.run()
    messages = {c.name: c.message for c in checks}

    assert messages["pandoc"] == "pandoc not found: install it (e.g. `sudo pacman -S pandoc-cli`)"
    assert messages["xelatex"] == (
        "xelatex not found: install a TeX Live distribution (e.g. `sudo pacman -S texlive-xetex`)"
    )
    assert messages["LaTeX packages"] == (
        "LaTeX packages missing: fontspec, geometry, longtable, caption, array, xcolor, "
        "lmodern, lmodern fonts (e.g. `sudo pacman -S texlive-latexrecommended texlive-latex "
        "texlive-fontsrecommended`)"
    )
    assert messages["xeCJK"] == "sudo pacman -S texlive-langchinese"
    assert messages["Noto Serif CJK SC"] == (
        "CJK font not found (Noto Serif CJK SC) (e.g. `sudo pacman -S noto-fonts-cjk`)"
    )
    assert "fcitx5 or ibus" in messages
    assert not any("brew" in message for message in messages.values())
    assert _by_name(checks, "Noto Serif CJK SC").url == "https://github.com/notofonts/noto-cjk"


# --- LaTeX packages (Sprint 8 M2) -------------------------------------------


def test_latex_packages_complete_is_ok_with_no_detail_or_command(monkeypatch):
    _latex(monkeypatch, [])

    check = _by_name(doctor.run(), "LaTeX packages")

    assert check.ok
    assert check.required
    assert check.detail == ""
    assert check.install == ""
    assert check.needed_for == ()
    assert check.url == ""


def test_latex_packages_name_what_is_missing_on_macos_shape(monkeypatch):
    from vimdiomas.platform import macos

    monkeypatch.setattr(doctor, "latex_install_hint", macos.latex_install_hint)
    _latex(monkeypatch, ["caption", "xcolor"])

    check = _by_name(doctor.run(), "LaTeX packages")

    assert not check.ok
    assert check.detail == "caption, xcolor"
    assert check.install == "sudo tlmgr install caption xcolor"
    assert check.message == (
        "LaTeX packages missing: caption, xcolor (e.g. `sudo tlmgr install caption xcolor`)"
    )


def test_latex_packages_install_covers_only_the_missing_on_arch(monkeypatch):
    _as_linux_arch(monkeypatch)
    _latex(monkeypatch, ["lmodern", "lmodern fonts"])

    check = _by_name(doctor.run(), "LaTeX packages")

    assert check.detail == "lmodern, lmodern fonts"
    assert check.install == "sudo pacman -S texlive-fontsrecommended"


def test_latex_packages_of_a_bare_arch_texlive_ask_for_the_two_collections(monkeypatch):
    _as_linux_arch(monkeypatch)
    _latex(monkeypatch, ["fontspec", "caption", "xcolor", "lmodern", "lmodern fonts"])

    assert _by_name(doctor.run(), "LaTeX packages").install == (
        "sudo pacman -S texlive-latexrecommended texlive-fontsrecommended"
    )


def test_latex_packages_without_kpsewhich_fail_without_naming_packages(monkeypatch):
    _as_linux_arch(monkeypatch)
    _latex(monkeypatch, None)

    check = _by_name(doctor.run(), "LaTeX packages")

    assert not check.ok
    assert check.detail == "needs a TeX distribution"
    assert check.install == ""
    assert check.message == (
        "LaTeX packages can't be checked: no TeX distribution found (kpsewhich is missing)"
    )


def test_latex_packages_without_a_platform_command_have_no_example(monkeypatch):
    monkeypatch.setattr(doctor, "latex_install_hint", lambda packages: None)
    _latex(monkeypatch, ["caption"])

    check = _by_name(doctor.run(), "LaTeX packages")

    assert check.install == ""
    assert check.message == "LaTeX packages missing: caption"


@pytest.mark.parametrize("languages", [["German"], []])
def test_missing_for_includes_the_failing_latex_packages(monkeypatch, languages):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")
    _latex(monkeypatch, ["caption"])

    assert "LaTeX packages" in _names(doctor.missing_for(doctor.run(), languages))


# --- _missing_latex_packages: one kpsewhich call -----------------------------


def _kpsewhich_prints(monkeypatch, stdout):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    return calls


def test_missing_latex_packages_matches_found_files_by_basename(monkeypatch):
    found = [
        "/usr/share/texmf-dist/tex/latex/geometry/geometry.sty",
        "/usr/share/texmf-dist/tex/latex/tools/longtable.sty",
        "/usr/share/texmf-dist/tex/latex/tools/array.sty",
    ]
    calls = _kpsewhich_prints(monkeypatch, "\n".join(found) + "\n")

    assert doctor._missing_latex_packages() == [
        "fontspec",
        "caption",
        "xcolor",
        "lmodern",
        "lmodern fonts",
    ]
    assert len(calls) == 1
    assert calls[0] == ["kpsewhich", *(probe for _, probe in doctor.LATEX_PACKAGES)]


def test_missing_latex_packages_is_empty_when_everything_is_found(monkeypatch):
    out = "".join(f"/texmf/{probe}\n" for _, probe in doctor.LATEX_PACKAGES)
    _kpsewhich_prints(monkeypatch, out)

    assert doctor._missing_latex_packages() == []


def test_missing_latex_packages_names_all_when_none_is_found(monkeypatch):
    _kpsewhich_prints(monkeypatch, "")

    assert doctor._missing_latex_packages() == LATEX_NAMES


def test_missing_latex_packages_is_none_without_kpsewhich(monkeypatch):
    def fake_run(command, **kwargs):
        raise FileNotFoundError("kpsewhich")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    assert doctor._missing_latex_packages() is None


# --- The table, the template and the platforms agree -------------------------


def _unconditional_packages() -> set[str]:
    template = (Path(doctor.__file__).parent / "templates" / "xecjk.tex").read_text()
    template = re.sub(r"\$if\(cjkfont\)\$.*?\$endif\$", "", template, flags=re.DOTALL)
    return set(re.findall(r"\\usepackage(?:\[[^\]]*\])?\{([^}]*)\}", template))


def test_every_package_the_template_always_loads_has_a_row():
    rows = {name for name, _ in doctor.LATEX_PACKAGES}
    loaded = {
        package.strip()
        for packages in _unconditional_packages()
        for package in packages.split(",")
    }

    assert loaded
    assert loaded <= rows


def test_both_platform_tables_list_the_doctor_tables_names():
    from vimdiomas.platform import linux, macos

    names = set(LATEX_NAMES)
    assert set(macos.LATEX_PACKAGES) == names
    assert set(linux.LATEX_PACKAGES) == names
