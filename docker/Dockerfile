FROM python:3.14
LABEL Pierre Augier <pierre.augier@univ-grenoble-alpes.fr>
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update
RUN apt-get install -y --no-install-recommends rsync unzip git vim sudo

RUN rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 appuser && useradd -m -r -u 1000 -g appuser -s /bin/bash appuser -s /bin/bash && usermod -a -G sudo appuser
RUN echo appuser:appuser | chpasswd
USER appuser
ARG HOME=/home/appuser
RUN mkdir -p $HOME/opt
WORKDIR $HOME/opt
RUN echo $USER $HOME $PWD && whoami

RUN mkdir -p $HOME/.local/bin
ENV PATH=$HOME/.local/bin:$HOME/.pixi/bin:$PATH

RUN uv --version

RUN uv tool install pdm
RUN pdm --version

RUN pdm py install 3.11
RUN pdm py install 3.12
RUN pdm py install 3.13

RUN uv tool install mercurial --with hg-evolve,hg-git
RUN uvx hg-setup init --auto --name py-edu-fr-devs --email py-edu-fr@no-mail.fr

RUN hg version -v
RUN hg debuginstall

# Install Pixi
RUN wget https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-unknown-linux-musl.tar.gz
RUN tar -xzf pixi-x86_64-unknown-linux-musl.tar.gz
RUN mv pixi $HOME/.local/bin

RUN pixi --version

RUN pixi global install micromamba
