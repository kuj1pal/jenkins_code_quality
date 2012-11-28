#!/usr/bin/env python
import os
import sys
import subprocess
import string
import fnmatch
import shutil
import optparse
from common import *
from time import sleep
#
import roslib; roslib.load_manifest("job_generation")
from roslib import stack_manifest
import rosdistro
from jobs_common import *
from apt_parser import parse_apt
import traceback
#

def remove(list1, list2):
    for l in list2:
        if l in list1:
            list1.remove(l)
#

def analyze(ros_distro, stack_name, workspace, test_depends_on):
    print "Testing on distro %s"%ros_distro
    print "Testing stack %s"%stack_name

    distro = rosdistro.Distro(get_rosdistro_file(ros_distro))


    STACK_DIR = 'stack_overlay'
    DEPENDS_DIR = 'depends_overlay'
    DEPENDS_ON_DIR = 'depends_on_overlay'

    # global try
    try:

        # set environment
        attr = []
        attr.append('32')
      
	print "Setting up environment"
        env = get_environment()
	env['INSTALL_DIR'] = os.getcwd()
	os.environ['WORKSPACE'] = env['INSTALL_DIR'] + '/build/' + stack_name
	env['ROS_PACKAGE_PATH'] = '%s:%s:%s:/opt/ros/%s/stacks:/home/user/el_workspace'%(env['INSTALL_DIR']+'/'+STACK_DIR + '/' + stack_name,
                                                                 env['INSTALL_DIR']+'/'+DEPENDS_DIR,
                                                                 env['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                                                 ros_distro)
	print "<<<<<%s"%(env['ROS_PACKAGE_PATH'])
        # return

        if 'ros' in stack_name:
            env['ROS_ROOT'] = env['INSTALL_DIR']+'/'+STACK_DIR+'/ros'
            print "We're building ROS, so setting the ROS_ROOT to %s"%(env['ROS_ROOT'])
	else:
            env['ROS_ROOT'] = '/opt/ros/%s/ros'%ros_distro
        env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
        env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(ros_distro, os.environ['PATH'])
        print "Environment set to %s"%str(env)
	
        # Parse distro file
        rosdistro_obj = rosdistro.Distro(get_rosdistro_file(ros_distro))
        print 'Operating on ROS distro %s'%rosdistro_obj.release_name
	
        # Install the stacks to test from source
	call('echo -e "\033[33;33m Color Text"', env,
        'Set output-color for installing to yellow')
        print 'Installing the stacks to test from source'
        rosinstall_file = '%s.rosinstall'%STACK_DIR
	
        if os.path.exists(rosinstall_file):
            os.remove(rosinstall_file)
        
	if os.path.exists('%s/.rosinstall'%STACK_DIR):
            os.remove('%s/.rosinstall'%STACK_DIR)
        rosinstall = ''
	
        #for stack in stack_name:
	print 'stack: %s'%(stack_name)
	print 'Installing all stacks of ros distro %s: %s'%(ros_distro, str(rosdistro_obj.stacks.keys()))	    
	print 'rosdistro_obj.stacks[stack_name]: %s'%(str(rosdistro_obj.stacks[stack_name]))
        rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack_name], 'devel')
        print 'Generating rosinstall file [%s]'%(rosinstall_file)
        print 'Contents:\n\n'+rosinstall+'\n\n'
        with open(rosinstall_file, 'w') as f:
            f.write(rosinstall)
            print 'rosinstall file [%s] generated'%(rosinstall_file) 
	call('rosinstall --rosdep-yes %s /opt/ros/%s %s'%(STACK_DIR, ros_distro, rosinstall_file), env,
             'Install the stacks to test from source.')
	

        # get all stack dependencies of stacks we're testing
        print "Computing dependencies of stacks we're testing"
        depends_all = []
		
        #for stack in stack_name:    
        stack_xml = '%s/%s/stack.xml'%(STACK_DIR, stack_name)
        call('ls %s'%stack_xml, env, 'Checking if stack %s contains "stack.xml" file'%stack_name)
	 		
        with open(stack_xml) as stack_file:
            depends_one = [str(d) for d in stack_manifest.parse(stack_file.read()).depends]  # convert to list
            print 'Dependencies of stack %s: %s'%(stack_name, str(depends_one))
            for d in depends_one:
                if not d in stack_name and not d in depends_all:
                    print 'Adding dependencies of stack %s'%d
                    get_depends_all(rosdistro_obj, d, depends_all)
                    print 'Resulting total dependencies of all stacks that get tested: %s'%str(depends_all)
	   
        if len(depends_all) > 0:
	    # Install Debian packages of stack dependencies
            print 'Installing debian packages of %s dependencies: %s'%(stack_name, str(depends_all))
            call('sudo apt-get update', env)
            call('sudo apt-get install %s --yes'%(stacks_to_debs(depends_all, ros_distro)), env)
	else:
            print 'Stack(s) %s do(es) not have any dependencies, not installing anything now'%str(stack_name)
	   

	# Install system dependencies of stacks we're testing
        print "Installing system dependencies of stacks we're testing"
        call('rosmake rosdep', env)
        #for stack in stack_name:
        call('rosdep install -y %s'%stack_name, env,
             'Install system dependencies of stack %s'%stack_name)
	
        # Run hudson helper for stacks only
	call('echo -e "\033[33;34m Color Text"', env,
             'Set color from build-output to blue')        
	print "Running Hudson Helper for stacks we're testing"
        res = 0

	       
	#for r in range(0, int(options.repeat)+1):
	for r in range(0, int(0)+1):
	    env['ROS_TEST_RESULTS_DIR'] = env['ROS_TEST_RESULTS_DIR'] + '/' + STACK_DIR + '_run_' + str(r)
	    helper = subprocess.Popen(('./build_helper.py --dir %s build'%(STACK_DIR + '/' + stack_name)).split(' '), env=env)
            helper.communicate()
	    if helper.returncode != 0:
                res = helper.returncode
     
            # concatenate filelists
            call('echo -e "\033[33;0m Color Text"', env,
             'Set color to white')
	    stack_dir = STACK_DIR + '/' + str(stack_name)
            filelist = stack_dir + '/filelist.lst'
            helper = subprocess.Popen(('./concatenate_filelists.py --dir %s --filelist %s'%(stack_dir, filelist)).split(' '), env=env)
            helper.communicate()
            print 'Concatenate filelists done --> %s'%str(stack_name) 
             
            # run cma
            cmaf = stack_dir + '/' + str(stack_name)
            helper = subprocess.Popen(('pal QACPP -cmaf %s -list %s'%(cmaf, filelist)).split(' '), env=env)
            helper.communicate()
            print 'CMA analysis done --> %s'%str(stack_name)  

            # export metrics to yaml and csv files
	    print 'stack_dir: %s '%str(stack_dir)
	    print 'stack_name[0]: %s '%str(stack_name)
            helper = subprocess.Popen(('./export_metrics_to_yaml.py --path %s --doc doc --csv csv --config export_config.yaml'%(stack_dir)).split(' '), env=env)
            helper.communicate()
	    call('echo -e "\033[33;0m Color Text"', env,
             'Set color to white')
            print 'Export metrics to yaml and csv files done --> %s'%str(stack_name)             
            print 'Analysis of stack %s done'%str(stack_name)
	if res != 0:
            return res


    # global except
    except Exception, ex:
        print "Global exception caught."
        print "%s. Check the console output for test failure details."%ex
        traceback.print_exc(file=sys.stdout)
        raise ex


def main():
    parser = optparse.OptionParser()
    parser.add_option("--depends_on", action="store_true", default=False)
    (options, args) = parser.parse_args()

    if len(args) <= 1 or len(args)>=3:
        print "Usage: %s ros_distro  stack_name "%sys.argv[0]
    	print " - with ros_distro the name of the ros distribution (e.g. 'electric' or 'fuerte')"
        print " - with stack_name the name of the stack you want to analyze"
        raise BuildException("Wrong arguments for analyze script")

    ros_distro = args[0]
    stack_name = args[1]
    workspace = os.environ['WORKSPACE']

    print "Running code_quality_stack on distro %s and stack %s"%(ros_distro, stack_name)
    res = analyze(ros_distro, stack_name, workspace, test_depends_on=options.depends_on)
    if res != 0:
        return res



if __name__ == '__main__':
    # global try
    try:
        res = main()
        print res
        if res != 0:
            raise ex
        print "analyze script finished cleanly"

    # global catch
    except BuildException as ex:
        print ex.msg

    except Exception as ex:
        print "analyze script failed. Check out the console output above for details."
        raise ex