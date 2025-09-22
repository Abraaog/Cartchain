FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip para versão mais recente
RUN pip install --no-cache-dir --upgrade pip

# Copiar e instalar dependências Python
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app/ .

ENV NODE_ID=1
EXPOSE 5000

CMD ["python", "node.py"]