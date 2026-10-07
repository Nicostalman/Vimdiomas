# Linux verification image

[`Dockerfile`](Dockerfile) builds an Arch Linux image with every dependency installed and Vimdiomas left out, so the Linux install can be tried from scratch. It works with any Docker runtime (on a Mac, [OrbStack](https://orbstack.dev) is the lightest). The official Arch image is amd64-only, so on Apple Silicon it runs under emulation — slower, but it works.

From the repo root:

```sh
docker build --platform linux/amd64 -t vimdiomas-linux docker/
docker run --rm -it --platform linux/amd64 -e TERM_PROGRAM -v "$PWD":/src:ro vimdiomas-linux
```

`-v` mounts your checkout read-only at `/src`. `-e TERM_PROGRAM` passes your terminal's name in, so Inspect Tree's PDF preview works from a terminal that supports it.

`learner`'s password is `learner`: `sudo` asks for it when the wizard installs something.

Inside, follow *Installing* in the [main README](../readme.md#installing) as written. To try a branch that isn't on GitHub yet, clone the mounted checkout in step 1 instead:

```sh
git clone -b <branch> /src ~/.local/share/vimdiomas
```

To run the test suite (commit your changes first, since this clones rather than copies):

```sh
git clone -b <branch> /src ~/vimdiomas && cd ~/vimdiomas
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

To look at a compiled PDF on the host, `docker cp <container>:/home/learner/Documents/Vimdiomas/tree-Chinese/Vocabulary/Food.pdf .` copies it out.

## Bare image

For the wizard's *Install missing* (Sprint 8), build the image with only `python`, `git` and `sudo`:

```sh
docker build --platform linux/amd64 --build-arg BARE=1 -t vimdiomas-linux-bare docker/
docker run --rm -it --platform linux/amd64 -e TERM_PROGRAM -v "$PWD":/src:ro vimdiomas-linux-bare
```

Follow *Installing* as above. The wizard's first step lists everything as missing, and *Install missing* installs it all with `pacman` (password `learner`). Ticking Chinese at step 3 then offers xeCJK and the CJK font.
