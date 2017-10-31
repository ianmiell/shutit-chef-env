import random
import string
import os

from shutit_module import ShutItModule

class shutit_chef_env(ShutItModule):

	def build(self, shutit):
		# Collect the config.
		# Some of these are used in jinja templates, so don't assume they are
		# unused if not referenced in this file.
		vagrant_image    = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui              = shutit.cfg[self.module_id]['gui']
		memory           = shutit.cfg[self.module_id]['memory']

		# Set up run dir and runtime module_name.
		module_name = 'shutit_chef_env_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		run_dir     = '/space/git/shutit-chef-env/vagrant_run'
		shutit.send('command rm -rf ' + run_dir + '/' + module_name + ' && command mkdir -p ' + run_dir + '/' + module_name + ' && command cd ' + run_dir + '/' + module_name)

		# Check we have vagrant landrush plugin.
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')

		# Set machine names.
		machine_names = ('chefnode1','chefworkstation','chefserver')
		# Set up Vagarantfile.
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
      v.customize ["modifyvm", :id, "--memory", "1024"]
      v.customize ["modifyvm", :id, "--memory", "1024"]
    end
  end
  config.vm.define "chefworkstation" do |chefworkstation|
    chefworkstation.vm.box = ''' + '"' + vagrant_image + '"' + '''
    chefworkstation.vm.hostname = "chefworkstation.vagrant.test"
    chefworkstation.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", "512"]
    end
  end
  config.vm.define "chefnode1" do |chefnode1|
    chefnode1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    chefnode1.vm.hostname = "chefnode1.vagrant.test"
    chefnode1.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", "512"]
    end
  end
end''')

		# Try and pick up sudo password from 'secret' file (which is gitignored).
		try:
			pw = open('secret').read().strip()
		except:
			pw = shutit.get_env_pass()

		# Bring vagrant machines up
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'],{'assword for':pw},timeout=99999)
		except:
			shutit.multisend('vagrant up ',{'assword for':pw},timeout=99999)
		shutit.send('vagrant up --provider virtualbox',timeout=99999)

		# root password will be 'chef'
		root_pass = 'chef'
		# Go on each machine, escalate to root and set up ssh so we can move between hosts.
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			shutit.send(r'''sed -i 's/^\(127.0.0.1[ \t]*[^ \t]*\).*/\1/' /etc/hosts''')
			shutit.send('wget -qO- https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh | sh')
			shutit.send('''sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config''')
			shutit.send('''sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config''')
			shutit.send('service sshd restart')
			shutit.send('echo root:' + root_pass + ' | /usr/sbin/chpasswd')
			shutit.multisend('ssh-keygen',{'Enter file':'','Enter passphrase':'','Enter same pass':''})
			shutit.logout()
			shutit.logout()

		# Go on each machine and copy ssh ids so we can move between hosts without passwords.
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			for to_machine in machine_names:
				shutit.multisend('ssh-copy-id root@' + to_machine + '.vagrant.test',{'ontinue connecting':'yes','assword':root_pass})
				shutit.multisend('ssh-copy-id root@' + to_machine,{'ontinue connecting':'yes','assword':root_pass})
			shutit.logout()
			shutit.logout()

		# Set up Chef server.
		shutit.login(command='vagrant ssh chefserver')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.install('chef-server-webui')
		# Get and install chef server deb.
		shutit.send('wget -q https://github.com/ianmiell/shutit-chef-env/raw/master/chef-server-core_12.16.14-1_amd64.deb.xaa')
		shutit.send('wget -q https://github.com/ianmiell/shutit-chef-env/raw/master/chef-server-core_12.16.14-1_amd64.deb.xab')
		shutit.send('cat chef-server-core_12.16.14-1_amd64.deb.xaa chef-server-core_12.16.14-1_amd64.deb.xab > chef-server-core_12.16.14-1_amd64.deb && rm *xaa *xab')
		shutit.send('dpkg -i chef-server-core_*.deb',note='Install the package')
		# Set up chef.
		shutit.send('chef-server-ctl reconfigure',note='Set up the chef server on this host')
		shutit.send('chef-server-ctl install chef-manage',note='Install chef manager')
		# Create certificates. 
		shutit.send('chef-server-ctl user-create admin admin admin admin@example.com examplepass -f admin.pem',note='Create the admin user certificate')
		shutit.send('chef-server-ctl org-create mycorp "MyCorp" --association_user admin -f mycorp-validator.pem',note='Create the organisation validator certificate')
		# Put certificates in memory.
		admin_pem = shutit.send_and_get_output('cat admin.pem')
#chef-server-ctl install chef-manage
		validator_pem = shutit.send_and_get_output('cat mycorp-validator.pem')
		shutit.logout()
		shutit.logout()

		# Store the knife.rb file contents.
		knife_rb_file = '''current_dir = File.dirname(__FILE__)
log_level                :info
log_location             STDOUT
node_name                "admin"
client_key               "#{current_dir}/admin.pem"
validation_client_name   "mycorp-validator"
validation_key           "#{current_dir}/mycorp-validator.pem"
chef_server_url          "https://chefserver.vagrant.test/organizations/mycorp"
syntax_check_cache_path  "#{ENV['HOME']}/.chef/syntaxcache"
cookbook_path            ["#{current_dir}/../cookbooks"]'''

		# Set up Chef workstation.
		shutit.login(command='vagrant ssh chefworkstation')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('wget -q https://packages.chef.io/stable/ubuntu/12.04/chefdk_1.0.3-1_amd64.deb && dpkg -i chefdk*deb && rm -f chefdk*deb')
		shutit.send('mkdir -p /root/.chef')
		shutit.send_file('/root/.chef/knife.rb',knife_rb_file)
		shutit.send_file('/root/.chef/admin.pem',admin_pem)
		# Verify the chef install.
		shutit.send('chef verify')
		shutit.send('knife ssl fetch')
		shutit.send('''echo 'eval "$(chef shell-init bash)"' >> /root/.bash_profile''')
		# Generate a skeleton chef repo to upload.
		shutit.send('chef generate app chef-repo')
		shutit.send("""echo 'export PATH="/opt/chefdk/embedded/bin:$PATH"' >> ~/.configuration_file && source ~/.configuration_file""")
		# Add (commented out) debug tool. See: http://jtimberman.housepub.org/blog/2015/09/01/quick-tip-alternative-chef-shell-with-pry/
		shutit.send('''echo "#require 'pry'
#binding.pry" >> /root/chef-repo/cookbooks/chef-repo/recipes/default.rb''')
		# Upload the generated cookbook
		shutit.send('knife cookbook upload chef-repo -o /root/chef-repo/cookbooks')
		shutit.logout()
		shutit.logout()

		# Set up Chef node and bootstrap node.
		shutit.login(command='vagrant ssh chefnode1')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('wget -q https://packages.chef.io/stable/ubuntu/12.04/chef_12.16.42-1_amd64.deb && dpkg -i chef_12.16.42-1_amd64.deb && rm -f chef_12.16.42-1_amd64.deb')
		shutit.send('mkdir .chef')
		shutit.send_file('/root/.chef/knife.rb',knife_rb_file)
		shutit.send_file('/root/.chef/admin.pem',admin_pem)
		shutit.send('knife ssl fetch')
		shutit.send('knife bootstrap -N chefnode1.vagrant.test chefnode1.vagrant.test')
		shutit.logout()
		shutit.logout()

		# Assign the repo to the node using knife.
		shutit.login(command='vagrant ssh chefworkstation')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('knife node run_list add chefnode1.vagrant.test chef-repo')
		shutit.logout()
		shutit.logout()
		
		# Go to the node and run chef-client.
		shutit.login(command='vagrant ssh chefnode1')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('chef-client')
		shutit.logout()
		shutit.logout()

		for machine in machine_names:
			shutit.send('vagrant snapshot save ' + machine,note='Snapshot the vagrant machine')

		shutit.pause_point('********************************************************************************\n\nYou are on the host.\n\nThe chef node is chefnode1.vagrant.test\n\nThe chef workstation is chefworkstation.vagrant.test\n\nThe chef server is chefserver.vagrant.test\n\n********************************************************************************')

		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/xenial64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
		return True

def module():
	return shutit_chef_env(
		'cookbook-openshift3.shutit_chef_env.shutit_chef_env', 1355141237.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
	)
