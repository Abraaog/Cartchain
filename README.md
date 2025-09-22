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
