FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos necesarios
COPY . /app

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el archivo .env
COPY .env /app/.env

# Configurar Python para que no almacene en búfer la salida
ENV PYTHONUNBUFFERED=1

# Comando de inicio
CMD ["python", "monitor.py"]
