import hashlib
import json
from datetime import datetime

class Bloco:
    def __init__(self, index, transacoes, hash_anterior):
        self.index = index
        self.timestamp = datetime.utcnow().isoformat()
        self.transacoes = transacoes
        self.hash_anterior = hash_anterior
        self.nonce = 0
        self.hash = self._calcular_hash()
    
    def _calcular_hash(self):
        """Calcula o hash do bloco"""
        bloco_str = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transacoes': self.transacoes,
            'hash_anterior': self.hash_anterior,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(bloco_str).hexdigest()
    
    def minerar(self, dificuldade=2):
        """Realiza a prova de trabalho (mineração)"""
        alvo = "0" * dificuldade
        while not self.hash.startswith(alvo):
            self.nonce += 1
            self.hash = self._calcular_hash()
        print(f"Bloco {self.index} minerado: {self.hash}")

class Blockchain:
    def __init__(self, dificuldade=2):
        self.cadeia = [self._criar_bloco_genesis()]
        self.transacoes_pendentes = []
        self.dificuldade = dificuldade
    
    def _criar_bloco_genesis(self):
        """Cria o primeiro bloco da cadeia (bloco gênesis)"""
        return Bloco(0, [], "0")
    
    def adicionar_transacao(self, transacao):
        """Adiciona uma transação à lista de pendentes"""
        self.transacoes_pendentes.append(transacao)
    
    def minerar_transacoes_pendentes(self):
        """Minera todas as transações pendentes em um novo bloco"""
        if not self.transacoes_pendentes:
            return None
        
        ultimo_bloco = self.cadeia[-1]
        novo_bloco = Bloco(
            len(self.cadeia),
            self.transacoes_pendentes,
            ultimo_bloco.hash
        )
        
        print(f"Minerando bloco {novo_bloco.index}...")
        novo_bloco.minerar(self.dificuldade)
        self.cadeia.append(novo_bloco)
        self.transacoes_pendentes = []
        
        return novo_bloco
    
    def verificar_transacao(self, doc_hash):
        """Verifica se uma transação existe na blockchain"""
        for bloco in self.cadeia:
            for transacao in bloco.transacoes:
                if transacao.get('hash') == doc_hash:
                    return True
        return False
    
    def validar_cadeia(self):
        """Valida a integridade da blockchain"""
        for i in range(1, len(self.cadeia)):
            atual = self.cadeia[i]
            anterior = self.cadeia[i-1]
            
            if atual.hash != atual._calcular_hash():
                print(f"Hash inválido no bloco {atual.index}")
                return False
            
            if atual.hash_anterior != anterior.hash:
                print(f"Encadeamento quebrado no bloco {atual.index}")
                return False
        
        return True
    
    def get_cadeia(self):
        """Retorna a cadeia completa em formato de dicionário"""
        return [bloco.__dict__ for bloco in self.cadeia]

    def to_dict(self):
        """Converte a blockchain para dicionário serializável"""
        return {
            'cadeia': [bloco.__dict__ for bloco in self.cadeia],
            'dificuldade': self.dificuldade
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria uma blockchain a partir de um dicionário"""
        blockchain = cls(data['dificuldade'])
        blockchain.cadeia = []
        
        for bloco_data in data['cadeia']:
            bloco = Bloco(
                bloco_data['index'],
                bloco_data['transacoes'],
                bloco_data['hash_anterior']
            )
            bloco.timestamp = bloco_data['timestamp']
            bloco.nonce = bloco_data['nonce']
            bloco.hash = bloco_data['hash']
            blockchain.cadeia.append(bloco)
        
        return blockchain

    def get_latest_block_hash(self):
        """Retorna o hash do último bloco"""
        return self.cadeia[-1].hash if self.cadeia else "0"
