# Sandbox for every real kit-arms run (T175 AC 11): the agent sees only its own arm copy
# (bind-mounted rw at the same path) and the Claude credentials file (ro). run_arms.py builds it:
#   docker build -t kit-arms-claude:2.1.310 -f experiments/kit-arms/Dockerfile \
#     --build-context claude-bin=<dir holding the host's native claude binary, named 2.1.310> <empty dir>
# The binary is the host's own native build (ELF, glibc only), so every arm runs the exact same CLI.
FROM python:3.12-slim

ARG CLAUDE_VERSION=2.1.310

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ripgrep ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir pytest==9.0.2 \
 && git config --system user.name Sam \
 && git config --system user.email sam@example.com \
 && mkdir -p /tmp/h/.claude \
 && chmod -R 1777 /tmp/h

COPY --from=claude-bin --chmod=755 ${CLAUDE_VERSION} /usr/local/bin/claude

# Throwaway HOME (the container is removed after each run); no auto-update inside the sandbox.
ENV HOME=/tmp/h DISABLE_AUTOUPDATER=1
