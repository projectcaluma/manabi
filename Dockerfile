FROM acr.run/camac-ng/manabi
COPY --chown=manabi . /app/
CMD pipenv run python -m manabi
