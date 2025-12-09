import socket
import pickle
import pygame
import random
import time
import os
import uuid
import threading

# so pra caso voce esteja usando o WSL igual eu!!
os.environ["SDL_AUDIODRIVER"] = "dummy"

SERVIDORES = [('localhost', 5555), ('localhost', 5556)]
servidor_atual_idx = 0

LARGURA = 600; ALTURA = 600
# Gera um ID único que não muda ao reconectar
MEU_ID = str(uuid.uuid4()) 

COR_PLAYER = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# --- ALGORITMO DE CRISTIAN: Variáveis de Sincronização de Relógio Físico ---
clock_offset = 0.0  # Diferença entre relógio local e servidor
ultimo_rtt = 0.0    # Round-trip time da última sincronização
lock_cristian = threading.Lock()

pygame.init()
pygame.font.init()
fonte = pygame.font.SysFont(None, 24)
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption(f"CTF Distribuído - Player {MEU_ID[:4]}")

cliente = None

def conectar():
    global cliente, servidor_atual_idx
    while True:
        ip, porta = SERVIDORES[servidor_atual_idx]
        print(f"Tentando conectar em {ip}:{porta}...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, porta))
            s.settimeout(2.0)
            cliente = s
            print(f"Conectado em {porta}!")
            return True
        except:
            print(f"Falha em {porta}. Tentando próximo...")
            servidor_atual_idx = (servidor_atual_idx + 1) % len(SERVIDORES)
            time.sleep(1)

conectar()
x = random.randint(0, LARGURA - 50); y = random.randint(0, ALTURA - 50)
meu_relogio_lamport = 0

# --- ALGORITMO DE CRISTIAN: Thread de Sincronização de Relógio Físico ---
def sincronizar_relogio_cristian():
    """
    Implementação do Algoritmo de Cristian para sincronização de relógio físico.
    O cliente envia request ao servidor, mede o RTT, e calcula o offset.
    Fórmula: tempo_ajustado = tempo_servidor + (RTT / 2)
    """
    global clock_offset, ultimo_rtt
    while True:
        try:
            # Cria socket separado para não interferir no jogo
            ip, porta = SERVIDORES[servidor_atual_idx]
            sock_sync = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_sync.settimeout(3.0)
            sock_sync.connect((ip, porta))
            
            # T1: Tempo local antes de enviar
            t1 = time.time()
            
            # Envia request de sincronização
            pacote_sync = {
                'id': MEU_ID,
                'acao': 'SYNC_TIME',
                'cor': COR_PLAYER
            }
            sock_sync.send(pickle.dumps(pacote_sync))
            
            # Recebe resposta do servidor
            resp = sock_sync.recv(4096)
            
            # T4: Tempo local após receber
            t4 = time.time()
            
            resposta = pickle.loads(resp)
            if resposta.get('acao') == 'SYNC_TIME_RESPONSE':
                # T2/T3: Tempo do servidor (assumimos processamento instantâneo)
                t_servidor = resposta['server_time']
                
                # RTT = T4 - T1 (tempo total de ida e volta)
                rtt = t4 - t1
                
                # Algoritmo de Cristian: 
                # O tempo estimado do servidor quando recebemos = t_servidor + RTT/2
                # Offset = tempo_servidor_estimado - tempo_local
                tempo_servidor_estimado = t_servidor + (rtt / 2)
                offset = tempo_servidor_estimado - t4
                
                with lock_cristian:
                    clock_offset = offset
                    ultimo_rtt = rtt
                
                print(f"[CRISTIAN] Sync OK! RTT={rtt*1000:.1f}ms, Offset={offset*1000:.2f}ms")
            
            sock_sync.close()
        except Exception as e:
            pass  # Falha silenciosa, tentará novamente
        
        # Sincroniza a cada 5 segundos
        time.sleep(5)

# Inicia thread de sincronização de Cristian
thread_cristian = threading.Thread(target=sincronizar_relogio_cristian, daemon=True)
thread_cristian.start()
print("[CRISTIAN] Thread de sincronização de relógio físico iniciada")

def desenhar(estado):
    tela.fill((0, 0, 0))
    bandeira = estado['bandeira']
    
    # Base
    pygame.draw.rect(tela, (0,0,255), (0,0,60,60), 2)
    tela.blit(fonte.render("BASE", True, (0,0,255)), (5, 5))
    
    # Bandeira
    if bandeira['dono'] is None:
        pygame.draw.rect(tela, (255,255,0), (bandeira['x'], bandeira['y'], 25, 25))
        
    y_placar = 10
    for pid, p in estado['jogadores'].items():
        # Desenha Player
        pygame.draw.rect(tela, p['cor'], (p['x'], p['y'], 20, 20))
        
        # Borda se tiver bandeira
        if bandeira['dono'] == pid:
            pygame.draw.rect(tela, (255,255,0), (p['x']-5, p['y']-5, 30, 30), 3)
            tela.blit(fonte.render("PEGOU!", True, (255,255,255)), (p['x'], p['y']-20))
            
        # Placar (Usa os primeiros 4 digitos do UUID)
        texto = f"P-{pid[:4]}: {p['score']}"
        tela.blit(fonte.render(texto, True, p['cor']), (LARGURA - 150, y_placar))
        y_placar += 25
    
    # --- CRISTIAN: Mostra informações de sincronização de relógio ---
    with lock_cristian:
        offset_ms = clock_offset * 1000
        rtt_ms = ultimo_rtt * 1000
    
    # Tempo local ajustado pelo Cristian
    tempo_ajustado = time.time() + clock_offset
    
    # Exibe no canto inferior esquerdo
    cor_info = (100, 255, 100)  # Verde claro
    tela.blit(fonte.render(f"[CRISTIAN] Offset: {offset_ms:+.2f}ms", True, cor_info), (5, ALTURA - 60))
    tela.blit(fonte.render(f"[CRISTIAN] RTT: {rtt_ms:.1f}ms", True, cor_info), (5, ALTURA - 40))
    tela.blit(fonte.render(f"[LAMPORT] Clock: {estado['clock']}", True, (255, 200, 100)), (5, ALTURA - 20))
            
    pygame.display.update()

rodando = True
while rodando:
    pygame.time.Clock().tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: rodando = False

    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_LEFT]: x -= 3
    if teclas[pygame.K_RIGHT]: x += 3
    if teclas[pygame.K_UP]: y -= 3
    if teclas[pygame.K_DOWN]: y += 3
    
    acao = "MOVER"
    if teclas[pygame.K_SPACE]: acao = "INTERAGIR"

    meu_relogio_lamport += 1
    
    # ENVIA O MEU_ID NO PACOTE AGORA!
    pacote = {
        'id': MEU_ID, 
        'acao': acao, 
        'x': x, 'y': y, 
        'cor': COR_PLAYER, 
        'clock': meu_relogio_lamport
    }

    try:
        cliente.send(pickle.dumps(pacote))
        resp = cliente.recv(4096)
        estado = pickle.loads(resp)
        meu_relogio_lamport = max(meu_relogio_lamport, estado['clock']) + 1
        desenhar(estado)
    except:
        print("Conexão perdida! Reconectando...")
        cliente.close()
        conectar()

pygame.quit()