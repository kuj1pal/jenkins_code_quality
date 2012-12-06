#!/bin/sh
/bin/echo '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ run_analysis.sh ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
# Add ros sources to apt
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $OS_PLATFORM main" > /etc/apt/sources.list.d/ros-latest.list'
wget http://packages.ros.org/ros.key -O $WORKSPACE/ros.key
#apt-key add $WORKSPACE/ros.key
#cp $HOME/chroot_configs/sources.list /etc/apt/sources.list
sudo apt-get update
#wget http://packages.ros.org/ros.key -O - | sudo apt-key add -


# install stuff we need
echo "Installing Debian packages we need for running this script"
sudo apt-get install python-rosinstall python-rospkg python-tk ia32-libs openssh-server ros-electric-ros-base ros-electric-ros-release --yes
rospack find 

source /opt/ros/$ROS_DISTRO/setup.sh
source $HOME/chroot_configs/set_qacpp_path.sh

python analyze.py $ROS_DISTRO $STACK_NAME $WORKSPACE $TEST_DEPENDS_ON
