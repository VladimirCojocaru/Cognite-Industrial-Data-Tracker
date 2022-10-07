FROM python:3.10.4

WORKDIR /Backend

COPY Backend/Requirements.txt .

RUN pip install --no-cache-dir -r Requirements.txt
RUN apt update && apt install -y telnet curl tcpdump


EXPOSE 5000

COPY Backend/Flask/flask_backend.py .
COPY envFiles ./envFiles

CMD ["python", "./flask_backend.py"]