# Vimdiomas

Store vocabulary efficiently into markdown files, tastefully compiled to PDF.

## Tutorial and overview

![Adding an entry to a category](docs/images/overview-1.png)

![Inspect tree in PDF mode, with the compiled PDF beside it](docs/images/overview-2.png)


Only Vim keybindings!



## Installing

Vimdiomas runs on **macOS** and **Linux**. Before you start, have the tools listed under [Dependencies](#dependencies) below, at least Python 3.14+ and git. The first-run wizard checks the rest.

```sh
# Download
git clone https://github.com/Nicostalman/Vimdiomas.git ~/.local/share/vimdiomas

# Setup
cd ~/.local/share/vimdiomas
python3 -m venv .venv
.venv/bin/pip install .

# Run once
~/.local/share/vimdiomas/.venv/bin/vimdiomas
```

From now on the app can be called by its name

```sh
vimdiomas
```

### The wizard

The first time you start Vimdiomas, it walks you through setting up. It runs **once** — once it has written your settings, starting Vimdiomas goes straight to your notebook.

Your settings are saved to `~/.config/vimdiomas/config.toml`.

**If the wizard says `~/.local/bin` isn't on your PATH**, open a new terminal after finishing the wizard — that's what picks up the line it just added — and `vimdiomas` will work. If it still doesn't, the line to add by hand is:

```sh
export PATH="$HOME/.local/bin:$PATH"
```


### Uninstalling

Delete the clone and the command. Your notebook and your settings are separate, and survive:

```sh
rm -rf ~/.local/share/vimdiomas
rm ~/.local/bin/vimdiomas
```

Your notes live wherever you pointed the wizard (`~/Documents/Vimdiomas` by default) and your settings in `~/.config/vimdiomas/`. Delete those too if you really mean it.

## Dependencies

Apart from Python and git, the wizard checks all of these for you on first run and tells you what's missing, with the install command for your system, so you don't have to work through these lists by hand.

### On macOS

**Required** — the app won't compile PDFs without these:

| | What it's for | Install |
|---|---|---|
| Python 3.14+ | Runs the app | `brew install python` |
| git | Downloads the app | `xcode-select --install` |
| pandoc | Markdown → LaTeX | `brew install pandoc` |
| TeX Live (or BasicTeX) | LaTeX → PDF | `brew install --cask basictex` |

**Only for Chinese** — you don't need these for the other languages, and the app offers to install `xeCJK` when you set Chinese up:

| | What it's for | Install |
|---|---|---|
| `xeCJK` | Typesets Chinese | `sudo tlmgr install xecjk` |
| Songti SC | The CJK font | Ships with macOS |

**Optional** — each one adds a feature, and without it only that feature is missing:

| | What it's for | Install |
|---|---|---|
| `macism` | Switches your keyboard between Chinese and English while you type | `brew install laishulu/homebrew/macism` |
| `nvim` | Opens source files from Inspect Tree | `brew install neovim` |
| `pdftoppm` | Inspect Tree's PDF preview | `brew install poppler` |

`xeCJK` is the one people miss: BasicTeX doesn't include it, and Chinese won't typeset without it.

### On Linux

**Required:**

| | What it's for | Arch | Debian / Ubuntu | Fedora |
|---|---|---|---|---|
| Python 3.14+ | Runs the app | `sudo pacman -S python` | `sudo apt install python3 python3-venv` | `sudo dnf install python3` |
| git | Downloads the app | `sudo pacman -S git` | `sudo apt install git` | `sudo dnf install git` |
| pandoc | Markdown → LaTeX | `sudo pacman -S pandoc-cli` | `sudo apt install pandoc` | `sudo dnf install pandoc` |
| TeX Live's XeTeX, with the recommended LaTeX packages and fonts | LaTeX → PDF | `sudo pacman -S texlive-xetex texlive-latexrecommended texlive-fontsrecommended` | `sudo apt install texlive-xetex texlive-latex-recommended texlive-fonts-recommended` | `sudo dnf install texlive-xetex texlive-collection-latexrecommended texlive-collection-fontsrecommended` |

**Only for Chinese** — the app offers to install these when you set Chinese up:

| | What it's for | Arch | Debian / Ubuntu | Fedora |
|---|---|---|---|---|
| `xeCJK` | Typesets Chinese | `sudo pacman -S texlive-langchinese` | `sudo apt install texlive-lang-chinese` | `sudo dnf install texlive-xecjk` |
| Noto Serif CJK SC | The CJK font | `sudo pacman -S noto-fonts-cjk` | `sudo apt install fonts-noto-cjk` | `sudo dnf install google-noto-serif-cjk-fonts` |

**Optional:**

| | What it's for | Arch | Debian / Ubuntu | Fedora |
|---|---|---|---|---|
| fcitx5 or ibus | Switches your keyboard between Chinese and English while you type | `sudo pacman -S fcitx5-im fcitx5-chinese-addons` | `sudo apt install fcitx5 fcitx5-chinese-addons` | `sudo dnf install fcitx5 fcitx5-chinese-addons` |
| `nvim` | Opens source files from Inspect Tree | `sudo pacman -S neovim` | `sudo apt install neovim` | `sudo dnf install neovim` |
| `pdftoppm` | Inspect Tree's PDF preview | `sudo pacman -S poppler` | `sudo apt install poppler-utils` | `sudo dnf install poppler-utils` |

Keyboard switching works with whichever of fcitx5 or ibus is running, and does nothing if neither is. PDFs compiled on Linux use Noto Serif CJK SC rather than macOS's Songti SC, so they look close to a Mac's but not identical.

WSL isn't supported. It may well work as plain Linux, but nothing there is tested.

### LaTeX packages

Besides XeTeX itself, the PDF template loads `fontspec`, `lmodern`, `geometry`, `longtable`, `caption`, `array` and `xcolor`, plus `xeCJK` for Chinese. The full TeX Live, BasicTeX and the Linux packages in the tables above all include them. A bare `texlive-xetex` on Arch does not, which is why the tables name the recommended collections too. `vimdiomas doctor` does not check for these packages individually: a missing one shows up as a LaTeX error when you compile.

### What `vimdiomas doctor` checks

```sh
vimdiomas doctor
```

It reports every dependency above as `ok` or missing, each marked `required`, `optional`, or with the language that needs it. It exits non-zero if a required one is gone, or one needed by a language in your config: a German-only install passes without `xeCJK`. Run it if compiling suddenly fails or your keyboard stops switching. The wizard checks all this on first run, but a tool can disappear later, usually after an OS or package-manager upgrade.

Chinese not typesetting, or a LaTeX error mentioning CJK, is almost always the missing `xeCJK` package. On macOS, `sudo tlmgr install xecjk`. On Linux, your distribution's Chinese TeX Live package from the table above (`texlive-langchinese` on Arch).