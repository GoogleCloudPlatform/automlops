FROM python:3.9
RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN python -m pip install -r     requirements.txt --quiet --no-cache-dir     && rm -f requirements.txt
WORKDIR /
COPY trainer /trainer
ENTRYPOINT ["python", "-m", "trainer.task"]