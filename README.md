# CTF Distribuído

Jogo capture the flag 2D com arquitetura Primary-Backup. Implementa sincronização de relógios (Cristian e Lamport), replicação de estado e tolerância a falhas.

## Requisitos

- Python 3.11+
- pygame

## Instalação

```bash
python -m venv venv
source venv/bin/activate
pip install pygame
```

## Execução

Abra 3 terminais:

```bash
# Terminal 1 - Backup
python servidor2.py 5556 5555 BACKUP

# Terminal 2 - Primary
python servidor2.py 5555 5556 PRIMARY

# Terminal 3+ - Clientes
python cliente2.py
```

## Controles

- Setas: mover
- Espaço: pegar bandeira / derrubar adversário

## Objetivo

Pegue a bandeira no centro e leve até a base (canto superior esquerdo) para pontuar.
