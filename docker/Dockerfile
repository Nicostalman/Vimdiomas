# Vimdiomas' Linux verification image (Sprint 5 M7): an Arch Linux machine
# with every dependency installed, and Vimdiomas deliberately *not* installed —
# the point is to follow the README's Linux section inside it.
#
# With --build-arg BARE=1 (Sprint 8 M3) it is the other machine: only python,
# git and sudo, so the wizard's "Install missing" has everything to install.
# Without it, "Install missing" must not appear.
#
# Arch's official image is amd64-only; on Apple Silicon build and run it
# with --platform linux/amd64. See docker/README.md.

FROM archlinux:latest

ARG BARE=0

# pacman 7 downloads as a sandboxed user restricted by seccomp, which
# fails under amd64 emulation on Apple Silicon ("error restricting syscalls
# via seccomp"). The sandbox guards downloads, not the installed system, so
# a throwaway test image can do without it.
RUN sed -i '/^\[options\]/a DisableSandbox' /etc/pacman.conf

# `sudo` is in both variants: "Install missing" runs it, as it would on a real
# machine.
RUN if [ "$BARE" = "1" ]; then \
        pacman -Syu --noconfirm --needed python git sudo; \
    else \
        pacman -Syu --noconfirm --needed \
            python \
            git \
            sudo \
            pandoc-cli \
            texlive-xetex \
            texlive-latexrecommended \
            texlive-fontsrecommended \
            texlive-langchinese \
            noto-fonts-cjk \
            fontconfig \
            poppler; \
    fi \
    && pacman -Scc --noconfirm

# Vimdiomas needs Python 3.14+. Fail the build loudly rather than let the
# README's install fail later inside the container.
RUN python -c 'import sys; assert sys.version_info >= (3, 14), sys.version'

# The repo is bind-mounted from the host, owned by another uid; let git
# clone from it anyway. Only ever done in this throwaway image.
RUN git config --system --add safe.directory '*'

# A regular user with bash as the login shell, so the wizard's linking and
# PATH steps run against a realistic $HOME and ~/.bashrc. It has a password
# (`learner`) and is in `wheel`, so sudo asks for one through the suspended TUI
# as it does on a real machine.
RUN useradd --create-home --shell /bin/bash --groups wheel learner \
    && echo 'learner:learner' | chpasswd \
    && echo '%wheel ALL=(ALL:ALL) ALL' > /etc/sudoers.d/wheel
USER learner
WORKDIR /home/learner
ENV SHELL=/bin/bash

CMD ["/bin/bash", "-l"]
