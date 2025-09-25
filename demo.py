import requests
import time
import json
import sys
import os
from datetime import datetime
import random
from colorama import init, Fore, Style
import docker  # <-- NOVA IMPORTAÇÃO

# Inicializar colorama para cores no terminal
init(autoreset=True)

class CartorioDigitalDemo:
    def __init__(self):
        self.nodes = ['http://localhost:5001', 'http://localhost:5002', 'http://localhost:5003']
        self.documentos_exemplo = [
            "Contrato de Aluguel - Imóvel na Rua das Flores, 123",
            "Escritura de Compra e Venda - Lote no Jardim Primavera",
            "Procuração Pública - Representação Legal",
            "Testamento Particular - Distribuição de Bens",
            "Declaração de União Estável - Reconhecimento de Sociedade de Fato",
            "Contrato Social - Constituição de Empresa",
            "Escritura de Doação - Bens Imóveis",
            "Registro de Marca - Propriedade Intelectual"
        ]
        self.cores = {
            'titulo': Fore.CYAN + Style.BRIGHT,
            'sucesso': Fore.GREEN + Style.BRIGHT,
            'erro': Fore.RED + Style.BRIGHT,
            'aviso': Fore.YELLOW + Style.BRIGHT,
            'info': Fore.BLUE + Style.BRIGHT,
            'destaque': Fore.MAGENTA + Style.BRIGHT
        }
        # --- NOVA LÓGICA: INICIAR CLIENTE DOCKER ---
        try:
            self.docker_client = docker.from_env()
        except docker.errors.DockerException:
            self.print_status("ERRO: Docker não está a correr ou não foi encontrado. A simulação de falha real será desativada.", "erro")
            self.docker_client = None
    
    def print_banner(self):
        """Imprime o banner inicial"""
        print(f"""
{self.cores['titulo']}╔{'═' * 80}╗
║{'🏛️  CARTÓRIO DIGITAL - DEMONSTRAÇÃO COMPLETA':^81}║
╠{'═' * 80}╣
║{'Sistema Distribuído - Projeto de Sistemas Distribuídos':^80}║
╚{'═' * 80}╝
{Style.RESET_ALL}""")
    
    def print_header(self, titulo, emoji="📋"):
        """Imprime um cabeçalho formatado"""
        print(f"\n{self.cores['titulo']}{emoji} {titulo}")
        print(f"{self.cores['titulo']}{'═' * (len(titulo) + 2)}{Style.RESET_ALL}")
    
    def print_status(self, mensagem, tipo="info"):
        """Imprime mensagem com cor"""
        cor = self.cores.get(tipo, self.cores['info'])
        print(f"{cor}{mensagem}{Style.RESET_ALL}")
    
    def verificar_status_nos(self):
        """Verifica o status de todos os nós"""
        self.print_header("STATUS DOS NÓS DO SISTEMA", "🖥️")
        
        tabela = []
        for i, node_url in enumerate(self.nodes, 1):
            try:
                response = requests.get(f"{node_url}/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    lider = f"{self.cores['destaque']}👑 LÍDER" if data['is_leader'] else "⚪ Seguidor"
                    zk_status = f"{self.cores['sucesso']}✅ Conectado" if data['zookeeper_connected'] else f"{self.cores['erro']}❌ Desconectado"
                    blockchain = f"📦 {data['chain_length']} blocos"
                    tabela.append([f"Nó {i}", lider, blockchain, zk_status])
                else:
                    tabela.append([f"Nó {i}", f"{self.cores['erro']}❌ Erro HTTP", "", ""])
            except requests.exceptions.RequestException:
                tabela.append([f"Nó {i}", f"{self.cores['erro']}❌ Offline", "", ""])
        
        # Imprimir tabela formatada
        print(f"{'Nó':<10} {'Status':<25} {'Blockchain':<20} {'ZooKeeper':<25}")
        print("-" * 80)
        for linha in tabela:
            print(f"{linha[0]:<10} {linha[1]:<25} {linha[2]:<20} {linha[3]:<25}")
    
    def mostrar_blockchain(self, node_url=None):
        """Mostra a blockchain atual"""
        # Tenta encontrar um nó online para pedir a blockchain
        if node_url is None:
            for url in self.nodes:
                try:
                    requests.get(f"{url}/status", timeout=1)
                    node_url = url
                    break
                except requests.exceptions.RequestException:
                    continue
        
        if node_url is None:
            self.print_status("❌ Nenhum nó online para mostrar a blockchain.", "erro")
            return

        self.print_header("BLOCKCHAIN ATUAL", "🔗")
        try:
            response = requests.get(f"{node_url}/blockchain", timeout=5)
            if response.status_code == 200:
                blockchain = response.json()['chain']
                self.print_status(f"Total de blocos: {len(blockchain)}", "info")
                print()
                
                for block in blockchain:
                    print(f"{self.cores['destaque']}📦 BLOCO {block['index']}{Style.RESET_ALL}")
                    print(f"   Hash: {block['hash'][:20]}...")
                    print(f"   Timestamp: {datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   Dados: {str(block['data'])[:60]}{'...' if len(str(block['data'])) > 60 else ''}")
                    print(f"   {'─' * 60}")
            else:
                self.print_status(f"❌ Erro ao obter blockchain: {response.status_code}", "erro")
        except Exception as e:
            self.print_status(f"❌ Erro ao obter blockchain: {str(e)}", "erro")
    
    def registrar_documento(self, documento, tentativas=3):
        """Registra um documento no sistema"""
        self.print_status(f"📝 Registrando: {documento[:50]}...", "info")
        
        leader_node = None
        for tentativa in range(tentativas):
            for node_url in self.nodes:
                try:
                    response = requests.get(f"{node_url}/status", timeout=2)
                    if response.status_code == 200 and response.json()['is_leader']:
                        leader_node = node_url
                        break
                except requests.exceptions.RequestException:
                    continue
            if leader_node:
                break
            else:
                if tentativa < tentativas - 1:
                    self.print_status(f"⏳ Aguardando líder... (tentativa {tentativa + 1}/{tentativas})", "aviso")
                    time.sleep(2)
        
        if leader_node:
            try:
                response = requests.post(
                    f"{leader_node}/register",
                    json={"document": documento},
                    timeout=10
                )
                if response.status_code == 201:
                    block_data = response.json()['block']
                    self.print_status("✅ Documento registrado com sucesso!", "sucesso")
                    self.print_status(f"   📦 Bloco: {block_data['index']} | Hash: {block_data['hash'][:16]}...", "info")
                    self.print_status(f"   🏛️  Processado por: Nó {leader_node.replace('http://', '')}", "destaque")
                    return True
                else:
                    self.print_status(f"❌ Erro ao registrar: {response.json().get('error', response.status_code)}", "erro")
                    return False
            except Exception as e:
                self.print_status(f"❌ Erro na requisição: {str(e)}", "erro")
                return False
        else:
            self.print_status("❌ Nenhum líder encontrado após todas as tentativas!", "erro")
            return False

    # --- FUNÇÃO DE SIMULAÇÃO DE FALHA ATUALIZADA ---
    def simular_falha_lider(self):
        """Simula a falha REAL do líder e pergunta ao utilizador se quer reiniciá-lo."""
        self.print_header("SIMULAÇÃO DE FALHA DO LÍDER", "🚨")
        
        if not self.docker_client:
            self.print_status("Simulação de falha real desativada. Docker não está disponível.", "erro")
            self.print_status("Apenas a fazer uma pausa de 5s.", "aviso")
            time.sleep(5)
            self.verificar_status_nos()
            return

        # 1. Identificar o líder atual
        leader_id = None
        for i, node_url in enumerate(self.nodes, 1):
            try:
                response = requests.get(f"{node_url}/status", timeout=2)
                if response.status_code == 200 and response.json()['is_leader']:
                    leader_id = i
                    break
            except requests.exceptions.RequestException:
                continue

        if not leader_id:
            self.print_status("❌ Não foi possível identificar o líder atual para simular a falha.", "erro")
            return

        self.print_status(f"👑 Líder atual identificado: Nó {leader_id}", "info")
        
        # 2. Parar o contentor do líder
        leader_container_name = f"cartorio-digital-node{leader_id}-1"
        try:
            self.print_status(f"🚨 A parar o contentor Docker '{leader_container_name}' para simular uma falha...", "aviso")
            leader_container = self.docker_client.containers.get(leader_container_name)
            leader_container.stop()
            self.print_status(f"🛑 Contentor '{leader_container_name}' parado.", "sucesso")
        except Exception as e:
            self.print_status(f"❌ Falha ao parar o contentor '{leader_container_name}': {e}", "erro")
            return

        # 3. Aguardar nova eleição
        self.print_status("⏳ A aguardar 10 segundos para a eleição de um novo líder...", "aviso")
        time.sleep(10)

        # 4. Verificar o novo estado do sistema
        self.print_status("📊 A verificar o estado do sistema após a falha:", "destaque")
        self.verificar_status_nos()

        # 5. Tentar registar um documento com o novo líder
        self.print_status("\n📝 A tentar registar um documento de emergência com o novo líder:", "info")
        self.registrar_documento("DOCUMENTO DE EMERGÊNCIA - Registro após falha do líder")
        
        # 6. Perguntar ao utilizador se quer reiniciar o nó que falhou
        resposta = input(f"\n{self.cores['aviso']}Deseja que o Nó {leader_id} (antigo líder) volte a funcionar? (s/n): {Style.RESET_ALL}").lower()

        if resposta in ['s', 'sim']:
            try:
                self.print_status(f"\n🔄 A reiniciar o Nó {leader_id}...", "info")
                leader_container.start()
                self.print_status("⏳ A aguardar 5 segundos para o nó se juntar ao cluster como seguidor...", "aviso")
                time.sleep(5)
                self.print_status(f"✅ Nó {leader_id} reiniciado com sucesso.", "sucesso")
            except Exception as e:
                self.print_status(f"❌ Falha ao reiniciar o contentor '{leader_container_name}': {e}", "erro")
        else:
            self.print_status(f"\nℹ️ O Nó {leader_id} permanecerá offline.", "info")
        
        # 7. Apresentar o estado final após a decisão
        self.print_status("\n📊 Estado final do sistema após a simulação de falha:", "destaque")
        self.verificar_status_nos()

    def verificar_consistencia(self):
        """Verifica a consistência da blockchain em todos os nós"""
        self.print_header("VERIFICAÇÃO DE CONSISTÊNCIA", "🔍")
        
        blockchains = {}
        self.print_status("🔍 Verificando blockchain em todos os nós:", "info")
        
        nodes_online = 0
        for i, node_url in enumerate(self.nodes, 1):
            try:
                response = requests.get(f"{node_url}/blockchain", timeout=5)
                if response.status_code == 200:
                    nodes_online += 1
                    blockchain = response.json()['chain']
                    blockchains[f'Nó {i}'] = {
                        'length': len(blockchain),
                        'last_hash': blockchain[-1]['hash'] if blockchain else None,
                    }
                    self.print_status(f"   ✅ Nó {i}: {len(blockchain)} blocos", "sucesso")
                else:
                    self.print_status(f"   ❌ Nó {i}: Erro ao obter blockchain", "erro")
            except requests.exceptions.RequestException:
                 self.print_status(f"   ❌ Nó {i}: Não disponível", "erro")
        
        # Verificar consistência
        self.print_status("\n📊 Análise de consistência:", "destaque")
        if nodes_online > 1:
            # Pegar os dados apenas dos nós que responderam
            online_data = blockchains.values()
            lengths = {data['length'] for data in online_data}
            hashes = {data['last_hash'] for data in online_data}
            
            if len(lengths) == 1:
                self.print_status("   ✅ Todos os nós ONLINE têm a mesma quantidade de blocos", "sucesso")
            else:
                self.print_status("   ⚠️ Nós ONLINE têm quantidades diferentes de blocos!", "aviso")
            
            if len(hashes) == 1:
                self.print_status("   ✅ Todos os nós ONLINE têm o mesmo hash do último bloco", "sucesso")
            else:
                self.print_status("   ⚠️ Nós ONLINE têm hashes diferentes no último bloco! INCONSISTÊNCIA!", "erro")
        else:
            self.print_status("   ℹ️ Não é possível verificar a consistência com menos de dois nós online.", "info")

    def executar_demo_interativa(self):
        """Executa demonstração interativa com pausas"""
        self.print_banner()
        
        input(f"\n{self.cores['aviso']}Pressione ENTER para verificar o estado inicial do sistema...{Style.RESET_ALL}")
        self.verificar_status_nos()
        
        input(f"\n{self.cores['aviso']}Pressione ENTER para ver a blockchain inicial...{Style.RESET_ALL}")
        self.mostrar_blockchain()
        
        self.print_header("REGISTRANDO DOCUMENTOS DE EXEMPLO", "📝")
        for i, documento in enumerate(self.documentos_exemplo, 1):
            input(f"\n{self.cores['aviso']}Pressione ENTER para registrar o documento {i}/{len(self.documentos_exemplo)}...{Style.RESET_ALL}")
            self.registrar_documento(documento)
            time.sleep(1)
        
        input(f"\n{self.cores['aviso']}Pressione ENTER para verificar a consistência dos dados...{Style.RESET_ALL}")
        self.verificar_consistencia()
        
        input(f"\n{self.cores['aviso']}Pressione ENTER para ver a blockchain final após registros...{Style.RESET_ALL}")
        self.mostrar_blockchain()
        
        input(f"\n{self.cores['aviso']}Pressione ENTER para simular uma falha REAL do líder...{Style.RESET_ALL}")
        self.simular_falha_lider()
        
        input(f"\n{self.cores['aviso']}Pressione ENTER para verificar a consistência final...{Style.RESET_ALL}")
        self.verificar_consistencia()

        self.print_header("DEMONSTRAÇÃO CONCLUÍDA! 🎉", "🎉")
        print(f"\n{self.cores['sucesso']}Todos os conceitos foram demonstrados com sucesso!{Style.RESET_ALL}")

if __name__ == "__main__":
    demo = CartorioDigitalDemo()
    demo.executar_demo_interativa()

