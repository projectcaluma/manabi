ARG VERSION=latest
FROM acr.run/camac-ng/manabi:$VERSION
COPY --chown=manabi . /app/
CMD pipenv run python -m manabi
