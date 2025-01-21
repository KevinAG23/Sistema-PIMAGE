# Usar una imagen base ligera de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos del frontend
COPY . .

# Exponer el puerto para el servidor HTTP
EXPOSE 5500

# Comando para iniciar el servidor HTTP
CMD ["python3", "-m", "http.server", "5500"]
