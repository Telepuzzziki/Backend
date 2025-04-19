# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Порт, который будет слушать приложение (измените на ваш)
EXPOSE 8080

# Команда для запуска приложения
CMD ["python", "-m", "app.main"]