from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NodeExistsError, NoNodeError
import time
import logging

class ZooKeeperCoordinator:
    """Gere a ligação com o ZooKeeper, a eleição de líder e o registo de nós."""
    
    def __init__(self, node_address, hosts="zoo1:2181,zoo2:2181,zoo3:2181"):
        self.node_address = node_address
        self.zk = KazooClient(hosts=hosts)
        self.is_leader = False
        self.leader_path = "/cartorio/leader"
        self.nodes_path = "/cartorio/nodes"

    def connect(self):
        """Tenta conectar-se ao ZooKeeper de forma robusta."""
        while not self.zk.connected:
            try:
                logging.info(f"({self.node_address}) A tentar conectar-se ao ZooKeeper...")
                self.zk.start(timeout=10)
                self.zk.add_listener(self._zk_listener)
                logging.info(f"({self.node_address}) Conectado ao ZooKeeper com sucesso.")
            except Exception as e:
                logging.error(f"({self.node_address}) Não foi possível conectar-se ao ZooKeeper: {e}. A tentar novamente em 5s...")
                time.sleep(5)
        
        # Garantir que os caminhos base existem
        self.zk.ensure_path(self.nodes_path)

    def _zk_listener(self, state):
        """Ouve mudanças no estado da ligação com o ZooKeeper."""
        if state == KazooState.LOST:
            logging.warning(f"({self.node_address}) Ligação com o ZooKeeper perdida! A tentar reconectar...")
            # A reconexão é gerida automaticamente pelo Kazoo
        elif state == KazooState.SUSPENDED:
            logging.warning(f"({self.node_address}) Ligação com o ZooKeeper suspensa.")
        else:
            logging.info(f"({self.node_address}) Estado do ZooKeeper mudou para: {state}")

    def run_leader_election(self):
        """Inicia e mantém o processo de eleição de líder."""
        self.connect()
        self.register_node()

        while True:
            try:
                # Tenta criar o nó de líder efémero. Se conseguir, torna-se líder.
                self.zk.create(self.leader_path, self.node_address.encode(), ephemeral=True)
                self.is_leader = True
                logging.info(f"👑👑👑 Eu ({self.node_address}) fui eleito o novo LÍDER! 👑👑👑")
                # Como líder, apenas espera até que a ligação caia.
                while self.zk.connected:
                    time.sleep(1)

            except NodeExistsError:
                # O nó de líder já existe, por isso este nó é um seguidor.
                self.is_leader = False
                leader_address = self.get_leader_address()
                logging.info(f"👨‍💼 Um líder já existe em {leader_address}. Eu sou um seguidor.")
                
                # Espera aqui até que o nó do líder seja apagado.
                # A anotação @self.zk.DataWatch cria um "observador" que re-executa esta função
                # quando os dados no leader_path mudam (ou o nó é apagado).
                leader_deleted_event = self.zk.handler.event_object()
                
                @self.zk.DataWatch(self.leader_path)
                def watch_leader_node(data, stat):
                    if data is None: # O nó foi apagado
                        logging.warning("🚨 Líder caiu! Iniciando nova eleição...")
                        leader_deleted_event.set() # Sinaliza que a eleição deve recomeçar
                
                # Pausa a execução aqui até que o líder caia
                leader_deleted_event.wait()

            except Exception as e:
                logging.error(f"({self.node_address}) Erro no ciclo de eleição: {e}. A reiniciar o processo...")
                time.sleep(5)


    def register_node(self):
        """Regista este nó no caminho dos nós ativos."""
        path = f"{self.nodes_path}/{self.node_address}"
        try:
            self.zk.create(path, ephemeral=True)
            logging.info(f"({self.node_address}) Nó registado com sucesso no ZooKeeper.")
        except NodeExistsError:
            # Se já existir, pode ser de uma sessão anterior. Ignora.
            pass

    def get_leader_address(self):
        """Obtém o endereço do nó líder atual."""
        try:
            leader_data, _ = self.zk.get(self.leader_path)
            return leader_data.decode()
        except NoNodeError:
            return None
        except Exception:
            return None
            
    def get_active_node_addresses(self):
        """Retorna uma lista dos endereços de todos os nós ativos."""
        try:
            return self.zk.get_children(self.nodes_path)
        except NoNodeError:
            return []

    def is_connected(self):
        return self.zk.connected
