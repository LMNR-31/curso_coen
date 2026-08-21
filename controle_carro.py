#!/usr/bin/env python3

import subprocess
import threading
import math
import time
import sys
import tty
import termios
import select
import os
from collections import deque

# ==========================================================
# CONFIGURAÇÃO DAS RODAS (Skid-Steer)
# ==========================================================

RODAS = {
    "roda_frente_esquerda": {
        "topic": "/joint4_cmd",  # roda4
        "sinal": 1.0,
        "lado": "esquerdo"
    },
    "roda_frente_direita": {
        "topic": "/joint1_cmd",  # roda1
        "sinal": 1.0,
        "lado": "direito"
    },
    "roda_tras_esquerda": {
        "topic": "/joint3_cmd",  # roda3
        "sinal": -1.0,
        "lado": "esquerdo"
    },
    "roda_tras_direita": {
        "topic": "/joint2_cmd",  # roda2
        "sinal": -1.0,
        "lado": "direito"
    }
}

# ==========================================================
# PARÂMETROS DO ROBÔ
# ==========================================================

WHEEL_RADIUS = 0.05      # Raio da roda (metros)
WHEEL_BASE = 0.15        # Distância entre rodas (metros)
MAX_LINEAR = 0.5         # Velocidade linear máxima (m/s)
MAX_ANGULAR = 1.0        # Velocidade angular máxima (rad/s)
MAX_WHEEL_SPEED = 5.0    # Velocidade máxima das rodas (rad/s)

# Velocidades padrão
linear_speed = 0.15
angular_speed = 0.3

# ==========================================================
# CONFIGURAÇÃO DE MOVIMENTO POR COMANDO
# ==========================================================

# Cada comando faz a roda girar 1 volta completa
VOLTAS_POR_COMANDO = 1.0
DISTANCIA_POR_COMANDO = VOLTAS_POR_COMANDO * 2 * math.pi * WHEEL_RADIUS
ANGULO_POR_COMANDO = VOLTAS_POR_COMANDO * 2 * math.pi

# FREQUÊNCIA DE ENVIO (aumentada)
PASSO_TEMPO = 0.05  # 10ms entre cada comando (antes era 50ms)
FATOR_SUAVIZACAO = 0.95  # Fator para movimento mais suave

def calcular_duracao(linear_vel, angular_vel):
    """Calcula o tempo necessário para executar o comando"""
    if linear_vel != 0:
        tempo = DISTANCIA_POR_COMANDO / abs(linear_vel)
    elif angular_vel != 0:
        tempo = ANGULO_POR_COMANDO / abs(angular_vel)
    else:
        tempo = 0.1
    return max(0.3, min(2.0, tempo))

# ==========================================================
# FILA DE COMANDOS (ACÚMULO)
# ==========================================================

class FilaComandos:
    def __init__(self):
        self.fila = deque()
        self.lock = threading.Lock()
        self.executando = False
        self.parar_ignorado = True
        self.posicao_rodas = {topic: 0.0 for topic in ["/joint1_cmd", "/joint2_cmd", "/joint3_cmd", "/joint4_cmd"]}
        self.ultimo_comando = None
        self.rodas_paradas = True
        self.total_comandos = 0
        
    def adicionar(self, linear, angular, duracao=None):
        """Adiciona um comando à fila com duração automática"""
        with self.lock:
            # Ignora comandos de parar
            if linear == 0.0 and angular == 0.0:
                print("\n[PARAR] Comando de parar IGNORADO - continuando acumulação")
                return
            
            # Calcula duração automaticamente
            if duracao is None:
                duracao = calcular_duracao(linear, angular)
            
            # Verifica se é o mesmo comando
            if self.ultimo_comando == (linear, angular):
                print(f"\n[FILA] Comando duplicado ignorado")
                return
            
            self.fila.append((linear, angular, duracao))
            self.ultimo_comando = (linear, angular)
            tipo = self._get_tipo_movimento(linear, angular)
            
            # Mostra informações do comando
            if linear != 0:
                print(f"\n[FILA] + {tipo} | L:{linear:+.2f} m/s")
                print(f"[FILA]   Distância: {DISTANCIA_POR_COMANDO:.3f}m ({VOLTAS_POR_COMANDO:.1f} volta)")
            elif angular != 0:
                print(f"\n[FILA] + {tipo} | A:{angular:+.2f} rad/s")
                print(f"[FILA]   Ângulo: {math.degrees(ANGULO_POR_COMANDO):.1f}° ({VOLTAS_POR_COMANDO:.1f} volta)")
                print(f"[FILA]   GIRO NO LUGAR - rodas em sentidos OPOSTOS")
            
            print(f"[FILA]   Duração: {duracao:.2f}s")
            print(f"[FILA] Comandos na fila: {len(self.fila)}")
            
            if not self.executando:
                self.executando = True
                threading.Thread(target=self.executar, daemon=True).start()
    
    def _get_tipo_movimento(self, linear, angular):
        if linear > 0.01 and abs(angular) < 0.01:
            return "FRENTE"
        elif linear < -0.01 and abs(angular) < 0.01:
            return "TRÁS"
        elif abs(linear) < 0.01 and angular > 0.01:
            return "GIRO ESQ (no lugar)"
        elif abs(linear) < 0.01 and angular < -0.01:
            return "GIRO DIR (no lugar)"
        elif linear > 0 and angular > 0:
            return "CURVA ESQ"
        elif linear > 0 and angular < 0:
            return "CURVA DIR"
        else:
            return "PARADO"
    
    def executar(self):
        """Executa os comandos da fila em sequência"""
        while True:
            with self.lock:
                if not self.fila:
                    self.executando = False
                    self.parar_rodas()
                    print(f"\n[FILA] Todos os {self.total_comandos} comandos executados!")
                    self.total_comandos = 0
                    break
                
                linear, angular, duracao = self.fila.popleft()
                self.total_comandos += 1
            
            self.ultimo_comando = None
            
            tipo = self._get_tipo_movimento(linear, angular)
            print(f"\n[EXECUTANDO] {tipo} | Restam: {len(self.fila)}")
            
            self.mover_robo_com_tempo(linear, angular, duracao)
            time.sleep(0.1)  # Pausa entre comandos
    
    def mover_robo_com_tempo(self, linear, angular, duracao):
        """Move o robô por um tempo específico usando posição incremental - ALTA FREQUÊNCIA"""
        linear = max(-MAX_LINEAR, min(MAX_LINEAR, linear))
        angular = max(-MAX_ANGULAR, min(MAX_ANGULAR, angular))
        
        # Calcular velocidades das rodas (rad/s)
        v_left = (linear - (angular * WHEEL_BASE / 2)) / WHEEL_RADIUS
        v_right = (linear + (angular * WHEEL_BASE / 2)) / WHEEL_RADIUS
        
        v_left = max(-MAX_WHEEL_SPEED, min(MAX_WHEEL_SPEED, v_left))
        v_right = max(-MAX_WHEEL_SPEED, min(MAX_WHEEL_SPEED, v_right))
        
        # Mostra o tipo de movimento
        if linear == 0 and angular != 0:
            print(f"[GIRO NO LUGAR] Esquerda: {v_left:+.2f} rad/s | Direita: {v_right:+.2f} rad/s")
            print(f"[GIRO NO LUGAR] Rodas em SENTIDOS OPOSTOS!")
        else:
            print(f"[RODAS] Esquerda: {v_left:+.2f} rad/s | Direita: {v_right:+.2f} rad/s")
        
        # ENVIA COMANDOS COM ALTA FREQUÊNCIA (passo menor)
        passo = PASSO_TEMPO  # 10ms - ALTA FREQUÊNCIA
        passos = max(1, int(duracao / passo))
        
        # Calcula incremento por passo
        inc_left = v_left * passo * FATOR_SUAVIZACAO
        inc_right = v_right * passo * FATOR_SUAVIZACAO
        
        # Envia comandos em alta frequência
        for i in range(passos):
            with self.lock:
                # Atualiza posições
                self.posicao_rodas["/joint4_cmd"] += inc_left * 1.0   # frente esq
                self.posicao_rodas["/joint3_cmd"] += inc_left * -1.0  # trás esq
                self.posicao_rodas["/joint1_cmd"] += inc_right * 1.0  # frente dir
                self.posicao_rodas["/joint2_cmd"] += inc_right * -1.0 # trás dir
            
            # Envia comandos para as rodas
            for nome, config in RODAS.items():
                posicao = self.posicao_rodas[config["topic"]]
                self._enviar_comando_posicao(config["topic"], posicao)
            
            # Espera o passo (ALTA FREQUÊNCIA)
            time.sleep(passo)
        
        # Após o movimento, para as rodas
        self.parar_rodas()
    
    def _enviar_comando_posicao(self, topic, posicao):
        """Envia comando de posição para uma roda"""
        comando = [
            "gz",
            "topic",
            "-t", topic,
            "-m", "gz.msgs.Double",
            "-p", f"data: {posicao}"
        ]

        try:
            result = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=0.5  # Timeout reduzido para maior frequência
            )
            if result.returncode != 0:
                return False
            return True
        except Exception as e:
            return False
    
    def parar_rodas(self):
        """Para todas as rodas mantendo a posição atual"""
        for nome, config in RODAS.items():
            posicao = self.posicao_rodas[config["topic"]]
            self._enviar_comando_posicao(config["topic"], posicao)
        self.rodas_paradas = True
    
    def limpar(self):
        """Limpa a fila e para o robô"""
        with self.lock:
            self.fila.clear()
            self.executando = False
            self.ultimo_comando = None
            self.total_comandos = 0
            print("\n[FILA] Fila limpa!")
        self.parar_rodas()
    
    def get_tamanho(self):
        with self.lock:
            return len(self.fila)
    
    def get_fila(self):
        with self.lock:
            return list(self.fila)

# ==========================================================
# CRIAR FILA DE COMANDOS
# ==========================================================

fila_global = FilaComandos()

# ==========================================================
# CONTROLE POR TECLADO
# ==========================================================

def get_key():
    settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key
    except:
        return ''

# ==========================================================
# LIMPAR TELA
# ==========================================================

def limpar_tela():
    os.system('clear' if os.name == 'posix' else 'cls')

# ==========================================================
# MOSTRAR STATUS
# ==========================================================

def mostrar_status():
    limpar_tela()
    print("\n" + "=" * 70)
    print("        CONTROLE DO ROBÔ SKID-STEER - ACÚMULO DE MOVIMENTOS")
    print("=" * 70)
    print("\nCONTROLES:")
    print("  W  - Adicionar FRENTE ({:.1f} volta das rodas)".format(VOLTAS_POR_COMANDO))
    print("  S  - Adicionar TRÁS ({:.1f} volta das rodas)".format(VOLTAS_POR_COMANDO))
    print("  A  - Adicionar GIRO ESQUERDA ({:.1f} volta) - GIRO NO LUGAR".format(VOLTAS_POR_COMANDO))
    print("  D  - Adicionar GIRO DIREITA ({:.1f} volta) - GIRO NO LUGAR".format(VOLTAS_POR_COMANDO))
    print("  Q  - Parar (IGNORADO - não adiciona à fila)")
    print("  L  - Limpar fila e parar robô")
    print("  +  - Aumentar velocidade")
    print("  -  - Diminuir velocidade")
    print("  R  - Resetar velocidades")
    print("  1  - Teste: Frente + Giro + Frente")
    print("  2  - Teste: Quadrado (com giro no lugar)")
    print("  ESC - Sair")
    print("=" * 70)
    print(f"Velocidade Linear: {linear_speed:.2f} m/s")
    print(f"Velocidade Angular: {angular_speed:.2f} rad/s")
    print(f"Distância por comando: {DISTANCIA_POR_COMANDO:.3f}m")
    print(f"Ângulo por comando: {math.degrees(ANGULO_POR_COMANDO):.1f}°")
    print(f"Frequência de envio: {1/PASSO_TEMPO:.0f} Hz")
    print(f"Comandos na fila: {fila_global.get_tamanho()}")
    print("=" * 70)
    
    fila = fila_global.get_fila()
    if fila:
        print("\nFILA DE COMANDOS:")
        for i, (linear, angular, duracao) in enumerate(fila, 1):
            if linear > 0 and angular == 0:
                tipo = "FRENTE"
                info = f"{DISTANCIA_POR_COMANDO:.3f}m"
            elif linear < 0 and angular == 0:
                tipo = "TRÁS"
                info = f"{DISTANCIA_POR_COMANDO:.3f}m"
            elif linear == 0 and angular > 0:
                tipo = "GIRO ESQ"
                info = f"{math.degrees(ANGULO_POR_COMANDO):.1f}° (no lugar)"
            elif linear == 0 and angular < 0:
                tipo = "GIRO DIR"
                info = f"{math.degrees(ANGULO_POR_COMANDO):.1f}° (no lugar)"
            elif linear > 0 and angular > 0:
                tipo = "CURVA ESQ"
                info = "curva"
            elif linear > 0 and angular < 0:
                tipo = "CURVA DIR"
                info = "curva"
            else:
                tipo = "PARADO"
                info = ""
            print(f"  {i:2d}. {tipo:12s} | {info:20s} | {duracao:.2f}s")
    else:
        print("\nFILA: VAZIA")
    
    print("\n" + "=" * 70)

# ==========================================================
# MOVIMENTOS PROGRAMADOS
# ==========================================================

def teste_frente_giro_frente():
    print("\n" + "=" * 70)
    print("TESTE: FRENTE + GIRO + FRENTE")
    print("=" * 70)
    
    fila_global.limpar()
    fila_global.adicionar(linear_speed, 0.0)    # Frente
    fila_global.adicionar(0.0, angular_speed)   # Giro no lugar
    fila_global.adicionar(linear_speed, 0.0)    # Frente
    
    print("\n[TESTE] Comandos adicionados:")

def teste_quadrado():
    print("\n" + "=" * 70)
    print("TESTE: QUADRADO (com giro no lugar)")
    print("=" * 70)
    
    fila_global.limpar()
    
    for _ in range(4):
        fila_global.adicionar(linear_speed, 0.0)     # Frente
        fila_global.adicionar(0.0, angular_speed)    # Gira no lugar
    
    print("\n[TESTE] Quadrado adicionado à fila")

# ==========================================================
# LOOP PRINCIPAL
# ==========================================================

def main():
    global linear_speed, angular_speed
    
    linear_speed = 0.15
    angular_speed = 0.3
    
    mostrar_status()
    
    while True:
        key = get_key()
        
        if key == 'w' or key == 'W':
            fila_global.adicionar(linear_speed, 0.0)
            mostrar_status()
        
        elif key == 's' or key == 'S':
            fila_global.adicionar(-linear_speed, 0.0)
            mostrar_status()
        
        elif key == 'a' or key == 'A':
            fila_global.adicionar(0.0, angular_speed)
            mostrar_status()
        
        elif key == 'd' or key == 'D':
            fila_global.adicionar(0.0, -angular_speed)
            mostrar_status()
        
        elif key == 'q' or key == 'Q' or key == ' ':
            print("\n[PARAR] Comando IGNORADO - continue adicionando comandos")
            time.sleep(0.3)
            mostrar_status()
        
        elif key == 'l' or key == 'L':
            fila_global.limpar()
            time.sleep(0.3)
            mostrar_status()
        
        elif key == '+':
            linear_speed = min(MAX_LINEAR, linear_speed + 0.05)
            angular_speed = min(MAX_ANGULAR, angular_speed + 0.1)
            mostrar_status()
            print(f"\n[VELOCIDADE] Linear: {linear_speed:.2f} | Angular: {angular_speed:.2f}")
        
        elif key == '-':
            linear_speed = max(0.05, linear_speed - 0.05)
            angular_speed = max(0.1, angular_speed - 0.1)
            mostrar_status()
            print(f"\n[VELOCIDADE] Linear: {linear_speed:.2f} | Angular: {angular_speed:.2f}")
        
        elif key == 'r' or key == 'R':
            linear_speed = 0.15
            angular_speed = 0.3
            mostrar_status()
            print(f"\n[RESET] Velocidades restauradas")
        
        elif key == '1':
            teste_frente_giro_frente()
            time.sleep(0.5)
            mostrar_status()
        
        elif key == '2':
            teste_quadrado()
            time.sleep(0.5)
            mostrar_status()
        
        elif key == '\x1b':
            fila_global.limpar()
            limpar_tela()
            print("\nEncerrando controle...")
            break
        
        time.sleep(0.05)

# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPÇÃO] Ctrl+C detectado")
        fila_global.limpar()
        print("\n[FINALIZADO] Controle encerrado")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        fila_global.limpar()