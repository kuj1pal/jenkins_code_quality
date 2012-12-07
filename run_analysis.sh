#!/bin/bash
/bin/echo '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ run_analysis.sh ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'

# Add ros sources to apt
#sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu '$OS_PLATFORM' main" > /etc/apt/sources.list.d/ros-latest.list'
#wget http://packages.ros.org/ros.key -O $WORKSPACE/ros.key
#apt-key add $WORKSPACE/ros.key
#sudo apt-get update

##
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu lucid main" > /etc/apt/sources.list.d/ros-latest.list'
wget http://packages.ros.org/ros.key -O - | sudo apt-key add -
sudo apt-get update
sudo apt-get install ros-electric-desktop-full --yes
##

# install stuff we need
echo "Installing Debian packages we need for running this script"
sudo apt-get install apt-utils ia32-libs python-rosinstall python-rospkg python-tk openssh-server ros-electric-ros-base ros-electric-ros-release --yes
#ros-electric-ros-base

source /opt/ros/$ROS_DISTRO/setup.sh
source $HOME/chroot_configs/set_qacpp_path.sh

sudo cp $HOME/chroot_configs/rostoolchain.cmake /opt/ros/$ROS_DISTRO/ros/rostoolchain.cmake
#sudo cp $HOME/chroot_configs/source.list /etc/apt/source.list

# call analysis
python $WORKSPACE/jenkins_code_quality/analyze.py $ROS_DISTRO $STACK_NAME
