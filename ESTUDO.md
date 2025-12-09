# 📚 Guia de Estudo - CTF Distribuído

## Arquitetura do Sistema

```
┌─────────────┐     Replicação      ┌─────────────┐
│   PRIMARY   │ ──────────────────▶ │   BACKUP    │
│ (porta 5555)│                     │ (porta 5556)│
└──────┬──────┘                     └─────────────┘
       │ TCP Sockets
       ▼
   [CLIENTES]
```

- **PRIMARY**: Processa todas as requisições dos clientes
- **BACKUP**: Recebe cópia do estado; assume se PRIMARY cair
- **Clientes**: Jogadores que se conectam via socket TCP

---

## Os 4 Algoritmos Implementados

### 1. Algoritmo de Cristian (Relógio Físico)

**O que é:** Sincroniza o relógio do cliente com o servidor.

**Como funciona:**
1. Cliente envia pedido de tempo (marca T1)
2. Servidor responde com seu tempo (T2)
3. Cliente recebe resposta (marca T4)
4. RTT = T4 - T1 (tempo de ida e volta)
5. **Offset = T2 + (RTT/2) - T4**

**Por que RTT/2?** Assumimos que a mensagem leva metade do tempo para ir e metade para voltar.

**No código:**
- Cliente: `sincronizar_relogio_cristian()` em `cliente2.py`
- Servidor: trata `acao == 'SYNC_TIME'` em `servidor2.py`

---

### 2. Relógios Lógicos de Lamport

**O que é:** Ordena eventos em sistemas distribuídos sem depender de relógio físico.

**Regra:** `clock = max(clock_local, clock_recebido) + 1`

**Como funciona:**
1. A cada evento local, incrementa o clock
2. Ao enviar mensagem, inclui o clock
3. Ao receber, aplica a regra do max + 1

**No código:**
- Cliente: `meu_relogio_lamport += 1` antes de enviar
- Servidor: `estado['clock'] = max(estado['clock'], msg.get('clock', 0)) + 1`

**Para que serve:** Garante ordenação causal - se evento A causou B, então clock(A) < clock(B).

---

### 3. Consistência de Réplicas (Primary-Backup)

**O que é:** Mantém cópias sincronizadas do estado em múltiplos servidores.

**Como funciona:**
1. PRIMARY processa todas as operações
2. Após cada operação, PRIMARY envia estado completo para BACKUP
3. BACKUP aplica o estado recebido

**No código:**
- `replicar_estado()`: PRIMARY envia estado via socket
- `loop_backup()`: BACKUP recebe e aplica estado

**Vantagem:** Se PRIMARY cair, BACKUP tem o estado atualizado.

---

### 4. Tratamento de Falhas (Failover)

**O que é:** Sistema continua funcionando mesmo quando um servidor falha.

**Como funciona:**
1. BACKUP detecta que PRIMARY parou de enviar dados (exceção no socket)
2. BACKUP muda `TIPO_ATUAL` para "PRIMARY" e começa a aceitar clientes
3. Clientes detectam falha e tentam reconectar no próximo servidor da lista

**No código:**
- Servidor: `except: ... TIPO_ATUAL = "PRIMARY"` no `loop_backup()`
- Cliente: loop em `conectar()` que tenta cada servidor

---

## Fluxo de uma Jogada

```
1. Cliente pressiona tecla → incrementa Lamport → envia pacote
2. Servidor recebe → atualiza Lamport → processa ação → replica para BACKUP
3. Servidor envia estado atualizado → Cliente recebe → atualiza Lamport → desenha tela
```

---

## Perguntas que o Professor Pode Fazer

**P: O que é o Algoritmo de Cristian?**
> Sincroniza relógios físicos. O cliente pede o tempo ao servidor, mede o RTT, e calcula o offset usando `T_servidor + RTT/2 - T_local`.

**P: Por que usar RTT/2?**
> Porque assumimos que o tempo de ida é igual ao de volta. Então o tempo do servidor quando a resposta chegou é aproximadamente `T_servidor + RTT/2`.

**P: Qual a diferença entre Lamport e Cristian?**
> Lamport é relógio **lógico** (ordena eventos, não mede tempo real). Cristian é relógio **físico** (sincroniza o tempo real entre máquinas).

**P: O que acontece se o PRIMARY cair?**
> O BACKUP detecta a falha (socket fecha), assume como novo PRIMARY, e começa a aceitar conexões. Clientes reconectam automaticamente.

**P: Como funciona a exclusão mútua da bandeira?**
> O servidor controla quem tem a bandeira (`estado['bandeira']['dono']`). Só um jogador pode ter por vez. Se alguém tenta pegar enquanto outro tem, é negado.

**P: O que é replicação Primary-Backup?**
> O PRIMARY é o único que processa operações. Após cada operação, ele envia o estado completo para o BACKUP manter uma cópia atualizada.

**P: Por que usar `max(local, recebido) + 1` no Lamport?**
> O `max` garante que o clock nunca anda para trás. O `+1` garante que cada evento tem um timestamp único e crescente.

**P: Como o cliente sabe para qual servidor conectar?**
> Ele tem uma lista de servidores. Tenta o primeiro; se falhar, tenta o próximo. Isso permite failover automático.

---

## Arquivos do Projeto

| Arquivo | Função |
|---------|--------|
| `servidor2.py` | Servidor PRIMARY/BACKUP com toda lógica |
| `cliente2.py` | Cliente pygame com Cristian e Lamport |
| `requirements.txt` | Dependência: pygame |

---

## Conceitos-Chave em Uma Frase

- **Lamport**: Ordena eventos sem relógio físico
- **Cristian**: Sincroniza relógio físico via rede
- **Primary-Backup**: Uma cópia processa, outra fica de reserva
- **Failover**: Sistema continua se um componente falhar
- **RTT**: Tempo total de ida e volta de uma mensagem

