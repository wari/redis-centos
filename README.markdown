# A Recipe for a Redis RPM on CentOS

Perform the following on a build box as root.

## Create an RPM Build Environment

    yum install rpmdevtools
    rpmdev-setuptree

## Install Prerequisites for RPM Creation

    yum groupinstall 'Development Tools'

## Download Redis

    cd ~/rpmbuild/SOURCES
    wget http://redis.googlecode.com/files/redis-2.6.10.tar.gz

## Get Necessary System-specific Configs

    cd ~/rpmbuild/SOURCES
    wget https://raw.github.com/wari/redis-centos/2.6.10/conf/redis.conf 
    cd ~/rpmbuild/SPECS/
    wget https://raw.github.com/wari/redis-centos/2.6.10/spec/redis.spec

## Edit the specfile

You might want to edit the spec file depending on your environment (this one is
set to use id 498 for the redis user, for example)

## Edit the configuration file

Again, if necessary. You might want defaults set up to your liking.

## Build the RPM

    cd ~/rpmbuild/
    rpmbuild -ba SPECS/redis.spec

The resulting RPM will be:

    ~/rpmbuild/RPMS/x86_64/redis-2.6.10-1.x86_64.rpm

## Credits

Based on the `redis.spec` file from Jason Priebe, found on [Google Code][gc].

 [gc]: http://groups.google.com/group/redis-db/files
