# shutit-chef-env

A complete Chef environment in Vagrant. 

![ShutIt Chef Env](https://raw.githubusercontent.com/ianmiell/shutit-chef-env/master/shutit-chef-env-1.png)

Includes:

- Chef server
- Chef workstation
- Chef node
- Certificate setup
- Client setup (knife, chef-client etc)

## Pre-requisites

- [Virtualbox](https://www.virtualbox.org/wiki/Downloads)
- [Vagrant](https://www.vagrantup.com)
- [Vagrant landrush plugin](https://github.com/vagrant-landrush/landrush#installation)
- [ShutIt](https://ianmiell.github.io/shutit)

## Run

```
git clone --recursive https://github.com/ianmiell/shutit-chef-env
cd shutit-chef-env
./run.sh
```

## Why?

This can be used for a number of reasons:

- as a training tool for Chef newbies
- to demonstrate how a Chef infrastructure works
- to test Chef code that depends on a Chef server being available

## Video

[![asciicast](https://asciinema.org/a/hkos3EPsTscvN5y7FJnfOliXA.png)](https://asciinema.org/a/hkos3EPsTscvN5y7FJnfOliXA)
