FROM python:3.11-slim

# рабочая директория
WORKDIR /app

# системные зависимости (если нужны для aiohttp и др.)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# копируем requirements
COPY requirements.txt .

# устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# копируем весь проект
COPY . .

# переменная окружения для логов python
ENV PYTHONUNBUFFERED=1

# запуск бота
CMD ["python", "main.py"]