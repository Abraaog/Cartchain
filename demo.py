import requests
import time
import json
import sys
import os
from datetime import datetime
import random
from colorama import init, Fore, Style
import docker

# Inicializar colorama para cores no terminal
init(autoreset=True)

class CartorioDigitalDemo:
    def __init__(self):
        self.nodes_ports = ['5001', '5002', '5003']
        self.nodes_urls = [f'http://localhost:{port}' for port in self.nodes_ports]
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
        try:
            self.docker_client = docker.from_env()
        except docker.errors.DockerException:
            self.print_status("🚨 Docker não está a correr. A simulação de falha real não irá funcionar.", "erro")
            self.docker_client = None

    def print_banner(self):
        """Imprime o banner inicial da demonstração."""
        print(f"\n{self.cores['titulo']}╔{'═' * 80}╗")
        print(f"║{'🏛️  CARTÓRIO DIGITAL - DEMONSTRAÇÃO COMPLETA':^88}║")
        print(f"╠{'═' * 80}╣")
        print(f"║{'Sistema Distribuído - Projeto de Sistemas Distribuídos':^86}║")
        print(f"╚{'═' * 80}╝\n")

    def print_header(self, titulo, emoji="📋"):
        """Imprime um cabeçalho formatado para secções da demo."""
        print(f"\n{self.cores['titulo']}{emoji} {titulo}")
        print(f"{self.cores['titulo']}{'═' * (len(titulo) + 3)}{Style.RESET_ALL}")

    def print_status(self, mensagem, tipo="info"):
        """Imprime uma mensagem de estado com a cor apropriada."""
        cor = self.cores.get(tipo, self.cores['info'])
        print(f"{cor}{mensagem}{Style.RESET_ALL}")

    def get_node_status(self):
        """Obtém o estado de todos os nós e identifica o líder."""
        all_status = []
        leader_url = None
        for i, node_url in enumerate(self.nodes_urls, 1):
            try:
                response = requests.get(f"{node_url}/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    status = "👑 LÍDER" if data.get('is_leader') else "⚪ Seguidor"
                    if data.get('is_leader'):
                        leader_url = node_url
                    all_status.append([f"Nó {i}", status, f"📦 {data.get('chain_length', '?')} blocos", "✅ Conectado"])
                else:
                    all_status.append([f"Nó {i}", "❌ Erro HTTP", "", ""])
            except requests.exceptions.RequestException:
                all_status.append([f"Nó {i}", "❌ Offline", "", ""])
        return all_status, leader_url

    def verificar_status_nos(self):
        """Verifica e imprime o estado de todos os nós numa tabela."""
        self.print_header("STATUS DOS NÓS DO SISTEMA", "🖥️")
        status_data, _ = self.get_node_status()
        
        print(f"{'Nó':<10}{'Status':<25}{'Blockchain':<25}{'ZooKeeper'}")
        print("-" * 80)
        for linha in status_data:
            print(f"{linha[0]:<10}{linha[1]:<25}{linha[2]:<25}{linha[3]}")

    def mostrar_blockchain(self):
        """Mostra a blockchain atual a partir de um nó ativo."""
        self.print_header("BLOCKCHAIN ATUAL", "🔗")
        node_url_to_check = self.nodes_urls[0] # Tenta o primeiro nó por defeito
        
        try:
            response = requests.get(f"{node_url_to_check}/blockchain", timeout=5)
            if response.status_code == 200:
                blockchain_data = response.json()
                chain = blockchain_data.get('chain', [])
                self.print_status(f"Total de blocos: {len(chain)}", "info")
                
                for block in chain:
                    print(f"\n{self.cores['destaque']}📦 BLOCO {block.get('index')}{Style.RESET_ALL}")
                    print(f"   Hash: {block.get('hash', 'N/A')[:20]}...")
                    try:
                        ts_obj = datetime.fromisoformat(block.get('timestamp'))
                        ts_formatted = ts_obj.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"   Timestamp: {ts_formatted}")
                    except (TypeError, ValueError):
                        print(f"   Timestamp: {block.get('timestamp', 'N/A')}")
                    print(f"   Dados: {block.get('data', '')[:60]}")
                    print(f"   {'─' * 60}")
            else:
                self.print_status(f"❌ Erro ao obter blockchain: {response.status_code}", "erro")
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Erro de conexão ao obter blockchain: {e}", "erro")
        except Exception as e:
            self.print_status(f"❌ Erro ao processar blockchain: {e}", "erro")

    def registrar_documento(self, documento):
        """Registra um novo documento no sistema, enviando-o para o líder."""
        self.print_status(f"📝 Registrando: {documento[:50]}...", "info")
        _, leader_url = self.get_node_status()

        if not leader_url:
            self.print_status("❌ Nenhum líder encontrado para registar o documento!", "erro")
            return False

        try:
            response = requests.post(f"{leader_url}/register", json={"document": documento}, timeout=10)
            if response.status_code == 201:
                block_data = response.json().get('block', {})
                self.print_status("✅ Documento registrado com sucesso!", "sucesso")
                print(f"   📦 Bloco: {block_data.get('index')} | Hash: {block_data.get('hash', '')[:16]}...")
                print(f"   🏛️  Processado por: Nó {leader_url}")
                return True
            else:
                self.print_status(f"❌ Erro ao registrar: {response.status_code} - {response.text}", "erro")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Erro de conexão ao registrar: {str(e)}", "erro")
            return False

    def simular_falha_lider(self):
        """Simula uma falha real parando o contentor Docker do líder."""
        self.print_header("SIMULAÇÃO DE FALHA DO LÍDER", "🚨")
        if not self.docker_client:
            self.print_status("A simulação de falha não pode continuar sem o Docker a correr.", "erro")
            return

        _, leader_url = self.get_node_status()
        if not leader_url:
            self.print_status("Não foi possível identificar o líder para simular a falha.", "erro")
            return

        leader_port = leader_url.split(':')[-1]
        leader_node_num = self.nodes_ports.index(leader_port) + 1
        container_name = f"cartorio-digital-node{leader_node_num}-1"

        try:
            container = self.docker_client.containers.get(container_name)
            self.print_status(f"👑 Líder atual identificado: Nó {leader_node_num}", "info")
            self.print_status(f"🚨 A parar o contentor Docker '{container.name}' para simular uma falha...", "aviso")
            container.stop()
            self.print_status(f"🛑 Contentor '{container.name}' parado.", "sucesso")
            
            self.print_status("\n⏳ A aguardar 10 segundos para a eleição de um novo líder...", "aviso")
            time.sleep(10)

            self.print_status("\n📊 A verificar o estado do sistema após a falha:", "destaque")
            self.verificar_status_nos()

            self.print_header("A tentar registar um documento de emergência com o novo líder:", "📝")
            self.registrar_documento("DOCUMENTO DE EMERGÊNCIA - Registro após falha do líder")

            # Opção para reiniciar o nó
            escolha = input(f"\n{self.cores['aviso']}Deseja que o Nó {leader_node_num} (antigo líder) volte a funcionar? (s/n): {Style.RESET_ALL}").lower()
            if escolha == 's':
                self.print_status(f"\n🔄 A reiniciar o Nó {leader_node_num}...", "info")
                container.start()
                # CORREÇÃO: Aumentar o tempo de espera para garantir que o nó está totalmente online
                self.print_status("⏳ A aguardar 12 segundos para o nó arrancar, sincronizar a blockchain e ficar online...", "aviso")
                time.sleep(12)
                self.print_status(f"✅ Nó {leader_node_num} reiniciado com sucesso.", "sucesso")
            else:
                self.print_status(f"\nℹ️ O Nó {leader_node_num} permanecerá offline.", "info")
            
            self.print_status("\n📊 Estado final do sistema após a simulação de falha:", "destaque")
            self.verificar_status_nos()

        except docker.errors.NotFound:
            self.print_status(f"Erro: Contentor Docker '{container_name}' não encontrado.", "erro")
        except Exception as e:
            self.print_status(f"Ocorreu um erro durante a simulação de falha: {e}", "erro")

    def verificar_consistencia(self):
        """Verifica a consistência da blockchain em todos os nós online."""
        self.print_header("VERIFICAÇÃO DE CONSISTÊNCIA", "🔍")
        self.print_status("🔍 Verificando blockchain em todos os nós:", "info")
        
        blockchains = {}
        for i, node_url in enumerate(self.nodes_urls, 1):
            try:
                response = requests.get(f"{node_url}/blockchain", timeout=5)
                if response.status_code == 200:
                    chain = response.json().get('chain', [])
                    blockchains[f'Nó {i}'] = {
                        'length': len(chain),
                        'last_hash': chain[-1]['hash'] if chain else None,
                    }
                    self.print_status(f"   ✅ Nó {i}: {len(chain)} blocos", "sucesso")
                else:
                    self.print_status(f"   ❌ Nó {i}: Erro HTTP {response.status_code}", "erro")
            except requests.exceptions.RequestException:
                self.print_status(f"   ❌ Nó {i}: Não disponível", "erro")

        online_nodes_data = list(blockchains.values())
        self.print_status("\n📊 Análise de consistência:", "destaque")
        if len(online_nodes_data) > 1:
            lengths = {data['length'] for data in online_nodes_data}
            hashes = {data['last_hash'] for data in online_nodes_data}
            
            if len(lengths) == 1:
                self.print_status("   ✅ Todos os nós ONLINE têm a mesma quantidade de blocos", "sucesso")
            else:
                self.print_status("   ⚠️ Nós ONLINE têm quantidades diferentes de blocos!", "aviso")

            if len(hashes) == 1 and all(h is not None for h in hashes):
                self.print_status("   ✅ Todos os nós ONLINE têm o mesmo hash do último bloco", "sucesso")
            else:
                self.print_status("   ⚠️ Nós ONLINE têm hashes diferentes no último bloco! INCONSISTÊNCIA!", "aviso")
        else:
            self.print_status("   ℹ️ Menos de dois nós online para comparar.", "info")

    def executar_demo_interativa(self):
        """Executa a demonstração completa passo a passo."""
        self.print_banner()
        
        input("Pressione ENTER para verificar o estado inicial do sistema...")
        self.verificar_status_nos()
        
        input("\nPressione ENTER para ver a blockchain inicial...")
        self.mostrar_blockchain()
        
        self.print_header("REGISTRANDO DOCUMENTOS DE EXEMPLO")
        for i, doc in enumerate(self.documentos_exemplo, 1):
            input(f"\nPressione ENTER para registrar o documento {i}/{len(self.documentos_exemplo)}...")
            self.registrar_documento(doc)
            time.sleep(1)
        
        input("\nPressione ENTER para verificar a consistência dos dados...")
        self.verificar_consistencia()
        
        input("\nPressione ENTER para ver a blockchain final após registros...")
        self.mostrar_blockchain()
        
        input("\nPressione ENTER para simular uma falha REAL do líder...")
        self.simular_falha_lider()

        input("\nPressione ENTER para verificar a consistência final...")
        self.verificar_consistencia()

        self.print_header("DEMONSTRAÇÃO CONCLUÍDA! 🎉", "🎉")
        print("\nTodos os conceitos foram demonstrados com sucesso!")

if __name__ == "__main__":
    demo = CartorioDigitalDemo()
    demo.executar_demo_interativa()

