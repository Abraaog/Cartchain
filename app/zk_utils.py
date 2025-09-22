from kazoo.client import KazooClient
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

class ZooKeeperCoordinator:
    def __init__(self, hosts="zoo1:2181,zoo2:2181,zoo3:2181"):
        # Removido connection_retry_delay que não é suportado no kazoo 2.8.0
        self.zk = KazooClient(hosts=hosts)
        self.zk.start(timeout=10)
        self.is_leader = False
        self.leader_path = "/cartorio/leader"
        self.node_id = None
        
        # Garantir que os caminhos existam
        self.zk.ensure_path("/cartorio")
        self.zk.ensure_path("/cartorio/nodes")
        self.zk.ensure_path("/cartorio/eleicao")

    def start_election(self, node_id):
        """Implementação manual de eleição de líder"""
        self.node_id = node_id
        
        def watch_leader(data):
            """Watch para mudanças no líder"""
            try:
                if data is None:
                    # Líder desapareceu, iniciar nova eleição
                    print(f"⚠️ Líder desapareceu, iniciando nova eleição")
                    self.elect_leader()
            except Exception as e:
                print(f"⚠️ Erro no watch do líder: {e}")

        def elect_leader():
            """Tenta se tornar líder"""
            try:
                # Tenta criar o nó do líder (ephemeral)
                self.zk.create(self.leader_path, str(node_id).encode(), ephemeral=True)
                self.is_leader = True
                print(f"🚀 Nó {node_id} tornou-se líder")
                return True
            except Exception as e:
                # Já existe um líder
                self.is_leader = False
                # Obter quem é o líder atual
                try:
                    leader_id, stat = self.zk.get(self.leader_path, watch=watch_leader)
                    print(f"📋 Nó {node_id} reconhece líder: {leader_id.decode()}")
                except Exception as e2:
                    print(f"⚠️ Nó {node_id} não conseguiu identificar o líder: {e2}")
                return False

        # Iniciar eleição
        elect_leader()

    def register_node(self, node_id):
        try:
            self.zk.create(f"/cartorio/nodes/node_{node_id}", ephemeral=True)
            print(f"✅ Nó {node_id} registrado no ZooKeeper")
        except Exception as e:
            print(f"❌ Erro ao registrar nó {node_id}: {e}")

    def get_active_nodes(self):
        try:
            return self.zk.get_children("/cartorio/nodes")
        except Exception as e:
            print(f"⚠️ Erro ao obter nós ativos: {e}")
            return []