FROM python:3.7-slim
RUN useradd manabi
ENV PATH="/home/manabi/.local/bin:${PATH}"
COPY --chown=manabi . /app
WORKDIR /app
RUN c/install
USER manabi
CMD pipenv run python -m manabi
