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
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(run_dir + '/' + module_name + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "chefserver" do |chefserver|    
    chefserver.vm.box = ''' + '"' + vagrant_image + '"' + '''
    chefserver.vm.hostname = "chefserver.vagrant.test"
    chefserver.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", "2048"]
      v.customize ["modifyvm", :id, "--cpus", "2"]
    end     
  end

  config.vm.define "chefworkstation1" do |chefworkstation1|
    chefworkstation1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    chefworkstation1.vm.hostname = "chefworkstation1.vagrant.test"
  end

  config.vm.define "chefnode1" do |chefnode1|
    chefnode1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    chefnode1.vm.hostname = "chefnode1.vagrant.test"
  end
end''')
		pw = shutit.get_env_pass()                                                                                                                                                
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'],{'assword for':pw},timeout=99999)
		except:
			shutit.multisend('vagrant up ',{'assword for':pw},timeout=99999)
		shutit.send('vagrant up --provider virtualbox',timeout=99999)
		machine_names = ('chefnode1','chefworkstation1','chefserver')
		root_pass = 'chef'
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			shutit.send('''sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config''')
			shutit.send('''sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config''')
			shutit.send('service ssh restart')
			shutit.send('echo root:' + root_pass + ' | /usr/sbin/chpasswd')
			shutit.multisend('ssh-keygen',{'Enter file':'','Enter passphrase':'','Enter same pass':''}) 
			shutit.logout()
			shutit.logout()
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			for to_machine in machine_names:
				shutit.multisend('ssh-copy-id root@' + to_machine + '.vagrant.test',{'ontinue connecting':'yes','assword':root_pass})
				shutit.multisend('ssh-copy-id root@' + to_machine,{'ontinue connecting':'yes','assword':root_pass})
			shutit.logout()
			shutit.logout()
			
		shutit.login(command='vagrant ssh chefserver')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('hostname -f',note='Check the hostname is meaningful')
		shutit.send('wget https://packages.chef.io/stable/ubuntu/14.04/chef-server-core_12.11.1-1_amd64.deb',note='Get the chef server package')
		shutit.send('dpkg -i chef-server-core_*.deb',note='Install the package')
		shutit.send('chef-server-ctl reconfigure',note='Set up the chef server on this host')
		shutit.send('chef-server-ctl install chef-manage',note='Install chef manager')
		shutit.send("""chef-server-ctl user-create admin admin admin admin@example.com examplepass -f admin.pem""",note='Create the admin user certificate')
		shutit.send("""chef-server-ctl org-create digitalocean "DigitalOcean, Inc." --association_user admin -f digitalocean-validator.pem""",note='Create the organisation validator certificate')
		admin_pem = shutit.send_and_get_output('cat admin.pem')
#chef-server-ctl install chef-manage
		validator_pem = shutit.send_and_get_output('cat digitalocean-validator.pem')
		shutit.logout()
		shutit.logout()

		shutit.login(command='vagrant ssh chefworkstation1')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('cd /root')
		shutit.send('wget https://packages.chef.io/stable/ubuntu/12.04/chefdk_1.0.3-1_amd64.deb')
		shutit.send('dpkg -i chefdk*deb')
		shutit.install('git')
		shutit.send('git config --global user.name "Your Name"')
		shutit.send('git config --global user.email "username@domain.com"')
		#shutit.send('echo ".chef" >> /root/chef-repo/.gitignore')
		shutit.send('cd /root')
		shutit.send('chef generate repo chef-repo')
		shutit.send('cd /root/chef-repo')
		#shutit.send('git add .')
		#shutit.send('git commit -m "Excluding the ./.chef directory from version control"')
		shutit.send('chef verify')
		shutit.send('''echo 'eval "$(chef shell-init bash)"' >> /root/.bash_profile''')
		shutit.send('source /root/.bash_profile')
		shutit.send('mkdir /root/chef-repo/.chef')
		shutit.send_file('/root/chef-repo/.chef/admin.pem',admin_pem)
		shutit.send_file('/root/chef-repo/.chef/digitalocean-validator.pem',validator_pem)
		# Really annoyingly, node_name is 'admin'?
		knife_rb_file = '''current_dir = File.dirname(__FILE__)
log_level                :info
log_location             STDOUT
node_name                "admin"
client_key               "#{current_dir}/admin.pem"
validation_client_name   "digitalocean-validator"
validation_key           "#{current_dir}/digitalocean-validator.pem"
chef_server_url          "https://chefserver.vagrant.test/organizations/digitalocean"
syntax_check_cache_path  "#{ENV['HOME']}/.chef/syntaxcache"
cookbook_path            ["#{current_dir}/../cookbooks"]'''
		shutit.send_file('/root/chef-repo/.chef/knife.rb',knife_rb_file)
		shutit.send('cd /root/chef-repo')
		shutit.send('knife ssl fetch')
		shutit.send('knife client list')
		shutit.logout()
		shutit.logout()

		shutit.login(command='vagrant ssh chefnode1')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('wget https://packages.chef.io/stable/ubuntu/12.04/chef_12.16.42-1_amd64.deb')
		shutit.send('dpkg -i chef_12.16.42-1_amd64.deb ')
		shutit.send('mkdir .chef')
		shutit.send('cd .chef')
		shutit.send_file('/root/.chef/knife.rb',knife_rb_file)
		shutit.send_file('/root/.chef/admin.pem',admin_pem)
		shutit.send('knife ssl fetch')
		shutit.send('knife bootstrap -N chefnode1 chefnode1')
		shutit.pause_point('node added?')
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
