#!/bin/bash
FOLDER=$( ls $( cd $( dirname "${BASH_SOURCE[0]}" ) && pwd )/vagrant_run 2> /dev/null)
a=y
if [[ $FOLDER != '' ]]
then
	echo "This is snapshotted - sure you want to continue deleting? (y/n)"
	echo See folder: vagrant_run/${FOLDER}
	read a
fi
if [[ $a != 'y' ]]
then
	echo Refusing to continue
	exit 1
fi
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
if [[ $(command -v VBoxManage) != '' ]]
then
	while true 
	do
		VBoxManage list runningvms | grep shutit_chef_env | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep shutit_chef_env | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep shutit_chef_env | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep shutit_chef_env | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs -n1 virsh destroy
fi
