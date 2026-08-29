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
sudo apt update
sudo apt install -y curl

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb \
"https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb

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

# erro 

```bash
sudo apt update
sudo apt upgrade -y
```

```bash 
sudo reboot 
```
