import socket
import threading
import pickle
import time
import sys

# --- CONFIGURAÇÕES ---
if len(sys.argv) < 3:
    print("USO: python servidor.py <MINHA_PORTA> <PORTA_DO_PARCEIRO> <TIPO_INICIAL>")
    sys.exit()

MINHA_PORTA = int(sys.argv[1])
PORTA_PARCEIRO = int(sys.argv[2])
TIPO_ATUAL = sys.argv[3] 
HOST = '0.0.0.0'

# --- ESTADO GLOBAL ---
estado = {
    'jogadores': {},
    'bandeira': {'x': 300, 'y': 300, 'dono': None},
    'clock': 0 
}
lock = threading.Lock()
socket_replicacao = None 

# --- REPLICAÇÃO ---
def conectar_ao_backup():
    global socket_replicacao
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', PORTA_PARCEIRO))
            socket_replicacao = s
            print(f"[REPLICAÇÃO] Conectado ao Backup na porta {PORTA_PARCEIRO}")
            break
        except: time.sleep(2)

def replicar_estado():
    global socket_replicacao
    if socket_replicacao and TIPO_ATUAL == "PRIMARY":
        try:
            msg = pickle.dumps(estado)
            socket_replicacao.send(msg)
        except:
            print("[REPLICAÇÃO] Falha ao enviar para backup")
            socket_replicacao = None

# --- LÓGICA DO JOGO ---
def gerenciar_cliente(conn, addr):
    global estado
    if TIPO_ATUAL == "BACKUP": conn.close(); return

    print(f"[CONEXÃO] Nova conexão de {addr}")
    conn.settimeout(5.0) 
    
    # Variável para saber qual ID esse socket está controlando
    meu_pid = None 

    while True:
        try:
            data = conn.recv(4096)
            if not data: break
            msg = pickle.loads(data)
            
            # PEGA O ID QUE O CLIENTE MANDOU (UUID)
            pid = msg['id']
            meu_pid = pid # Vincula esse socket a este Player ID

            # --- ALGORITMO DE CRISTIAN: Sincronização de Relógio Físico ---
            if msg['acao'] == 'SYNC_TIME':
                resposta = {
                    'acao': 'SYNC_TIME_RESPONSE',
                    'server_time': time.time()
                }
                conn.send(pickle.dumps(resposta))
                print(f"[CRISTIAN] Enviando tempo para {pid[:4]}: {resposta['server_time']:.3f}")
                continue

            with lock:
                # SE É A PRIMEIRA VEZ QUE VEMOS ESSE ID, CRIAMOS
                if pid not in estado['jogadores']:
                    estado['jogadores'][pid] = {'score': 0, 'cor': msg['cor']}
                    print(f"[LOGIN] Novo jogador registrado: {pid[:4]}")
                
                # SE JÁ EXISTE (VEIO DO BACKUP OU RECONEXÃO), SÓ ATUALIZAMOS
                # Lamport
                estado['clock'] = max(estado['clock'], msg.get('clock', 0)) + 1
                
                # Movimentação
                if msg['acao'] == 'MOVER':
                    estado['jogadores'][pid]['x'] = msg['x']
                    estado['jogadores'][pid]['y'] = msg['y']
                    estado['jogadores'][pid]['cor'] = msg['cor'] # Garante a cor certa
                    
                    if estado['bandeira']['dono'] == pid:
                        if (msg['x']**2 + msg['y']**2)**0.5 < 50: 
                            estado['jogadores'][pid]['score'] += 1
                            estado['bandeira']['dono'] = None
                            estado['bandeira']['x'] = 300; estado['bandeira']['y'] = 300
                            print(f"[GAME] {pid[:4]} PONTUOU!")

                # 3. Interação
                elif msg['acao'] == 'INTERAGIR':
                    dono = estado['bandeira']['dono']
                    if dono is None:
                         if ((msg['x'] - 300)**2 + (msg['y'] - 300)**2)**0.5 < 30:
                             estado['bandeira']['dono'] = pid
                             print(f"[MUTEX][SUCESSO] {pid[:4]} pegou a bandeira!")
                    elif dono != pid and dono in estado['jogadores']:
                        dono_pos = estado['jogadores'][dono]
                        
                        # Prova do MUTEX
                        if ((msg['x'] - 300)**2 + (msg['y'] - 300)**2)**0.5 < 30:
                             print(f"[MUTEX][NEGADO] {pid[:4]} tentou pegar, mas pertence a {dono[:4]}")

                        # Roubo
                        if ((msg['x'] - dono_pos['x'])**2 + (msg['y'] - dono_pos['y'])**2)**0.5 < 30:
                            estado['bandeira']['dono'] = None
                            estado['bandeira']['x'] = 300; estado['bandeira']['y'] = 300
                            print(f"[GAME] {pid[:4]} DERRUBOU {dono[:4]}!")

                replicar_estado()
            conn.send(pickle.dumps(estado))
        except: break
 
    print(f"[SAIU] Conexão fechada para {meu_pid[:4] if meu_pid else '?'}")
    conn.close()

# --- BACKUP ---
def loop_backup():
    global estado, TIPO_ATUAL
    s_backup = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_backup.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s_backup.bind((HOST, MINHA_PORTA))
    s_backup.listen()
    print(f"[BACKUP] Ouvindo Primary na porta {MINHA_PORTA}...")
    
    conn, _ = s_backup.accept()
    print("[BACKUP] Sincronizado com Líder!")
    
    while True:
        try:
            data = conn.recv(4096)
            if not data: raise Exception("EOF")
            novo = pickle.loads(data)
            with lock:
                estado = novo
                if estado['clock'] % 50 == 0:
                    print(f"[BACKUP] Sync OK. Clock: {estado['clock']}")
        except:
            print("[FALHA] Primary caiu! [ELEIÇÃO] Assumindo Liderança!")
            TIPO_ATUAL = "PRIMARY"
            conn.close(); s_backup.close()
            return

# --- MAIN ---
if TIPO_ATUAL == "BACKUP":
    loop_backup()

print(f"[LÍDER] Ativo na porta {MINHA_PORTA}.")
if sys.argv[3] == "PRIMARY":
    threading.Thread(target=conectar_ao_backup, daemon=True).start()

s_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_game.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
s_game.bind((HOST, MINHA_PORTA))
s_game.listen()

while True:
    conn, addr = s_game.accept()
    threading.Thread(target=gerenciar_cliente, args=(conn, addr)).start()