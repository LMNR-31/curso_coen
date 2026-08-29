# intalação
```bash
sudo apt update
sudo apt upgrade -y

```
```bash
sudo apt install -y software-properties-common curl gnupg
```
```bash
sudo add-apt-repository universe

```
```bash
sudo apt update
```
```bash
sudo apt update
sudo apt install -y curl ca-certificates

```
```bash
sudo curl -L https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg


```
```bash
sudo apt install -y ros-jazzy-desktop

```

```bash
sudo apt install -y ros-dev-tools

```
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc

```
```bash
ros2 --help

```




```bash
sudo apt install -y ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-sim
```
```bash
sudo apt update
sudo apt install python3-colcon-common-extensions -y
```
```bash
sudo apt update
sudo apt install code

```
ou
```bash
sudo apt update
sudo apt install wget gpg
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list
sudo apt update
sudo apt install code
```
abrir
```bash
code
```


