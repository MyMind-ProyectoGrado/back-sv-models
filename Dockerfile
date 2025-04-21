FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Bogota 

WORKDIR /app

# Instalar solo lo necesario del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sox \
    ffmpeg \
    libsndfile1 \
    tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
