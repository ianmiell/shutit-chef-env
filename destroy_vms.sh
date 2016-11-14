
#!/bin/bash
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