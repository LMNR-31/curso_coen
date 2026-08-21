#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import sys
import select
import termios
import tty
import os

class WheelController(Node):
    def __init__(self):
        super().__init__('wheel_controller')
        
        # Parâmetros
        self.declare_parameter('robot_name', 'modelo_carrinho')
        self.declare_parameter('max_velocity', 2.0)
        self.declare_parameter('velocity_step', 0.1)
        
        self.robot_name = self.get_parameter('robot_name').value
        self.max_velocity = self.get_parameter('max_velocity').value
        self.velocity_step = self.get_parameter('velocity_step').value
        
        # Configuração das rodas
        self.wheels = {
            '1': {'name': 'Frontal Esquerda (FL)', 'topic': f'/{self.robot_name}/roda_frente_esquerda_cmd', 'velocity': 0.0},
            '2': {'name': 'Frontal Direita (FR)',  'topic': f'/{self.robot_name}/roda_frente_direita_cmd', 'velocity': 0.0},
            '3': {'name': 'Traseira Esquerda (RL)', 'topic': f'/{self.robot_name}/roda_traz_esquerda_cmd', 'velocity': 0.0},
            '4': {'name': 'Traseira Direita (RR)',  'topic': f'/{self.robot_name}/roda_traz_direita_cmd', 'velocity': 0.0},
        }
        
        self.selected_wheel = '1'
        self.control_mode = 'individual'  # 'individual', 'tanque', 'virar'
        self.virar_velocity = 0.0  # Velocidade de rotação no modo virar
        self.tanque_velocity = 0.0  # Velocidade linear do tanque
        
        # Publishers
        self.wheel_pubs = {}
        for key, wheel in self.wheels.items():
            self.wheel_pubs[key] = self.create_publisher(Float64, wheel['topic'], 10)
            self.get_logger().info(f'Publisher criado: {wheel["name"]} → {wheel["topic"]}')
        
        # Configuração do teclado
        self.settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        
        self.create_timer(0.05, self.read_keyboard)
        
        self.print_instructions()
    
    def print_instructions(self):
        """Imprime o menu de forma limpa"""
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        os.system('clear')
        
        print(f"""
╔════════════════════════════════════════════════╗
║   CONTROLADOR DE RODAS INDIVIDUAIS - GAZEBO    ║
║   Robô: {self.robot_name:<38} ║
╚════════════════════════════════════════════════╝

ESTRUTURA DO ROBÔ:
  [1 FL]                    [2 FR]
  ┌──────────────────────────┐
  │                          │
  │       {self.robot_name.upper():^16}       │
  │                          │
  └──────────────────────────┘
  [3 RL]                    [4 RR]

═══════════════════════════════════════════════════

MODO: INDIVIDUAL (I) | TANQUE (T) | VIRAR (R)

═══════════════════════════════════════════════════

MODO INDIVIDUAL:
  SELEÇÃO:
    1-4    →  Selecionar roda (1=FL, 2=FR, 3=RL, 4=RR)
  
  CONTROLE:
    W / S  →  Aumentar / Diminuir velocidade
    + / =  →  Aumentar TODAS as rodas
    - / _  →  Diminuir TODAS as rodas
    SPACE  →  Parar TODAS as rodas

───────────────────────────────────────────────────

MODO TANQUE (T):
  Controla movimento com opção de virar
  W / S  →  Avançar / Retroceder
  A      →  Virar à ESQUERDA (no lugar)
  D      →  Virar à DIREITA (no lugar)
  Q      →  Parar movimento linear
  SPACE  →  Parar tudo (linear + rotação)

───────────────────────────────────────────────────

MODO VIRAR (R):
  Gira no lugar (Direita ↑ Esquerda ↓)
  W      →  Girar SENTIDO HORÁRIO (Direita frente)
  S      →  Girar ANTI-HORÁRIO (Esquerda frente)
  A / D  →  Aumentar / Diminuir velocidade de giro
  SPACE  →  Parar tudo

───────────────────────────────────────────────────

GERAL:
  V      →  Ver velocidades atuais
  H      →  Mostrar este menu
  X      →  Sair do programa

PRESSIONE UMA TECLA PARA COMEÇAR...
""")
        
        tty.setcbreak(sys.stdin.fileno())
        self.get_logger().info(f'Controlador inicializado para: {self.robot_name}')
    
    def get_key(self):
        """Leitura não-bloqueante"""
        try:
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).lower()
        except Exception as e:
            self.get_logger().error(f'Erro ao ler teclado: {e}')
        return None
    
    def read_keyboard(self):
        key = self.get_key()
        if key is None:
            return
        
        try:
            # Mudar modo
            if key == 't':
                self.control_mode = 'tanque'
                self.tanque_velocity = 0.0
                print("\n🎮 Modo TANQUE ativado (W/S movimento + A/D virar)")
                self.get_logger().info('Modo: TANQUE')
                return
            
            elif key == 'r':
                self.control_mode = 'virar'
                self.virar_velocity = 0.0
                print("\n🔄 Modo VIRAR ativado (Gira no lugar)")
                self.get_logger().info('Modo: VIRAR')
                return
            
            elif key == 'i':
                self.control_mode = 'individual'
                print("\n🎲 Modo INDIVIDUAL ativado")
                self.get_logger().info('Modo: INDIVIDUAL')
                return
            
            # Funções gerais
            elif key == 'v':
                self.show_velocities()
            
            elif key == 'h':
                self.print_instructions()
            
            elif key == 'x':
                print("\nEncerrando...")
                raise KeyboardInterrupt
            
            # Controles por modo
            elif self.control_mode == 'individual':
                self.handle_individual_mode(key)
            
            elif self.control_mode == 'tanque':
                self.handle_tanque_mode(key)
            
            elif self.control_mode == 'virar':
                self.handle_virar_mode(key)
                
        except KeyboardInterrupt:
            raise
    
    def handle_individual_mode(self, key):
        """Controle individual de rodas"""
        if key in ['1', '2', '3', '4']:
            self.selected_wheel = key
            wheel = self.wheels[key]
            print(f"\n✓ Roda Selecionada: [{key}] {wheel['name']}")
            print(f"  Velocidade Atual: {wheel['velocity']:+.2f} rad/s\n")
        
        elif key == 'w':
            wheel = self.wheels[self.selected_wheel]
            wheel['velocity'] = min(wheel['velocity'] + self.velocity_step, self.max_velocity)
            self.print_wheel_status(self.selected_wheel, wheel)
            self.publish_wheel(self.selected_wheel)
        
        elif key == 's':
            wheel = self.wheels[self.selected_wheel]
            wheel['velocity'] = max(wheel['velocity'] - self.velocity_step, -self.max_velocity)
            self.print_wheel_status(self.selected_wheel, wheel)
            self.publish_wheel(self.selected_wheel)
        
        elif key in ['+', '=']:
            for k in self.wheels:
                self.wheels[k]['velocity'] = min(
                    self.wheels[k]['velocity'] + self.velocity_step,
                    self.max_velocity
                )
            print("↑ Aumentando velocidade de TODAS as rodas")
            self.publish_all()
        
        elif key in ['-', '_']:
            for k in self.wheels:
                self.wheels[k]['velocity'] = max(
                    self.wheels[k]['velocity'] - self.velocity_step,
                    -self.max_velocity
                )
            print("↓ Diminuindo velocidade de TODAS as rodas")
            self.publish_all()
        
        elif key == ' ':
            for k in self.wheels:
                self.wheels[k]['velocity'] = 0.0
            print("⏹ PARANDO todas as rodas")
            self.publish_all()
    
    def handle_tanque_mode(self, key):
        """Modo tanque: movimento + virada"""
        if key == 'w':
            # Avançar
            self.tanque_velocity = min(self.tanque_velocity + self.velocity_step, self.max_velocity)
            self.wheels['1']['velocity'] = self.tanque_velocity
            self.wheels['3']['velocity'] = self.tanque_velocity
            self.wheels['2']['velocity'] = self.tanque_velocity
            self.wheels['4']['velocity'] = self.tanque_velocity
            print(f"→ Avançando | Vel: {self.tanque_velocity:+.2f} rad/s")
            self.publish_all()
        
        elif key == 's':
            # Retroceder
            self.tanque_velocity = max(self.tanque_velocity - self.velocity_step, -self.max_velocity)
            self.wheels['1']['velocity'] = self.tanque_velocity
            self.wheels['3']['velocity'] = self.tanque_velocity
            self.wheels['2']['velocity'] = self.tanque_velocity
            self.wheels['4']['velocity'] = self.tanque_velocity
            print(f"← Retrocedendo | Vel: {self.tanque_velocity:+.2f} rad/s")
            self.publish_all()
        
        elif key == 'a':
            # Virar à ESQUERDA (esquerda fica mais lenta)
            esq_vel = self.tanque_velocity * 0.2
            dir_vel = self.tanque_velocity * 1.5
            
            self.wheels['1']['velocity'] = esq_vel
            self.wheels['3']['velocity'] = esq_vel
            self.wheels['2']['velocity'] = dir_vel
            self.wheels['4']['velocity'] = dir_vel
            print(f"↶ Virar à ESQUERDA | Esq: {esq_vel:+.2f} | Dir: {dir_vel:+.2f}")
            self.publish_all()
        
        elif key == 'd':
            # Virar à DIREITA (direita fica mais lenta)
            esq_vel = self.tanque_velocity * 1.5
            dir_vel = self.tanque_velocity * 0.2
            
            self.wheels['1']['velocity'] = esq_vel
            self.wheels['3']['velocity'] = esq_vel
            self.wheels['2']['velocity'] = dir_vel
            self.wheels['4']['velocity'] = dir_vel
            print(f"↷ Virar à DIREITA | Esq: {esq_vel:+.2f} | Dir: {dir_vel:+.2f}")
            self.publish_all()
        
        elif key == 'q':
            # Parar movimento linear
            self.tanque_velocity = 0.0
            self.wheels['1']['velocity'] = 0.0
            self.wheels['3']['velocity'] = 0.0
            self.wheels['2']['velocity'] = 0.0
            self.wheels['4']['velocity'] = 0.0
            print("⏹ PARANDO movimento linear")
            self.publish_all()
        
        elif key == ' ':
            # Parar tudo
            self.tanque_velocity = 0.0
            for k in self.wheels:
                self.wheels[k]['velocity'] = 0.0
            print("⏹ PARANDO completamente")
            self.publish_all()
    
    def handle_virar_mode(self, key):
        """Modo virar no lugar: Direita frente, Esquerda trás (ou inverso)"""
        if key == 'w':
            # Giro horário: Direita frente (2,4), Esquerda trás (1,3)
            self.virar_velocity = min(self.virar_velocity + self.velocity_step, self.max_velocity)
            
            self.wheels['1']['velocity'] = -self.virar_velocity
            self.wheels['3']['velocity'] = -self.virar_velocity
            self.wheels['2']['velocity'] = self.virar_velocity
            self.wheels['4']['velocity'] = self.virar_velocity
            
            print(f"🔄 Girando HORÁRIO (Direita→) | Vel: {self.virar_velocity:+.2f} rad/s")
            self.publish_all()
        
        elif key == 's':
            # Giro anti-horário: Esquerda frente (1,3), Direita trás (2,4)
            self.virar_velocity = min(self.virar_velocity + self.velocity_step, self.max_velocity)
            
            self.wheels['1']['velocity'] = self.virar_velocity
            self.wheels['3']['velocity'] = self.virar_velocity
            self.wheels['2']['velocity'] = -self.virar_velocity
            self.wheels['4']['velocity'] = -self.virar_velocity
            
            print(f"🔄 Girando ANTI-HORÁRIO (←Esquerda) | Vel: {self.virar_velocity:+.2f} rad/s")
            self.publish_all()
        
        elif key == 'a':
            # Aumentar velocidade de giro
            self.virar_velocity = min(self.virar_velocity + self.velocity_step, self.max_velocity)
            
            if self.wheels['2']['velocity'] > 0:
                self.wheels['1']['velocity'] = -self.virar_velocity
                self.wheels['3']['velocity'] = -self.virar_velocity
                self.wheels['2']['velocity'] = self.virar_velocity
                self.wheels['4']['velocity'] = self.virar_velocity
                print(f"↑ Aumentando giro HORÁRIO | Vel: {self.virar_velocity:+.2f} rad/s")
            else:
                self.wheels['1']['velocity'] = self.virar_velocity
                self.wheels['3']['velocity'] = self.virar_velocity
                self.wheels['2']['velocity'] = -self.virar_velocity
                self.wheels['4']['velocity'] = -self.virar_velocity
                print(f"↑ Aumentando giro ANTI-HORÁRIO | Vel: {self.virar_velocity:+.2f} rad/s")
            
            self.publish_all()
        
        elif key == 'd':
            # Diminuir velocidade de giro
            self.virar_velocity = max(self.virar_velocity - self.velocity_step, 0.0)
            
            if self.virar_velocity == 0.0:
                for k in self.wheels:
                    self.wheels[k]['velocity'] = 0.0
                print("⏹ PARANDO")
            else:
                if self.wheels['2']['velocity'] > 0:
                    self.wheels['1']['velocity'] = -self.virar_velocity
                    self.wheels['3']['velocity'] = -self.virar_velocity
                    self.wheels['2']['velocity'] = self.virar_velocity
                    self.wheels['4']['velocity'] = self.virar_velocity
                    print(f"↓ Diminuindo giro HORÁRIO | Vel: {self.virar_velocity:+.2f} rad/s")
                else:
                    self.wheels['1']['velocity'] = self.virar_velocity
                    self.wheels['3']['velocity'] = self.virar_velocity
                    self.wheels['2']['velocity'] = -self.virar_velocity
                    self.wheels['4']['velocity'] = -self.virar_velocity
                    print(f"↓ Diminuindo giro ANTI-HORÁRIO | Vel: {self.virar_velocity:+.2f} rad/s")
            
            self.publish_all()
        
        elif key == ' ':
            for k in self.wheels:
                self.wheels[k]['velocity'] = 0.0
            self.virar_velocity = 0.0
            print("⏹ PARANDO")
            self.publish_all()
    
    def print_wheel_status(self, key, wheel):
        if wheel['velocity'] > 0:
            direction = "→ FRENTE"
        elif wheel['velocity'] < 0:
            direction = "← TRÁS"
        else:
            direction = "⏹ PARADO"
        
        print(f"  [{key}] {wheel['name']:<30} {direction:<12} {wheel['velocity']:+7.2f} rad/s")
    
    def publish_wheel(self, key):
        msg = Float64()
        msg.data = self.wheels[key]['velocity']
        self.wheel_pubs[key].publish(msg)
    
    def publish_all(self):
        for key in self.wheels:
            msg = Float64()
            msg.data = self.wheels[key]['velocity']
            self.wheel_pubs[key].publish(msg)
    
    def show_velocities(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        
        mode_str = "INDIVIDUAL" if self.control_mode == 'individual' else ("TANQUE" if self.control_mode == 'tanque' else "VIRAR")
        
        print("\n╔" + "═" * 68 + "╗")
        print("║" + f" VELOCIDADES ATUAIS (Mode: {mode_str}) ".center(68) + "║")
        print("╠" + "═" * 68 + "╣")
        
        for key, wheel in self.wheels.items():
            status = "→" if wheel['velocity'] > 0 else ("←" if wheel['velocity'] < 0 else "⏹")
            line = f"  [{key}] {wheel['name']:<30} {status} {wheel['velocity']:+7.2f} rad/s"
            print("║" + line.ljust(68) + "║")
        
        print("╚" + "═" * 68 + "╝\n")
        
        tty.setcbreak(sys.stdin.fileno())
    
    def __del__(self):
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        except:
            pass

def main(args=None):
    rclpy.init(args=args)
    
    try:
        controller = WheelController()
        rclpy.spin(controller)
    except KeyboardInterrupt:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, controller.settings)
        except:
            pass
        print('\n╔═══════════════════════════════╗')
        print('║  Programa Finalizado com ✓    ║')
        print('╚═══════════════════════════════╝\n')
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
