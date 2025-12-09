# 🎮 Roteiro de Apresentação - Capture a Bandeira Distribuído

## 📋 Informações do Grupo

**Tema:** Capture a Bandeira Distribuído  
**Objetivo:** Demonstrar sincronização de relógios (físicos e lógicos), consistência de réplicas e tolerância a falhas em um jogo 2D distribuído.

---

## 🖥️ Sobre os Terminais

### Opção 1: Tudo no mesmo computador (mais fácil)
Abram **4 janelas de terminal** no mesmo PC. O código usa `localhost`, então funciona perfeitamente.

### Opção 2: Em máquinas diferentes (mais impressionante)
Para rodar em máquinas diferentes na mesma rede:

1. Descubra o IP da máquina dos servidores (ex: `192.168.1.100`)
2. No arquivo `cliente2.py`, altere a linha:
   ```python
   SERVIDORES = [('192.168.1.100', 5555), ('192.168.1.100', 5556)]
   ```
3. No arquivo `servidor2.py`, o `HOST = '0.0.0.0'` já aceita conexões externas

**Recomendação:** Testem primeiro no mesmo computador, depois tentem em máquinas separadas se der tempo.

---

## 🛠️ Preparação Prévia (ANTES da apresentação)

- [ ] Criar ambiente virtual: `python -m venv venv`
- [ ] Ativar: `source venv/bin/activate`
- [ ] Instalar pygame: `pip install pygame`
- [ ] Testar tudo pelo menos 3 vezes
- [ ] Organizar 4 terminais lado a lado na tela

---

## 📜 ROTEIRO DA APRESENTAÇÃO

### **Parte 1: Arquitetura do Sistema (2-3 min)**

**O que falar:**
> "Nosso sistema possui uma arquitetura **Primary-Backup** com dois servidores. O Primary processa todas as requisições e replica o estado para o Backup. Se o Primary cair, o Backup assume automaticamente."

**Diagrama para mostrar:**
```
┌─────────────┐     Replicação      ┌─────────────┐
│   PRIMARY   │ ─────────────────▶  │   BACKUP    │
│ (porta 5555)│                     │ (porta 5556)│
└──────┬──────┘                     └─────────────┘
       │
       │  TCP Sockets
       ▼
┌──────────────────────────────────────────────────┐
│            CLIENTES (múltiplos jogadores)        │
└──────────────────────────────────────────────────┘
```

---

### **Parte 2: Inicialização do Sistema (2 min)**

**Terminal 1 - BACKUP (rodar primeiro!):**
```bash
source venv/bin/activate
python servidor2.py 5556 5555 BACKUP
```
> "O Backup fica aguardando conexão do Primary..."

**Terminal 2 - PRIMARY:**
```bash
source venv/bin/activate
python servidor2.py 5555 5556 PRIMARY
```
> "Agora o Primary conecta no Backup e começa a replicar o estado."

**✅ Verificar no terminal:** Deve aparecer `[REPLICAÇÃO] Conectado ao Backup na porta 5556`

---

### **Parte 3: Demonstração dos Clientes (3 min)**

**Terminais 3 e 4 - Dois jogadores:**
```bash
source venv/bin/activate
python cliente2.py
```

**O que mostrar:**
- Cada cliente tem um **UUID único** (aparece no título da janela: "CTF Distribuído - Player xxxx")
- Cada cliente tem **cor aleatória**
- Movimento com **setas do teclado** (←↑↓→)
- Placar individual no canto superior direito
- Base azul no canto superior esquerdo
- Bandeira amarela no centro
- **Informações de sincronização no canto inferior esquerdo** (Cristian e Lamport)

---

### **Parte 4: Demonstração do Algoritmo de Cristian (3 min)** ⭐⭐ **NOVO!**

**O que falar:**
> "Implementamos o **Algoritmo de Cristian** para sincronização de relógios físicos. Cada cliente periodicamente consulta o servidor para sincronizar seu relógio local."

**O que mostrar na tela do jogo (canto inferior esquerdo):**
```
[CRISTIAN] Offset: +2.35ms
[CRISTIAN] RTT: 1.2ms
[LAMPORT] Clock: 1234
```

**O que mostrar no terminal do servidor:**
```
[CRISTIAN] Enviando tempo para xxxx: 1733680000.123
```

**Explicar o algoritmo:**
> "O cliente envia uma requisição ao servidor pedindo o tempo. Medimos o RTT (Round-Trip Time) e calculamos o offset usando a fórmula: `offset = tempo_servidor + (RTT/2) - tempo_local`. Isso compensa o atraso da rede."

**Diagrama para mostrar:**
```
Cliente                              Servidor
   │                                    │
   │──── REQUEST_TIME (T1) ────────────▶│
   │                                    │ (T2 = tempo do servidor)
   │◀─── SERVER_TIME ──────────────────│
   │ (T4 = tempo de chegada)            │
   │                                    │
   │  RTT = T4 - T1                     │
   │  Offset = T2 + (RTT/2) - T4        │
```

---

### **Parte 5: Demonstração da Exclusão Mútua (3 min)** ⭐

**O que falar:**
> "Agora vamos demonstrar a **exclusão mútua** no controle da bandeira."

**Passo a passo:**

1. **Jogador 1 pega a bandeira:**
   - Aproximar do quadrado amarelo no centro
   - Pressionar **ESPAÇO**
   - ✅ Terminal do servidor: `[MUTEX][SUCESSO] xxxx pegou a bandeira!`
   - ✅ Jogador fica com borda amarela e texto "PEGOU!"

2. **Jogador 2 tenta pegar a mesma bandeira:**
   - Aproximar do centro e pressionar ESPAÇO
   - ✅ Terminal do servidor: `[MUTEX][NEGADO] yyyy tentou pegar, mas pertence a xxxx`
   - > "Apenas um jogador pode ter a bandeira por vez - **exclusão mútua garantida**."

3. **Demonstrar roubo:**
   - Jogador 2 chega perto do Jogador 1 e aperta ESPAÇO
   - ✅ Terminal: `[GAME] yyyy DERRUBOU xxxx!`
   - Bandeira volta ao centro

4. **Demonstrar pontuação:**
   - Pegar a bandeira e levar até a BASE (quadrado azul no canto superior esquerdo)
   - ✅ Terminal: `[GAME] xxxx PONTUOU!`
   - Placar atualiza

---

### **Parte 6: Demonstração do Relógio de Lamport (2 min)** ⭐

**O que falar:**
> "Implementamos **relógios lógicos de Lamport** para ordenação causal de eventos no sistema distribuído."

**O que mostrar:**
- No terminal do BACKUP, a cada 50 ticks aparece:
  ```
  [BACKUP] Sync OK. Clock: 50
  [BACKUP] Sync OK. Clock: 100
  [BACKUP] Sync OK. Clock: 150
  ```

**Explicar:**
> "Cada mensagem entre cliente e servidor incrementa o relógio lógico. Usamos a regra de Lamport: `max(relógio_local, relógio_recebido) + 1` para manter a ordenação causal dos eventos."

---

### **Parte 7: Demonstração de Tolerância a Falhas (3 min)** ⭐⭐ **MAIS IMPORTANTE!**

**O que falar:**
> "Agora a parte mais importante: **tolerância a falhas com failover automático**."

**Passo a passo:**

1. **Derrubar o PRIMARY:**
   - No Terminal 2 (PRIMARY), pressionar `Ctrl+C`

2. **Observar no BACKUP (Terminal 1):**
   ```
   [FALHA] Primary caiu! [ELEIÇÃO] Assumindo Liderança!
   [LÍDER] Ativo na porta 5556.
   ```

3. **Observar nos CLIENTES (Terminais 3 e 4):**
   ```
   Conexão perdida! Reconectando...
   Tentando conectar em localhost:5555...
   Falha em 5555. Tentando próximo...
   Conectado em 5556!
   ```

4. **Mostrar que o jogo continua funcionando!**
   - Mover os jogadores - tudo funciona
   - Pontuação foi preservada
   - Posições foram preservadas
   - UUIDs garantem que jogadores não foram duplicados

**O que falar:**
> "O sistema detectou a falha do Primary, o Backup assumiu como novo líder através do algoritmo de eleição, e os clientes reconectaram automaticamente **sem perder o estado do jogo**. Isso foi possível porque o estado era replicado continuamente."

---

### **Parte 8: Resumo das Técnicas Implementadas (2 min)**

**Apresentar tabela - 4 ALGORITMOS IMPLEMENTADOS:**

| # | Técnica | Como foi implementado |
|---|---------|----------------------|
| **1** | **Sincronização de Relógios Físicos (Cristian)** | Cliente consulta servidor, mede RTT, calcula offset: `tempo_servidor + RTT/2 - tempo_local` |
| **2** | **Sincronização de Relógios Lógicos (Lamport)** | Clock incrementado a cada evento usando `max(local, recebido) + 1` |
| **3** | **Consistência de Réplicas** | Estado replicado continuamente do Primary para o Backup via socket TCP |
| **4** | **Tratamento de Falhas** | Detecção de falha, failover automático do Backup, reconexão automática dos clientes |

> **Nota:** O requisito era implementar **pelo menos 3** algoritmos. Implementamos **4** para garantir!

---

## ⚠️ Problemas Comuns e Soluções

| Problema | Solução |
|----------|---------|
| "Address already in use" | Esperar alguns segundos ou usar `kill -9 $(lsof -t -i:5555)` |
| Cliente não conecta | Verificar se os servidores estão rodando |
| Pygame não abre | Verificar se pygame está instalado: `pip install pygame` |
| Tela preta no WSL | O código já tem `SDL_AUDIODRIVER=dummy`, deve funcionar |

---

## 🎯 Dicas Finais

1. **Testem TUDO antes** - Rodem pelo menos 3 vezes completas
2. **Organizem os terminais** - 4 terminais lado a lado facilita visualização
3. **Dividam as falas** - Cada membro pode explicar uma parte
4. **Destaquem os logs** - Os prints `[MUTEX]`, `[GAME]`, `[BACKUP]` são as "provas" dos algoritmos
5. **Tenham backup do código** - Levem em pen drive ou tenham acesso ao repositório

---

## 📁 Estrutura dos Arquivos

```
TP-final/
├── servidor2.py    # Servidor Primary/Backup
├── cliente2.py     # Cliente do jogo (pygame)
├── README.md       # Instruções de execução
└── APRESENTACAO.md # Este arquivo
```

---

**Boa apresentação! 🚀**

