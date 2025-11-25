# Simple devcontainer to run the ADK-based Python agent in Codespaces
FROM python:3.11-slim

# system deps
RUN apt-get update && apt-get install -y git curl build-essential

WORKDIR /workspace

# install pip packages later via devcontainer.json
COPY requirements.txt /workspace/requirements.txt
RUN pip install --upgrade pip && pip install -r /workspace/requirements.txt

# expose port for local metrics/UI
EXPOSE 8000
