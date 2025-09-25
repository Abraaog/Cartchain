# Cartório Digital - Sistema Distribuído

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

## 🏛️ Sobre o Projeto

O **Cartório Digital** é uma aplicação distribuída desenvolvida como projeto final da disciplina de Sistemas Distribuídos. Este sistema demonstra conceitos fundamentais de computação distribuída através de uma solução prática para registro e validação de documentos com garantias de consistência, disponibilidade e tolerância a falhas.

### 🎯 Objetivo do Projeto

Este projeto tem como objetivo demonstrar na prática os conceitos teóricos de Sistemas Distribuídos vistos durante a disciplina, incluindo:

- **Eleição de Líder**: Mecanismo para coordenar operações no cluster
- **Replicação de Dados**: Garantia de disponibilidade e redundância
- **Coordenação Distribuída**: Gerenciamento do estado do sistema
- **Consistência**: Manutenção da integridade dos dados através de blockchain

## 🏗️ Arquitetura do Sistema
![Image](https://github.com/user-attachments/assets/f0df0626-ea4f-454b-bcb5-353c370b5636)

## 📋 Conceitos Implementados

### 1. Eleição de Líder
- **Descrição**: Algoritmo distribuído para eleger um nó coordenador
- **Implementação**: Utiliza ZooKeeper para gerenciar a eleição
- **Funcionalidade**: 
  - Apenas o líder pode registrar novos documentos
  - Detecção automática de falha do líder
  - Reeleição automática de novo líder
- **Vantagem**: Evita conflitos e garante ordem nas operações

### 2. Replicação de Dados
- **Descrição**: Todos os documentos são replicados para os nós seguidores
- **Implementação**: Comunicação HTTP entre nós após registro no líder
- **Funcionalidade**:
  - Replicação síncrona de documentos
  - Verificação de sucesso na replicação
  - Manutenção de múltiplas cópias dos dados
- **Vantagem**: Alta disponibilidade e tolerância a falhas

### 3. Coordenação Distribuída
- **Descrição**: ZooKeeper gerencia o estado e configuração do cluster
- **Implementação**: Nós efêmeros e watches para monitoramento
- **Funcionalidade**:
  - Registro de nós ativos no cluster
  - Monitoramento de saúde dos nós
  - Detecção de falhas em tempo real
- **Vantagem**: Visão global do estado do sistema

### 4. Consistência com Blockchain
- **Descrição**: Blockchain garante ordem e integridade dos documentos
- **Implementação**: Blocos encadeados com hash criptográfico
- **Funcionalidade**:
  - Cada documento é um bloco na blockchain
  - Hash criptográfico garante integridade
  - Cadeia de blocos garante ordem cronológica
- **Vantagem**: Imutabilidade e consistência sequencial

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Descrição |
|-----------|--------|-----------|
| **Python** | 3.9 | Linguagem principal de desenvolvimento |
| **Flask** | 2.3.3 | Framework web para criação de APIs |
| **ZooKeeper** | 3.7 | Sistema de coordenação distribuída |
| **Kazoo** | 2.8.0 | Cliente Python para ZooKeeper |
| **Docker** | 20.10+ | Plataforma de containerização |
| **Docker Compose** | 2.0+ | Orquestração de contêineres |
| **Requests** | 2.31.0 | Biblioteca para requisições HTTP |
| **PyCryptodome** | 3.15.0 | Biblioteca criptográfica |

## 🚀 Como Executar

### Pré-requisitos

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.9+](https://www.python.org/downloads/) (opcional, para desenvolvimento)
## Passo 1: Clonar o Repositório

```bash
git clone https://github.com/Abraaog/CartorioDigital.git
cd cartorio-digital
```
## Passo 2: Iniciar o Sistema
### Construir e iniciar todos os contêineres
```bash
docker-compose up -d
```
### Verificar status dos contêineres
```bash
docker-compose ps
```
## Passo 3: Verificar Funcionamento
### Verificar status dos nós
```bash
curl http://localhost:5001/status
curl http://localhost:5002/status
curl http://localhost:5003/status
```
### Registrar um documento
```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"document":"Contrato de Aluguel - Teste"}'
```
### Verificar blockchain
```bash
curl http://localhost:5001/blockchain
```
## Passo 4: Executar Demonstração Completa
### Executar script de demonstração
```bash
python demo.py
```

## 📊 Estrutura do Projeto
```bash
cartorio-digital/
├── app/                          # Código da aplicação
│   ├── __init__.py              # Inicialização do pacote
│   ├── blockchain.py            # Implementação da blockchain
│   ├── node.py                  # Lógica do nó distribuído
│   ├── zk_utils.py              # Utilitários do ZooKeeper
│   └── requirements.txt         # Dependências Python
├── demo.py                       # Script de demonstração
├── docker-compose.yml           # Orquestração Docker
├── Dockerfile                   # Imagem Docker da aplicação
└── README.md                    # Documentação do projeto
```

## 👥 Autores

| Nome | GitHub |
| :--- | :--- |
| **ABRAAO GOMES DA SILVA ARAUJO** | [@Abraaog](https://github.com/seu-usuario) |
| **THASSO KARLY MORAIS RAMOS** | [@Thasso](https://github.com/thassokarly) |
| **JOHN WESLEY DA SILVA MOREIRA PINTO** | [@JohnWesley](https://github.com/JohnWesleyPinto) |


# 🧪 Testes e Validação
## Cenários de Teste
### 1. Operação Normal
- Sistema inicia com 3 nós
- Um nó é eleito líder
- Documentos são registrados e replicados
- Todos os nós permanecem sincronizados

### 2. Falha do Líder
- Líder atual é identificado
- Simulação de falha do líder
- Novo líder é eleito automaticamente
- Sistema continua operando normalmente

### 3. Verificação de Consistência
- Comparar blockchain entre todos os nós
- Verificar replicação bem-sucedida
- Confirmar integridade dos dados

## Comandos para Testes
### Verificar status do cluster
```bash
docker-compose ps
```
### Visualizar logs em tempo real
```bash
docker-compose logs -f node1 node2 node3
```
### Simular falha de um nó
```bash
docker-compose stop node1
```
### Reiniciar nó falho
```bash
docker-compose start node1
```
### Parar todo o sistema
```bash
docker-compose down
```
## 📈 Resultados Esperados
### Métricas de Desempenho
- Tempo de eleição de líder: < 5 segundos
- Tempo de replicação: < 2 segundos
- Disponibilidade do sistema: 99.9%
- Consistência dos dados: 100%

### Indicadores de Sucesso
- ✅ Sistema distribuído funcional
- ✅ Eleição de líder operacional
- ✅ Replicação de dados bem-sucedida
- ✅ Tolerância a falhas comprovada
- ✅ Consistência mantida em todos os nós
