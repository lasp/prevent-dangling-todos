# This Dockerfile sets up a development environment for the project
# It is tested on an M3 Mac but is intended to work for x86 architectures as well.
FROM python:3.12-slim
ARG TARGETPLATFORM
ARG USERNAME=devuser

RUN adduser $USERNAME

# Install basic development tools and iptables/ipset
RUN apt update && apt install -y less \
  git \
  procps \
  sudo \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  curl \
  wget \
  vim \
  libgdal-dev \
  g++ \
  libc6 \
  && rm -rf /var/lib/apt/lists/*

# Install Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash && \
  apt-get install -y git-lfs

# Install NodeJS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# Ensure default devuser user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R $USERNAME:$USERNAME /usr/local/share

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Create Claude config directory and set permissions
RUN mkdir -p /home/$USERNAME/.claude && \
  chown -R $USERNAME:$USERNAME /home/$USERNAME/.claude

# Create virtual environment and permanently activate it for this image
# Note this venv is created outside of the context of the repo. If the devcontainer is created in mount mode,
# we don't want to overwrite any local virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV && chown $USERNAME:$USERNAME -R $VIRTUAL_ENV
# This adds not only the venv python executable but also all installed entrypoints to the PATH
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Set up non-root user
USER $USERNAME

# Install global packages
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Set the default shell to zsh rather than sh
ENV SHELL=/bin/zsh

# Default Powerlevel10k theme
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.2.0/zsh-in-docker.sh)" -- \
  -p git \
  -p colorize \
  -p https://github.com/zsh-users/zsh-autosuggestions \
  -p https://github.com/zsh-users/zsh-completions \
  -x

# Install Claude
RUN npm install -g @anthropic-ai/claude-code

# Install uv
RUN pip install uv

# Copy and set up dev environment script
USER root
COPY setup-dev-environment.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/setup-dev-environment.sh

USER $USERNAME

# Copy CLAUDE.md and settings to Claude config directory
COPY CLAUDE.md /home/$USERNAME/.claude/
COPY claude-settings.json /home/$USERNAME/.claude/settings.json
