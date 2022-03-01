FROM python:3.10-slim
RUN useradd manabi
ENV PATH="/home/manabi/.local/bin:${PATH}"
WORKDIR /app
COPY --chown=manabi \
    pyproject.toml \
    poetry.lock \
    .flake8 \
    MANIFEST.in \
    README.md \
    /app/
RUN mkdir c && mkdir manabi && touch manabi/__init__.py
COPY --chown=manabi c/install c/pipinstall /app/c/
RUN c/install
USER manabi
CMD poetry run python -m manabi
