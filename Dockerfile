# Usar uma imagem base leve do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# (Opcional) Instalar dependências do sistema
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Atualizar o pip
RUN pip install --no-cache-dir --upgrade pip

# Copiar o arquivo de dependências da subpasta 'app' para o WORKDIR
COPY app/requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da subpasta 'app' para o WORKDIR
COPY app/ .

# Expor a porta da aplicação Flask
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "node.py"]

