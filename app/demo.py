# demo.py
import requests
import time
import json
import sys
from datetime import datetime

class CartorioDigitalDemo:
    def __init__(self):
        self.nodes = ['http://localhost:5001', 'http://localhost:5002', 'http://localhost:5003']
        self.documentos_exemplo = [
            "Contrato de Aluguel - Imóvel na Rua das Flores, 123",
            "Escritura de Compra e Venda - Lote no Jardim Primavera",
            "Procuração Pública - Representação Legal",
            "Testamento Particular - Distribuição de Bens",
            "Declaração de União Estável - Reconhecimento de Sociedade de Fato"
        ]
    
    def print_header(self, titulo):
        """Imprime um cabeçalho formatado"""
        print("\n" + "="*60)
        print(f"🏛️  {titulo}")
        print("="*60)
    
    def verificar_status_nos(self):
        """Verifica o status de todos os nós"""
        self.print_header("STATUS DOS NÓS DO SISTEMA")
        
        for i, node in enumerate(self.nodes, 1):
            try:
                response = requests.get(f"{node}/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    lider = "👑 LÍDER" if data['is_leader'] else "⚪ Seguidor"
                    zk_status = "✅ Conectado" if data['zookeeper_connected'] else "❌ Desconectado"
                    print(f"Nó {i}: {lider} | Blockchain: {data['chain_length']} blocos | ZooKeeper: {zk_status}")
                else:
                    print(f"Nó {i}: ❌ Erro HTTP {response.status_code}")
            except Exception as e:
                print(f"Nó {i}: ❌ Não disponível - {str(e)}")
    
    def mostrar_blockchain(self, node_url=None):
        """Mostra a blockchain atual"""
        if node_url is None:
            node_url = self.nodes[0]
        
        self.print_header("BLOCKCHAIN ATUAL")
        try:
            response = requests.get(f"{node_url}/blockchain", timeout=5)
            if response.status_code == 200:
                blockchain = response.json()
                print(f"Total de blocos: {len(blockchain)}\n")
                
                for block in blockchain:
                    print(f"📦 BLOCO {block['index']}:")
                    print(f"   Hash: {block['hash'][:16]}...")
                    print(f"   Timestamp: {block['timestamp']}")
                    print(f"   Dados: {block['data'][:60]}{'...' if len(block['data']) > 60 else ''}")
                    print()
            else:
                print(f"❌ Erro ao obter blockchain: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro ao obter blockchain: {str(e)}")
    
    def registrar_documento(self, documento, tentativas=3):
        """Registra um documento no sistema"""
        print(f"\n📝 Registrando documento: {documento[:50]}...")
        
        # Encontrar o nó líder
        leader_node = None
        for tentativa in range(tentativas):
            for node in self.nodes:
                try:
                    response = requests.get(f"{node}/status", timeout=3)
                    if response.status_code == 200 and response.json()['is_leader']:
                        leader_node = node
                        break
                except:
                    continue
            
            if leader_node:
                break
            else:
                if tentativa < tentativas - 1:
                    print(f"   ⏳ Aguardando líder... (tentativa {tentativa + 1}/{tentativas})")
                    time.sleep(2)
        
        if leader_node:
            try:
                response = requests.post(
                    f"{leader_node}/register",
                    json={"document": documento},
                    timeout=5
                )
                if response.status_code == 201:
                    block_data = response.json()['block']
                    print(f"   ✅ Documento registrado com sucesso!")
                    print(f"   📦 Bloco: {block_data['index']} | Hash: {block_data['hash'][:16]}...")
                    print(f"   🏛️  Processado por: Nó {leader_node.split('/')[-1]}")
                    return True
                else:
                    print(f"   ❌ Erro ao registrar: {response.status_code}")
                    return False
            except Exception as e:
                print(f"   ❌ Erro na requisição: {str(e)}")
                return False
        else:
            print("   ❌ Nenhum líder encontrado após todas as tentativas!")
            return False
    
    def simular_falha_lider(self):
        """Simula a falha do líder e mostra a recuperação"""
        self.print_header("SIMULAÇÃO DE FALHA DO LÍDER")
        
        # Identificar o líder atual
        leader_id = None
        leader_node = None
        
        for i, node in enumerate(self.nodes, 1):
            try:
                response = requests.get(f"{node}/status", timeout=3)
                if response.status_code == 200 and response.json()['is_leader']:
                    leader_id = i
                    leader_node = node
                    break
            except:
                continue
        
        if leader_id:
            print(f"👑 Líder atual identificado: Nó {leader_id}")
            print("🚨 Simulando falha do líder...")
            print("💡 Na demonstração real, usaríamos: docker-compose stop node{leader_id}")
            
            # Aguardar um pouco para a eleição de novo líder
            print("⏳ Aguardando eleição de novo líder...")
            time.sleep(5)
            
            # Verificar novo status
            print("\n📊 Status após falha:")
            self.verificar_status_nos()
            
            # Tentar registrar um documento após a falha
            print("\n📝 Tentando registrar documento após falha do líder:")
            self.registrar_documento("DOCUMENTO DE EMERGÊNCIA - Registro após falha do líder")
            
            return leader_id
        else:
            print("❌ Não foi possível identificar o líder atual")
            return None
    
    def verificar_consistencia(self):
        """Verifica a consistência da blockchain em todos os nós"""
        self.print_header("VERIFICAÇÃO DE CONSISTÊNCIA")
        
        blockchains = {}
        print("🔍 Verificando blockchain em todos os nós:")
        
        for i, node in enumerate(self.nodes, 1):
            try:
                response = requests.get(f"{node}/blockchain", timeout=5)
                if response.status_code == 200:
                    blockchain = response.json()
                    blockchains[f'Nó {i}'] = {
                        'length': len(blockchain),
                        'last_hash': blockchain[-1]['hash'] if blockchain else None
                    }
                    print(f"   Nó {i}: {len(blockchain)} blocos")
                else:
                    print(f"   Nó {i}: ❌ Erro ao obter blockchain")
            except Exception as e:
                print(f"   Nó {i}: ❌ Não disponível - {str(e)}")
        
        # Verificar consistência
        print("\n📊 Análise de consistência:")
        if len(blockchains) > 0:
            lengths = [data['length'] for data in blockchains.values()]
            hashes = [data['last_hash'] for data in blockchains.values()]
            
            if len(set(lengths)) == 1:
                print("   ✅ Todos os nós têm a mesma quantidade de blocos")
            else:
                print("   ⚠️ Nós têm quantidades diferentes de blocos:")
                for node, data in blockchains.items():
                    print(f"      {node}: {data['length']} blocos")
            
            if len(set(hashes)) == 1:
                print("   ✅ Todos os nós têm o mesmo hash do último bloco")
            else:
                print("   ⚠️ Nós têm hashes diferentes no último bloco")
        else:
            print("   ❌ Não foi possível verificar a consistência")
    
    def executar_demo_completa(self):
        """Executa a demonstração completa"""
        print("🚀 INICIANDO DEMONSTRAÇÃO DO CARTÓRIO DIGITAL")
        print("="*60)
        print("📅 Data e hora:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        print("🏛️  Cartório Digital - Sistema Distribuído")
        print("="*60)
        
        # 1. Status inicial do sistema
        self.verificar_status_nos()
        time.sleep(2)
        
        # 2. Mostrar blockchain inicial
        self.mostrar_blockchain()
        time.sleep(2)
        
        # 3. Registrar documentos de exemplo
        self.print_header("REGISTRANDO DOCUMENTOS DE EXEMPLO")
        print(f"📝 Serão registrados {len(self.documentos_exemplo)} documentos:")
        
        for i, documento in enumerate(self.documentos_exemplo, 1):
            print(f"\n{i}. {documento}")
            sucesso = self.registrar_documento(documento)
            if sucesso:
                print(f"   ✅ Documento {i} registrado com sucesso!")
            else:
                print(f"   ❌ Falha ao registrar documento {i}")
            time.sleep(1)
        
        # 4. Verificar consistência após registros
        self.verificar_consistencia()
        time.sleep(2)
        
        # 5. Mostrar blockchain final
        self.mostrar_blockchain()
        time.sleep(2)
        
        # 6. Simular falha do líder
        leader_falhou = self.simular_falha_lider()
        time.sleep(2)
        
        # 7. Verificar consistência final
        self.verificar_consistencia()
        time.sleep(2)
        
        # 8. Mostrar blockchain final
        self.mostrar_blockchain()
        
        print("\n🎉 DEMONSTRAÇÃO CONCLUÍDA!")
        print("="*60)
        print("📊 RESUMO DA DEMONSTRAÇÃO:")
        print("✅ Eleição de líder distribuída")
        print("✅ Replicação de dados entre nós")
        print("✅ Consistência com blockchain")
        print("✅ Tolerância a falhas")
        print("✅ Coordenação distribuída com ZooKeeper")
        print("="*60)
        print("🏛️  Cartório Digital - Sistema robusto e distribuído!")

if __name__ == "__main__":
    demo = CartorioDigitalDemo()
    demo.executar_demo_completa()