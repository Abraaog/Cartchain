from flask import Flask, request, jsonify
from blockchain import Blockchain, Block
from zk_utils import ZooKeeperCoordinator
import threading
import requests
import os
import time
import logging

# Configurar logging para um formato mais claro
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)

# Obter o endereço do nó a partir das variáveis de ambiente
NODE_ADDRESS = os.environ.get("NODE_ADDRESS", "localhost:5000")

# --- ESTA É A LINHA CORRIGIDA ---
# Iniciar componentes principais, passando NODE_ADDRESS como argumento posicional
blockchain = Blockchain()
zk_coordinator = ZooKeeperCoordinator(NODE_ADDRESS)

@app.route('/register', methods=['POST'])
def register_document():
    """Endpoint para um cliente registar um novo documento. Apenas o líder pode executar esta operação."""
    if not zk_coordinator.is_leader:
        logging.warning(f"Tentativa de registo num nó não-líder ({NODE_ADDRESS}).")
        leader_address = zk_coordinator.get_leader_address()
        if leader_address:
            return jsonify({"error": "Apenas o líder pode registar documentos.", "leader_hint": leader_address}), 403
        else:
            return jsonify({"error": "Apenas o líder pode registar documentos. Nenhum líder eleito no momento."}), 503

    data = request.json.get("document")
    if not data:
        return jsonify({"error": "Documento não fornecido"}), 400

    logging.info(f"👑 LÍDER: Recebido documento para registro: '{data[:50]}...'")
    
    # Adicionar bloco à sua própria blockchain
    block = blockchain.add_block(data)
    logging.info(f"📦 Bloco {block.index} criado com hash {block.hash[:16]}...")

    # Replicar para outros nós em segundo plano para não bloquear o cliente
    logging.info(f"🔄 Iniciando replicação do bloco {block.index}...")
    threading.Thread(
        target=replicate_block, 
        args=(block,),
        daemon=True
    ).start()
    
    return jsonify({
        "message": "Documento registado e replicação iniciada.",
        "block": block.to_dict()
    }), 201

def replicate_block(block):
    """Obtém os endereços dos seguidores do ZooKeeper e envia-lhes o novo bloco."""
    active_node_addresses = zk_coordinator.get_active_node_addresses()
    
    followers = [addr for addr in active_node_addresses if addr != NODE_ADDRESS]
    if not followers:
        logging.info("Nenhum seguidor ativo para replicar.")
        return

    logging.info(f"🔍 Seguidores ativos encontrados: {followers}")
    
    success_count = 0
    for address in followers:
        try:
            logging.info(f"  -> Replicando para http://{address}/sync...")
            response = requests.post(
                f"http://{address}/sync",
                json={"block": block.to_dict()},
                timeout=5
            )
            if response.status_code == 200:
                logging.info(f"   ✅ Bloco replicado com sucesso para {address}")
                success_count += 1
            else:
                logging.error(f"   ❌ Falha ao replicar para {address}: Status {response.status_code}, Resposta: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"   ❌ Erro de conexão ao replicar para {address}: {e}")
    
    logging.info(f"📊 Replicação concluída: {success_count}/{len(followers)} seguidores atualizados.")

@app.route('/sync', methods=['POST'])
def sync_block():
    """Endpoint para os seguidores receberem blocos replicados do líder."""
    block_data = request.json.get("block")
    if not block_data:
        return jsonify({"error": "Dados do bloco não fornecidos"}), 400
    
    try:
        new_block = Block.from_dict(block_data)
        success, reason = blockchain.add_replicated_block(new_block)
        
        if success:
            logging.info(f"✅ Bloco {new_block.index} recebido do líder e adicionado à blockchain.")
            return jsonify({"message": "Bloco sincronizado com sucesso."}), 200
        else:
            logging.warning(f"⚠️ Bloco {new_block.index} recebido do líder foi rejeitado ({reason}).")
            return jsonify({"error": "Bloco inválido ou fora de ordem"}), 409
            
    except Exception as e:
        logging.error(f"❌ Erro grave no endpoint /sync: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    """Retorna a blockchain completa, encapsulada num objeto JSON."""
    return jsonify({"chain": [block.to_dict() for block in blockchain.chain]})

@app.route('/status', methods=['GET'])
def status():
    """Retorna o status do nó: se é líder, o tamanho da cadeia e a conexão com o ZooKeeper."""
    return jsonify({
        "node_address": NODE_ADDRESS,
        "is_leader": zk_coordinator.is_leader,
        "chain_length": len(blockchain.chain),
        "zookeeper_connected": zk_coordinator.is_connected()
    })

if __name__ == '__main__':
    # Iniciar eleição em segundo plano
    threading.Thread(target=zk_coordinator.run_leader_election, daemon=True).start()
    
    # Iniciar o servidor Flask
    # A porta interna do contentor é sempre 5000, o mapeamento é feito no docker-compose
    port = 5000
    logging.info(f"🚀 Nó {NODE_ADDRESS} a iniciar na porta {port}...")
    app.run(host="0.0.0.0", port=port)

