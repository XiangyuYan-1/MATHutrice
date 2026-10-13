# Build one immutable image per commit and run it unchanged in every
# environment. Runtime settings are supplied by the environment, never baked
# into the image.
FROM python:3.14.7-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv

ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Keep dependency installation cached when only application code changes.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY mathutrice ./mathutrice
RUN uv sync --locked --no-dev

# The application writes uploaded PDFs and its ephemeral SQLite database at
# runtime. Run it as an unprivileged user that owns only the required paths.
RUN useradd --system --no-create-home app \
    && mkdir -p mathutrice/rag_documents \
    && chown app /app mathutrice/rag_documents
USER app

ENV PATH="/app/.venv/bin:$PATH"

# The workflow supplies the commit SHA. The application returns it in the
# X-Revision header so a deploy can prove that the new image is answering.
ARG REVISION=unknown
ENV REVISION=$REVISION

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn mathutrice.app:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
