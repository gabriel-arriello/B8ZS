"""
B8ZS — Bipolar with 8-Zero Substitution
========================================
Regras de codificação:
  - Bit 1  → pulso AMI alternado (+1 / -1)
  - Bit 0  → nível zero (0)
  - 8 zeros consecutivos → 000VB0VB  (só após pelo menos 1 pulso não-zero)
      V = violação  (MESMA polaridade do último pulso não-zero)
      B = bipolar   (polaridade OPOSTA — segue AMI)

Referência: Forouzan cap.4 — slides UTFPR pág. 4.57-4.58.
"""


def codificar(binario: str) -> list[int]:
    """
    Converte string de bits ('0'/'1') para lista de níveis AMI/B8ZS.
    Retorna lista de int: -1, 0 ou +1.
    """
    niveis: list[int] = []
    proximo_pulso = 1     # próxima polaridade AMI esperada
    ultimo_nao_zero = 0   # 0 = nenhum pulso não-zero emitido ainda

    i = 0
    while i < len(binario):
        # Detecta bloco de 8 zeros — só substitui após primeiro pulso não-zero
        if (ultimo_nao_zero != 0
                and binario[i] == '0'
                and i + 8 <= len(binario)
                and binario[i:i + 8] == '00000000'):

            v = ultimo_nao_zero    # V viola AMI (mesma pol. do último)
            b = -v                  # B segue AMI (oposto)

            # Padrão: 0 0 0 V B 0 V B
            niveis.extend([0, 0, 0, v, b, 0, v, b])

            ultimo_nao_zero = b
            proximo_pulso = -b
            i += 8

        elif binario[i] == '1':
            niveis.append(proximo_pulso)
            ultimo_nao_zero = proximo_pulso
            proximo_pulso = -proximo_pulso
            i += 1

        else:  # '0' normal
            niveis.append(0)
            i += 1

    return niveis


def decodificar(niveis: list[int]) -> str:
    """
    Converte lista de níveis AMI/B8ZS de volta para string de bits.

    Detecta 000VB0VB verificando se V é uma VIOLAÇÃO AMI real
    (mesma polaridade do último pulso não-zero visto).
    Só considera padrão B8ZS válido se já houve pelo menos um pulso não-zero.
    """
    bits: list[str] = []
    i = 0
    ultimo_nao_zero = 0   # 0 = nenhum pulso não-zero visto ainda

    while i < len(niveis):
        # Tenta detectar padrão B8ZS: [0,0,0,V,B,0,V,B]
        if i + 8 <= len(niveis) and ultimo_nao_zero != 0:
            n = niveis[i:i + 8]
            v = n[3]
            b = n[4]

            padrao_estrutural = (
                n[0] == 0
                and n[1] == 0
                and n[2] == 0
                and v != 0
                and b != 0
                and b == -v          # B oposto a V
                and n[5] == 0
                and n[6] == v        # segundo V
                and n[7] == b        # segundo B
            )

            # V deve violar AMI: mesma pol. do último não-zero
            violacao = (v == ultimo_nao_zero)

            if padrao_estrutural and violacao:
                bits.extend(['0'] * 8)
                ultimo_nao_zero = b
                i += 8
                continue

        # Processamento normal
        nivel = niveis[i]
        if nivel == 0:
            bits.append('0')
        else:
            bits.append('1')
            ultimo_nao_zero = nivel
        i += 1

    return ''.join(bits)
