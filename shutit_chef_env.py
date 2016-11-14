import random
import string
import os

from shutit_module import ShutItModule

class shutit_chef_env(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		run_dir = '/space/git/shutit-chef-env/vagrant_run'   
		module_name = 'shutit_chef_env_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('command rm -rf ' + run_dir + '/' + module_name + ' && command mkdir -p ' + run_dir + '/' + module_name + ' && command cd ' + run_dir + '/' + module_name)
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(run_dir + '/' + module_name + '/Vagrantfile','''

Vagrant.configure("2") do |config|
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "master" do |master|    
    master.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master.vm.hostname = "master.local"
    master.vm.network "private_network", ip: "192.168.2.2"
  end

  config.vm.define "slave1" do |slave1|
    slave1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    slave1.vm.network :private_network, ip: "192.168.2.3"
    slave1.vm.hostname = "slave1.local"
  end

  config.vm.define "slave2" do |slave2|
    slave2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    slave2.vm.network :private_network, ip: "192.168.2.4"
    slave2.vm.hostname = "slave2.local"
  end
end''')
		shutit.send('vagrant up --provider virtualbox',timeout=99999)
		shutit.login(command='vagrant ssh master')
		shutit.login(command='sudo su -',password='vagrant')

		shutit.send(INSTALL CHEF)
		shutit.send('chef-server-ctl reconfigure')
		shutit.send("""chef-server-ctl user-create kramer Cosmo Kramer 'kramer@test.com' --filename /root/kramer.pem""")
		shutit.send("""chef-server-ctl org-create short_name 'Kramerica Enterprises' --association_user kramer --filename kramerica-validator.pem""")

		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')

		return True

	def test(self, shutit):

		return True

	def finalize(self, shutit):

		return True

	def isinstalled(self, shutit):

		return False

	def start(self, shutit):

		return True

	def stop(self, shutit):

		return True

def module():
	return shutit_chef_env(
		'cookbook-openshift3.shutit_chef_env.shutit_chef_env', 1355141237.0001,   
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
	)
