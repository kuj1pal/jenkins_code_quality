#!/bin/sh -ex

# Add ros sources to apt
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $OS_PLATFORM main" > /etc/apt/sources.list.d/ros-latest.list'
wget http://packages.ros.org/ros.key -O $WORKSPACE/ros.key
apt-key add $WORKSPACE/ros.key
sudo apt-get update

# install stuff we need
echo "Installing Debian packages we need for running this script"
sudo apt-get install -y \
         python-rosinstall python-rospkg python-tk \
         ia32-libs openssh-server \
         ros-electric-ros-base ros-electric-ros-release

source /opt/ros/$ROS_DISTRO/setup.sh
source $HOME/chroot_configs/set_qacpp_path.sh

python analyze.py $ROS_DISTRO $STACK_NAME $WORKSPACE $TEST_DEPENDS_ON