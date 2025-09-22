from flask import Flask, request, jsonify
from blockchain import Blockchain
from zk_utils import ZooKeeperCoordinator
import threading
import requests
import os
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
blockchain = Blockchain()
zk_coordinator = ZooKeeperCoordinator()

@app.route('/register', methods=['POST'])
def register_document():
    if not zk_coordinator.is_leader:
        return jsonify({"error": "Apenas o líder pode registrar documentos"}), 403
    
    data = request.json.get("document")
    if not data:
        return jsonify({"error": "Documento não fornecido"}), 400
    
    block = blockchain.add_block(data)
    
    # Replicar para outros nós em background
    threading.Thread(
        target=replicate_block, 
        args=(block,),
        daemon=True
    ).start()
    
    return jsonify({
        "status": "success",
        "block": {
            "index": block.index,
            "hash": block.hash,
            "timestamp": block.timestamp
        }
    }), 201

def replicate_block(block):
    """Replica o bloco para outros nós ativos"""
    time.sleep(0.5)  # Pequeno delay para evitar race conditions
    
    nodes = zk_coordinator.get_active_nodes()
    current_node = f"node_{os.environ.get('NODE_ID', 1)}"
    
    for node in nodes:
        if node != current_node:
            try:
                response = requests.post(
                    f"http://{node}:5000/sync",
                    json={"block": block.__dict__},
                    timeout=3
                )
                if response.status_code == 200:
                    print(f"✅ Bloco replicado para {node}")
                else:
                    print(f"⚠️ Falha ao replicar para {node}: {response.status_code}")
            except Exception as e:
                print(f"❌ Erro ao replicar para {node}: {e}")

@app.route('/sync', methods=['POST'])
def sync_block():
    """Endpoint para receber blocos replicados"""
    block_data = request.json.get("block")
    if not block_data:
        return jsonify({"error": "Dados do bloco não fornecidos"}), 400
    
    from blockchain import Block
    blockchain.chain.append(Block(**block_data))
    return jsonify({"status": "synced"}), 200

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    """Retorna a blockchain completa"""
    return jsonify([{
        "index": block.index,
        "hash": block.hash,
        "timestamp": block.timestamp,
        "data": block.data
    } for block in blockchain.chain])

@app.route('/status', methods=['GET'])
def status():
    """Retorna o status do nó"""
    return jsonify({
        "node_id": os.environ.get("NODE_ID", 1),
        "is_leader": zk_coordinator.is_leader,
        "chain_length": len(blockchain.chain),
        "zookeeper_connected": zk_coordinator.zk.connected
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check para o nó"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    NODE_ID = int(os.environ.get("NODE_ID", 1))
    
    print(f"🚀 Iniciando nó {NODE_ID}...")
    
    # Iniciar eleição em thread separada
    election_thread = threading.Thread(
        target=zk_coordinator.start_election,
        args=(NODE_ID,)
    )
    election_thread.daemon = True
    election_thread.start()
    
    # Esperar ZooKeeper estar pronto
    time.sleep(3)
    
    # Registrar nó no ZooKeeper
    zk_coordinator.register_node(NODE_ID)
    
    print(f"✅ Nó {NODE_ID} pronto e aguardando requisições")
    app.run(host="0.0.0.0", port=5000)