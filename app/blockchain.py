import hashlib
import json
import time
import logging

class Block:
    """
    Representa um único bloco na nossa blockchain.
    """
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Calcula o hash SHA-256 do conteúdo do bloco.
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        """
        Converte o objeto Bloco para um dicionário para serialização (JSON).
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(block_dict):
        """
        Cria um objeto Bloco a partir de um dicionário.
        """
        return Block(
            index=block_dict['index'],
            timestamp=block_dict['timestamp'],
            data=block_dict['data'],
            previous_hash=block_dict['previous_hash']
        )

class Blockchain:
    """
    Representa a nossa blockchain, uma lista de blocos.
    """
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        """
        Cria o primeiro bloco da cadeia (Bloco Gênese).
        O timestamp é fixo para garantir que todos os nós comecem com o mesmo hash.
        """
        # --- MODIFICAÇÃO 1: Timestamp fixo ---
        return Block(0, 1672531200, "Genesis Block", "0") # 1672531200 é 01/01/2023 00:00:00 UTC

    def get_last_block(self):
        """
        Retorna o último bloco da cadeia.
        """
        return self.chain[-1]

    def add_block(self, data):
        """
        Cria e adiciona um novo bloco à cadeia (usado pelo líder).
        """
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=last_block.hash
        )
        self.chain.append(new_block)
        return new_block

    def add_replicated_block(self, block):
        """
        Adiciona um bloco que foi replicado de outro nó (usado pelos seguidores).
        Inclui validação.
        """
        last_block = self.get_last_block()

        # Validação 1: O índice está correto?
        if block.index != last_block.index + 1:
            logging.error(f"Bloco Rejeitado: Índice inválido. Esperado: {last_block.index + 1}, Recebido: {block.index}")
            return False, "Índice inválido"

        # Validação 2: O hash anterior corresponde?
        if block.previous_hash != last_block.hash:
            logging.error(f"Bloco Rejeitado: Hash anterior inválido. Esperado: {last_block.hash}, Recebido: {block.previous_hash}")
            return False, "Hash anterior inválido"
        
        # --- MODIFICAÇÃO 2: Prevenir adição de duplicados ---
        # Validação 3: Já temos este bloco?
        if any(b.hash == block.hash for b in self.chain):
            logging.warning(f"Bloco Rejeitado: Bloco duplicado com hash {block.hash}")
            return False, "Bloco duplicado"

        # Validação 4: O hash do próprio bloco é válido?
        if block.hash != block.calculate_hash():
            logging.error(f"Bloco Rejeitado: Hash do bloco é inválido.")
            return False, "Hash do bloco inválido"

        self.chain.append(block)
        return True, "Bloco aceite"
