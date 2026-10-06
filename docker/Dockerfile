# Vimdiomas' Linux verification image (Sprint 5 M7): an Arch Linux machine
# with every dependency installed, and Vimdiomas deliberately *not* installed —
# the point is to follow the README's Linux section inside it.
#
# Arch's official image is amd64-only; on Apple Silicon build and run it
# with --platform linux/amd64. See docker/README.md.

FROM archlinux:latest

# pacman 7 downloads as a sandboxed user restricted by seccomp, which
# fails under amd64 emulation on Apple Silicon ("error restricting syscalls
# via seccomp"). The sandbox guards downloads, not the installed system, so
# a throwaway test image can do without it.
RUN sed -i '/^\[options\]/a DisableSandbox' /etc/pacman.conf

RUN pacman -Syu --noconfirm --needed \
        python \
        git \
        pandoc-cli \
        texlive-xetex \
        texlive-latexrecommended \
        texlive-fontsrecommended \
        texlive-langchinese \
        noto-fonts-cjk \
        fontconfig \
        poppler \
    && pacman -Scc --noconfirm

# Vimdiomas needs Python 3.14+. Fail the build loudly rather than let the
# README's install fail later inside the container.
RUN python -c 'import sys; assert sys.version_info >= (3, 14), sys.version'

# The repo is bind-mounted from the host, owned by another uid; let git
# clone from it anyway. Only ever done in this throwaway image.
RUN git config --system --add safe.directory '*'

# A regular user with bash as the login shell, so the wizard's linking and
# PATH steps run against a realistic $HOME and ~/.bashrc.
RUN useradd --create-home --shell /bin/bash learner
USER learner
WORKDIR /home/learner
ENV SHELL=/bin/bash

CMD ["/bin/bash", "-l"]
