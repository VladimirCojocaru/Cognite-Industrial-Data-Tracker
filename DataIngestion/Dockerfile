FROM python:3.10

WORKDIR /DataIngestion

COPY DataIngestion/Requirements.txt .

RUN pip install --no-cache-dir -r Requirements.txt



COPY DataIngestion/dataIngestion.py .
COPY jsonFiles ./jsonFiles
COPY envFiles ./envFiles

CMD ["python", "./dataIngestion.py"]