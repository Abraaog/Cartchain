import hashlib
import json
from datetime import datetime
import logging

class Block:
    """Representa um único bloco na nossa blockchain."""
    def __init__(self, index, timestamp, data, previous_hash, hash_value=None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = hash_value if hash_value else self.calculate_hash()

    def calculate_hash(self):
        """Calcula o hash SHA-256 de um bloco."""
        # CORREÇÃO: Usar isoformat para consistência total com to_dict
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        """Converte o objeto Bloco num dicionário para serialização JSON."""
        return {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(block_dict):
        """Cria um objeto Bloco a partir de um dicionário."""
        return Block(
            index=block_dict['index'],
            timestamp=datetime.fromisoformat(block_dict['timestamp']),
            data=block_dict['data'],
            previous_hash=block_dict['previous_hash'],
            hash_value=block_dict['hash']
        )

class Blockchain:
    """Gere a cadeia de blocos, incluindo a sua adição e validação."""
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        """Cria o primeiro bloco da cadeia (Bloco Gênese)."""
        genesis_timestamp = datetime(2022, 12, 31, 21, 0, 0)
        return Block(0, genesis_timestamp, "Genesis Block", "0")

    def add_block(self, data):
        """Cria e adiciona um novo bloco à cadeia."""
        last_block = self.chain[-1]
        new_block = Block(
            index=last_block.index + 1,
            timestamp=datetime.now(),
            data=data,
            previous_hash=last_block.hash
        )
        self.chain.append(new_block)
        return new_block
    
    def add_replicated_block(self, new_block):
        """Adiciona um bloco recebido do líder após validação."""
        last_block = self.chain[-1]
        
        if new_block.index != last_block.index + 1:
            return False, "Índice inválido"
            
        if new_block.previous_hash != last_block.hash:
            return False, f"Hash anterior inválido. Esperado: {last_block.hash}, Recebido: {new_block.previous_hash}"
            
        if new_block.hash != new_block.calculate_hash():
            return False, "Hash do bloco inválido"
            
        self.chain.append(new_block)
        return True, "Bloco adicionado com sucesso"

    @staticmethod
    def is_chain_valid(chain_of_blocks):
        """Valida uma cadeia de blocos completa."""
        genesis_block = chain_of_blocks[0]
        if genesis_block.index != 0 or genesis_block.previous_hash != "0":
            return False

        for i in range(1, len(chain_of_blocks)):
            current_block = chain_of_blocks[i]
            previous_block = chain_of_blocks[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
            if current_block.index != previous_block.index + 1:
                return False
        return True

    def replace_chain(self, new_chain_dicts):
        """
        Substitui a cadeia local por uma nova se ela for mais longa e válida.
        """
        if len(new_chain_dicts) <= len(self.chain):
            logging.info("A cadeia recebida não é mais longa que a atual.")
            return False, "Cadeia não é mais longa"

        try:
            new_chain = [Block.from_dict(b) for b in new_chain_dicts]
        except Exception as e:
            logging.error(f"Erro ao converter a cadeia recebida: {e}")
            return False, "Formato de bloco inválido"

        if not self.is_chain_valid(new_chain):
            logging.warning("A cadeia recebida é inválida.")
            return False, "Cadeia inválida"

        logging.info(f"Substituindo a cadeia local ({len(self.chain)} blocos) pela nova ({len(new_chain)} blocos).")
        self.chain = new_chain
        return True, "Cadeia substituída com sucesso"

