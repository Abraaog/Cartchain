from kazoo.client import KazooClient
import json
import time
import uuid
import os  # Importação necessária

class ZooKeeperClient:
    def __init__(self, hosts='127.0.0.1:2181', node_id=None):
        self.hosts = hosts
        self.node_id = node_id or str(uuid.uuid4())
        self.zk = KazooClient(hosts=hosts)
        self.zk.start()
        self._ensure_paths()
    
    def _ensure_paths(self):
        """Garante que os caminhos necessários existam"""
        paths = ['/cartorio', '/cartorio/documentos', '/cartorio/eleicao']
        for path in paths:
            self.zk.ensure_path(path)
    
    def registrar_documento(self, doc_hash, proprietario):
        """Registra um documento no ZooKeeper (sobrescreve se já existir)"""
        path = f'/cartorio/documentos/{doc_hash}'
        data = {
            'proprietario': proprietario,
            'timestamp': time.time(),
            'hash': doc_hash,
            'node_id': self.node_id
        }
        
        print(f"Tentando registrar documento: {doc_hash}")
        print(f"Caminho: {path}")
        print(f"Dados: {data}")
        
        try:
            # Verificar se o caminho pai existe
            parent_path = '/cartorio/documentos'
            if not self.zk.exists(parent_path):
                print(f"Criando caminho pai: {parent_path}")
                self.zk.ensure_path(parent_path)
            
            # Verificar se o znode já existe e deletar se existir
            if self.zk.exists(path):
                print(f"Documento já existe, sobrescrevendo: {path}")
                self.zk.delete(path)
            
            # Criar o znode
            self.zk.create(path, json.dumps(data).encode(), ephemeral=False)
            print(f"✅ Documento registrado com sucesso: {path}")
            return True, path
                
        except Exception as e:
            print(f"❌ ERRO ao registrar documento: {str(e)}")
            print(f"Tipo do erro: {type(e).__name__}")
            return False, str(e)
    
    def verificar_documento(self, doc_hash):
        """Verifica se um documento existe e retorna seus dados"""
        path = f'/cartorio/documentos/{doc_hash}'
        if self.zk.exists(path):
            data, _ = self.zk.get(path)
            return json.loads(data.decode())
        return None
    
    def participar_eleicao(self):
        """Participa da eleição de líder usando znodes efêmeros sequenciais"""
        election_path = '/cartorio/eleicao/node_'
        try:
            path = self.zk.create(election_path, ephemeral=True, sequence=True)
            return path.split('/')[-1]
        except Exception as e:
            print(f"Erro na eleição: {e}")
            return None
    
    def verificar_lider(self):
        """Verifica quem é o líder atual (menor número sequencial)"""
        children = self.zk.get_children('/cartorio/eleicao')
        if children:
            return sorted(children)[0]
        return None
    
    def eh_lider(self):
        """Verifica se este nó é o líder"""
        lider = self.verificar_lider()
        if lider:
            meu_node = f"node_{self.node_id}"
            children = self.zk.get_children('/cartorio/eleicao')
            for child in children:
                data, _ = self.zk.get(f'/cartorio/eleicao/{child}')
                if data.decode() == self.node_id:
                    return child == lider
        return False
    
    def listar_documentos(self):
        """Lista todos os documentos registrados"""
        documentos = []
        children = self.zk.get_children('/cartorio/documentos')
        for child in children:
            data, _ = self.zk.get(f'/cartorio/documentos/{child}')
            documentos.append(json.loads(data.decode()))
        return documentos
    
    def fechar(self):
        """Fecha a conexão com o ZooKeeper"""
        self.zk.stop()
        self.zk.close()
