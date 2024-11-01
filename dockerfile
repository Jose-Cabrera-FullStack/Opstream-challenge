# pull official base image
FROM python:3.11-slim

# set work directory
WORKDIR /usr/src/opstream

# Crear usuario no-root
RUN addgroup --system appgroup && adduser --system --group appuser

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Crear y activar entorno virtual
RUN python -m venv /usr/src/venv
ENV PATH="/usr/src/venv/bin:$PATH"

# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# Cambiar propiedad de archivos
RUN chown -R appuser:appgroup /usr/src/

USER appuser