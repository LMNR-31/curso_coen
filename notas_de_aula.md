# Notas de Aula — ROS 2 Jazzy + Gazebo (GZ)

## 1) Preparação do ambiente

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## 2) Converter URDF para SDF

```bash
cd ~/curso_coen_ws/src/nome_do_robo
gz sdf -p meu_robo.urdf > meu_robo.sdf
```

---

## 3) Trechos importantes no SDF

### Material (aparência visual)

```xml
<material>
  <ambient>0.4 0 0 1</ambient>
  <diffuse>0.85 0 0 1</diffuse>
  <specular>0.3 0.3 0.3 1</specular>
</material>
```

### Plugin de controle de junta

```xml
<plugin filename="gz-sim-joint-controller-system" name="gz::sim::systems::JointController">
  <joint_name>nome_da_junta</joint_name>
  <topic>/nome_do_robo/nome_da_roda_cmd</topic>
</plugin>
```

### Limites da junta

```xml
<effort>20</effort>      <!-- torque máximo -->
<velocity>2.0</velocity> <!-- velocidade máxima -->
```

### Dinâmica da junta

```xml
<damping>0.10</damping>  <!-- amortecimento -->
<friction>0.0</friction> <!-- atrito -->
```

---

## 4) Execução do sistema (3 terminais)

### Terminal 1 — Gazebo

```bash
cd ~/curso_coen_ws/src/nome_do_robo
gz sim worlds/curso_coen_worlds.sdf
```

### Terminal 2 — Bridge (ROS 2 <-> Gazebo)

```bash
ros2 run ros_gz_bridge parameter_bridge \
/modelo_carrinho/roda_frente_direita_cmd@std_msgs/msg/Float64@gz.msgs.Double \
/modelo_carrinho/roda_frente_esquerda_cmd@std_msgs/msg/Float64@gz.msgs.Double \
/modelo_carrinho/roda_traz_direita_cmd@std_msgs/msg/Float64@gz.msgs.Double \
/modelo_carrinho/roda_traz_esquerda_cmd@std_msgs/msg/Float64@gz.msgs.Double
```

### Terminal 3 — Controller

```bash
cd ~/curso_coen_ws
colcon build
source install/setup.bash
ros2 run wheel_robot_controller wheel_controller.py
```

---

## 5) Observações rápidas

- Sempre faça `source /opt/ros/jazzy/setup.bash` antes de compilar/executar.
- Após `colcon build`, rode `source install/setup.bash` no terminal atual.
- Verifique se os nomes das juntas e tópicos no SDF batem com os tópicos da bridge.
- Se algo não responder, confira se os 3 terminais estão ativos e sem erro.




# intalação
```bash
sudo apt install -y ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-sim
```
```bash
sudo apt update
sudo apt install python3-colcon-common-extensions -y
```


