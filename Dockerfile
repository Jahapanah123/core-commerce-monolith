FROM python:3.11

WORKDIR /app

# system deps (IMPORTANT)
RUN apt-get update && apt-get install -y gcc build-essential

# install poetry
RUN pip install --no-cache-dir --upgrade pip setuptools wheel poetry

# copy dependency files first (cache layer)
COPY pyproject.toml poetry.lock ./

# install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# copy full project
COPY . .

# default command (overridden in compose for worker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]