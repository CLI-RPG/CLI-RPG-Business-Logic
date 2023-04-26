FROM python:3.10
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
COPY . /app
WORKDIR /app
EXPOSE 5000
CMD ["python", "io_service.py"]