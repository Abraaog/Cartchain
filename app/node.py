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

# Iniciar componentes principais
blockchain = Blockchain()
zk_coordinator = ZooKeeperCoordinator(NODE_ADDRESS)

def synchronize_blockchain_on_startup():
    """
    Função crucial executada no arranque para sincronizar a blockchain com a rede.
    Um nó que (re)inicia precisa de "apanhar" o trabalho que perdeu.
    """
    logging.info("--- INICIANDO PROCESSO DE SINCRONIZAÇÃO DA BLOCKCHAIN ---")
    # Pequena pausa para permitir que outros nós se registem no ZK
    time.sleep(5) 

    my_address = NODE_ADDRESS
    other_nodes = [addr for addr in zk_coordinator.get_active_node_addresses() if addr != my_address]

    if not other_nodes:
        logging.info("Nenhum outro nó encontrado. A iniciar com a blockchain gênese.")
        return

    logging.info(f"Nós ativos encontrados para sincronização: {other_nodes}")
    longest_chain = None
    best_node = None

    # Encontrar a blockchain mais longa entre todos os nós ativos
    for address in other_nodes:
        try:
            logging.info(f"A pedir blockchain do nó {address}...")
            response = requests.get(f"http://{address}/blockchain", timeout=5)
            if response.status_code == 200:
                data = response.json()
                chain_dicts = data['chain']
                if longest_chain is None or len(chain_dicts) > len(longest_chain):
                    longest_chain = chain_dicts
                    best_node = address
                    logging.info(f"Nova blockchain mais longa encontrada em {address} com {len(longest_chain)} blocos.")
            else:
                logging.warning(f"Resposta inválida de {address}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Não foi possível obter a blockchain de {address}: {e}")

    # Se uma cadeia mais longa foi encontrada, tenta substituir a local
    if longest_chain:
        logging.info(f"A tentar substituir a cadeia local pela do nó {best_node}.")
        success, reason = blockchain.replace_chain(longest_chain)
        if not success:
            logging.error(f"Falha ao substituir a cadeia! Razão: {reason}. A continuar com a blockchain local.")
    else:
        logging.warning("Não foi possível sincronizar com nenhum nó. A continuar com a blockchain local.")
    logging.info("--- PROCESSO DE SINCRONIZAÇÃO CONCLUÍDO ---")


@app.route('/register', methods=['POST'])
def register_document():
    if not zk_coordinator.is_leader:
        logging.warning(f"Tentativa de registo num nó não-líder ({NODE_ADDRESS}).")
        leader_address = zk_coordinator.get_leader_address()
        return jsonify({"error": "Apenas o líder pode registar documentos.", "leader_hint": leader_address or "Nenhum"}), 403

    data = request.json.get("document")
    if not data: return jsonify({"error": "Documento não fornecido"}), 400

    logging.info(f"👑 LÍDER: Recebido documento para registro: '{data[:50]}...'")
    block = blockchain.add_block(data)
    logging.info(f"📦 Bloco {block.index} criado com hash {block.hash[:16]}...")

    logging.info(f"🔄 Iniciando replicação do bloco {block.index}...")
    threading.Thread(target=replicate_block, args=(block,), daemon=True).start()
    
    return jsonify({"message": "Documento registado e replicação iniciada.", "block": block.to_dict()}), 201

def replicate_block(block):
    followers = [addr for addr in zk_coordinator.get_active_node_addresses() if addr != NODE_ADDRESS]
    if not followers: return

    logging.info(f"🔍 Seguidores ativos encontrados: {followers}")
    success_count = 0
    for address in followers:
        try:
            logging.info(f"  -> Replicando para http://{address}/sync...")
            response = requests.post(f"http://{address}/sync", json={"block": block.to_dict()}, timeout=5)
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
    block_data = request.json.get("block")
    if not block_data: return jsonify({"error": "Dados do bloco não fornecidos"}), 400
    
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
    return jsonify({"chain": [block.to_dict() for block in blockchain.chain]})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "node_address": NODE_ADDRESS,
        "is_leader": zk_coordinator.is_leader,
        "chain_length": len(blockchain.chain),
        "zookeeper_connected": zk_coordinator.is_connected()
    })

if __name__ == '__main__':
    threading.Thread(target=zk_coordinator.run_leader_election, daemon=True).start()
    
    # Espera que a ligação com o ZK esteja estabelecida antes de tentar sincronizar
    while not zk_coordinator.is_connected():
        time.sleep(1)

    # **NOVO PASSO CRUCIAL: Sincroniza a blockchain com a rede antes de arrancar o servidor web**
    synchronize_blockchain_on_startup()

    port = 5000
    logging.info(f"🚀 Nó {NODE_ADDRESS} pronto e a iniciar o servidor na porta {port}...")
    app.run(host="0.0.0.0", port=port)

