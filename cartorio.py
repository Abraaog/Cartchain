from zk_client import ZooKeeperClient
from blockchain import Blockchain
import hashlib
import os
import time
import json
import threading

class CartorioDigital:
    def __init__(self, node_id, zk_hosts='127.0.0.1:2181'):
        self.node_id = node_id
        self.zk = ZooKeeperClient(zk_hosts, node_id)
        self.blockchain = Blockchain()
        self.election_node = None
        self.is_leader = False
        
    def iniciar(self):
        """Inicia o nó e participa da eleição"""
        print(f"Nó {self.node_id} iniciando...")
        
        # Participa da eleição de líder
        self.election_node = self.zk.participar_eleicao()
        if self.election_node:
            print(f"Nó {self.node_id} entrou na eleição como: {self.election_node}")
        
        # Verifica se é líder periodicamente
        self._verificar_lider()
        
        # Inicia sincronização periódica da blockchain
        def sincronizar_periodicamente():
            while True:
                time.sleep(5)  # Sincroniza a cada 5 segundos
                self._sincronizar_blockchain()
        
        threading.Thread(target=sincronizar_periodicamente, daemon=True).start()
    
    def _verificar_lider(self):
        """Verifica se este nó é o líder atual"""
        lider = self.zk.verificar_lider()
        if lider:
            self.is_leader = (lider == self.election_node)
            print(f"Nó {self.node_id} é líder: {self.is_leader}")
        else:
            self.is_leader = False
            print(f"Nó {self.node_id} ainda não há líder")
    
    def registrar_documento(self, arquivo_path):
        """Registra um documento no cartório digital"""
        print(f"\n=== Registrando documento ===")
        print(f"Arquivo: {arquivo_path}")
        
        if not os.path.exists(arquivo_path):
            print(f"❌ Arquivo não encontrado: {arquivo_path}")
            return False, f"Arquivo não encontrado: {arquivo_path}"
        
        try:
            doc_hash = self._calcular_hash(arquivo_path)
            print(f"Hash calculado: {doc_hash}")
        except Exception as e:
            print(f"❌ Erro ao calcular hash: {e}")
            return False, f"Erro ao calcular hash: {e}"
        
        print("Registrando no ZooKeeper...")
        sucesso, resultado = self.zk.registrar_documento(doc_hash, self.node_id)
        if not sucesso:
            print(f"❌ Falha ao registrar no ZooKeeper: {resultado}")
            return False, f"Erro ao registrar no ZooKeeper: {resultado}"
        
        print(f"✅ Documento registrado no ZooKeeper: {doc_hash}")
        
        print("Adicionando à blockchain...")
        try:
            self.blockchain.adicionar_transacao({
                'tipo': 'registro',
                'hash': doc_hash,
                'proprietario': self.node_id,
                'timestamp': time.time(),
                'arquivo': os.path.basename(arquivo_path)
            })
            print("✅ Transação adicionada à blockchain")
            print(f"Blockchain agora tem {len(self.blockchain.cadeia)} blocos")
            print(f"Transações pendentes: {len(self.blockchain.transacoes_pendentes)}")
            
        except Exception as e:
            print(f"❌ Erro ao adicionar à blockchain: {e}")
            return False, f"Erro ao adicionar à blockchain: {e}"
        
        print(f"✅ Documento registrado com sucesso: {doc_hash}")
        return True, doc_hash
    
    def verificar_documento(self, arquivo_path):
        """Verifica a autenticidade de um documento"""
        # Primeiro sincroniza com o ZooKeeper
        self._sincronizar_blockchain()
        
        doc_hash = self._calcular_hash(arquivo_path)
        
        # 1. Verifica no ZooKeeper
        registro = self.zk.verificar_documento(doc_hash)
        if not registro:
            return False, "Documento não registrado no ZooKeeper"
        
        # 2. Verifica na blockchain (agora sincronizada)
        if not self.blockchain.verificar_transacao(doc_hash):
            return False, "Documento não encontrado na blockchain"
        
        return True, registro    
    
    def minerar_bloco(self):
        """Minera um novo bloco (apenas o líder pode fazer isso)"""
        if not self.is_leader:
            return False, "Apenas o líder pode minerar blocos"
    
        novo_bloco = self.blockchain.minerar_transacoes_pendentes()
        if novo_bloco:
            # Salva a blockchain atualizada no ZooKeeper
            self._salvar_blockchain_no_zookeeper()
            return True, f"Bloco {novo_bloco.index} minerado com sucesso"
        return False, "Nenhuma transação pendente para minerar"

    def listar_todos_documentos(self):
        """Lista todos os documentos registrados no sistema"""
        return self.zk.listar_documentos()
    
    def validar_blockchain(self):
        """Valida a integridade da blockchain local"""
        return self.blockchain.validar_cadeia()
    
    def status(self):
        """Retorna o status atual do nó"""
        self._verificar_lider()
        return {
            'node_id': self.node_id,
            'is_leader': self.is_leader,
            'election_node': self.election_node,
            'blockchain_length': len(self.blockchain.cadeia),
            'pending_transactions': len(self.blockchain.transacoes_pendentes)
        }
    
    def _calcular_hash(self, arquivo_path):
        """Calcula o hash SHA-256 de um arquivo"""
        sha256 = hashlib.sha256()
        with open(arquivo_path, 'rb') as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def imprimir_blockchain(self):
        """Imprime a blockchain para depuração"""
        print("=== BLOCKCHAIN ===")
        for i, bloco in enumerate(self.blockchain.cadeia):
            print(f"Bloco {i}:")
            print(f"  Índice: {bloco.index}")
            print(f"  Hash: {bloco.hash}")
            print(f"  Hash Anterior: {bloco.hash_anterior}")
            print(f"  Timestamp: {bloco.timestamp}")
            print(f"  Nonce: {bloco.nonce}")
            print(f"  Transações ({len(bloco.transacoes)}):")
            for j, tx in enumerate(bloco.transacoes):
                print(f"    {j+1}. {tx}")
            print()
        print("================")
    
    def _salvar_blockchain_no_zookeeper(self):
        """Salva a blockchain atual no ZooKeeper"""
        try:
            blockchain_data = self.blockchain.to_dict()
            path = '/cartorio/blockchain'
            
            if self.zk.zk.exists(path):
                self.zk.zk.set(path, json.dumps(blockchain_data).encode())
            else:
                self.zk.zk.create(path, json.dumps(blockchain_data).encode())
            
            print(f"✅ Blockchain salva no ZooKeeper: {len(self.blockchain.cadeia)} blocos")
            
        except Exception as e:
            print(f"❌ Erro ao salvar blockchain no ZooKeeper: {e}")

    def _carregar_blockchain_do_zookeeper(self):
        """Carrega a blockchain do ZooKeeper"""
        try:
            path = '/cartorio/blockchain'
            if self.zk.zk.exists(path):
                data, _ = self.zk.zk.get(path)
                blockchain_data = json.loads(data.decode())
                self.blockchain = Blockchain.from_dict(blockchain_data)
                print(f"✅ Blockchain carregada do ZooKeeper: {len(self.blockchain.cadeia)} blocos")
                return True
            else:
                print("ℹ️  Nenhuma blockchain encontrada no ZooKeeper")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao carregar blockchain do ZooKeeper: {e}")
            return False

    def _sincronizar_blockchain(self):
        """Sincroniza a blockchain com o ZooKeeper"""
        if self.is_leader:
            self._salvar_blockchain_no_zookeeper()
        else:
            self._carregar_blockchain_do_zookeeper()
    
    def fechar(self):
        """Fecha as conexões"""
        self.zk.fechar()
