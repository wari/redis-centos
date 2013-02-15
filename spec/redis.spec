%define pid_dir %{_localstatedir}/run/redis
%define pid_file %{pid_dir}/redis.pid

Summary: redis
Name: redis
Version: 2.6.10
Release: stable
License: BSD
Group: Applications/Multimedia
URL: http://code.google.com/p/redis/

Source0: redis-%{version}.tar.gz
Source1: redis.conf

BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: gcc, make
Requires(post): /sbin/chkconfig /usr/sbin/useradd
Requires(preun): /sbin/chkconfig, /sbin/service
Requires(postun): /sbin/service
Provides: redis

Packager: Jason Priebe <jpriebe@cbcnewmedia.com>

%description
Redis is an open source, BSD licensed, advanced key-value store. It is often
referred to as a data structure server since keys can contain strings, hashes,
lists, sets and sorted sets.

You can run atomic operations on these types, like appending to a string;
incrementing the value in a hash; pushing to a list; computing set
intersection, union and difference; or getting the member with highest ranking
in a sorted set.

In order to achieve its outstanding performance, Redis works with an in-memory
dataset. Depending on your use case, you can persist it either by dumping the
dataset to disk every once in a while, or by appending each command to a log.

Redis also supports trivial-to-setup master-slave replication, with very fast
non-blocking first synchronization, auto-reconnection on net split and so
forth.

Other features include Transactions, Pub/Bub, Lua scripting, Keys with a
limited time-to-live, and configuration settings to make Redis behave like a
cache.

You can use Redis from most programming languages out there.

Redis is written in ANSI C and works in most POSIX systems like Linux, *BSD, OS
X without external dependencies. Linux and OSX are the two operating systems
where Redis is developed and more tested, and we recommend using Linux for
deploying.

%prep
%setup

%{__cat} <<EOF >redis.logrotate
%{_localstatedir}/redis/*log {
    missingok
}
EOF

%{__cat} <<'EOF' >redis.sysv
#!/bin/bash
#
# Init file for redis
#
# Written by Jason Priebe <jpriebe@cbcnewmedia.com>
#
# chkconfig: - 80 12
# description: A persistent key-value database with network interface
# processname: redis-server
# config: /etc/redis.conf
# pidfile: %{pidfile}

source %{_sysconfdir}/init.d/functions

RETVAL=0
prog="redis-server"

start() {
    PID=`cat /var/run/redis.pid 2>/dev/null`
    checkpid $PID
    PIDCHECK=$?
    if [ "$PIDCHECK" -eq 1 ]; then
        if [ -e /var/run/redis.pid ]; then
            rm -f /var/run/redis.pid
        fi
        echo -n $"Starting $prog: "
        daemon --user redis --pidfile /var/run/redis.pid /usr/sbin/$prog /etc/redis.conf
        RETVAL=$?
        echo
        [ $RETVAL -eq 0 ] && touch /var/lock/subsys/$prog && pgrep redis-server > /var/run/redis.pid
        return $RETVAL
    else
        echo "Service already running"
        return 0
    fi
}

stop() {
    PID=`cat /var/run/redis.pid 2>/dev/null`
    checkpid $PID
    PIDCHECK=$?
    if [ "$PIDCHECK" -eq 1 ]; then
        echo -n $"$prog is not running"
        echo_failure
        RETVAL=1
    else
        echo "Shutdown may take a while; redis needs to save the entire database";
        echo -n $"Shutting down $prog: "
        /usr/bin/redis-cli shutdown
        if checkpid $PID 2>&1; then
            echo_failure
            RETVAL=1
        else
            rm -f /var/lib/redis/temp*rdb
            rm -f /var/lock/subsys/$prog
            rm -f /var/run/redis.pid
            echo_success
            RETVAL=0
        fi
    fi

    echo
    return $RETVAL
}

restart() {
  stop
  start
}

condrestart() {
    [-e /var/lock/subsys/$prog] && restart || :
}

case "$1" in
  start)
  start
  ;;
  stop)
  stop
  ;;
  status)
  status -p %{pid_file} $prog
  RETVAL=$?
  ;;
  restart)
  restart
  ;;
  condrestart|try-restart)
  condrestart
  ;;
   *)
  echo $"Usage: $0 {start|stop|status|restart|condrestart}"
  RETVAL=1
esac

exit $RETVAL
EOF


%build
%{__make}

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
%{__install} -Dp -m 0755 src/redis-server %{buildroot}%{_sbindir}/redis-server
%{__install} -Dp -m 0755 src/redis-benchmark %{buildroot}%{_bindir}/redis-benchmark
%{__install} -Dp -m 0755 src/redis-cli %{buildroot}%{_bindir}/redis-cli

%{__install} -Dp -m 0755 redis.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/redis
%{__install} -Dp -m 0755 redis.sysv %{buildroot}%{_sysconfdir}/init.d/redis
%{__install} -Dp -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/redis.conf

%{__install} -p -d -m 0755 %{buildroot}%{_localstatedir}/lib/redis
%{__install} -p -d -m 0755 %{buildroot}%{_localstatedir}/log/redis
%{__install} -p -d -m 0755 %{buildroot}%{pid_dir}

%pre
/usr/sbin/useradd -c 'Redis' -u 498 -s /bin/false -r -d %{_localstatedir}/lib/redis redis 2> /dev/null || :
mkdir /var/redis
/bin/chown redis /var/redis

%preun
if [ $1 = 0 ]; then
    # make sure redis service is not running before uninstalling

    # when the preun section is run, we've got stdin attached.  If we
    # call stop() in the redis init script, it will pass stdin along to
    # the redis-cli script; this will cause redis-cli to read an extraneous
    # argument, and the redis-cli shutdown will fail due to the wrong number
    # of arguments.  So we do this little bit of magic to reconnect stdin
    # to the terminal
    term="/dev/$(ps -p$$ --no-heading | awk '{print $2}')"
    exec < $term

    /sbin/service redis stop > /dev/null 2>&1 || :
    /sbin/chkconfig --del redis
fi

%post
/sbin/chkconfig --add redis
/sbin/service redis start

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%{_sbindir}/redis-server
%{_bindir}/redis-benchmark
%{_bindir}/redis-cli
%{_sysconfdir}/init.d/redis
%config(noreplace) %{_sysconfdir}/redis.conf
%{_sysconfdir}/logrotate.d/redis
%dir %attr(0770,redis,redis) %{_localstatedir}/lib/redis
%dir %attr(0755,redis,redis) %{_localstatedir}/log/redis
%dir %attr(0755,redis,redis) %{_localstatedir}/run/redis

%changelog
* Fri Feb 15 2013 - Wari Wahab <wari@celestix.com>
- Updated to 2.6.10

* Tue Jul 13 2010 - jay at causes dot com 2.0.0-rc2
- upped to 2.0.0-rc2

* Mon May 24 2010 - jay at causes dot com 1.3.9-2
- moved pidfile back to /var/run/redis/redis.pid, so the redis
  user can write to the pidfile.
- Factored it out into %{pid_dir} (/var/run/redis), and
  %{pid_file} (%{pid_dir}/redis.pid)


* Wed May 05 2010 - brad at causes dot com 1.3.9-1
- redis updated to version 1.3.9 (development release from GitHub)
- extract config file from spec file
- move pid file from /var/run/redis/redis.pid to just /var/run/redis.pid
- move init file to /etc/init.d/ instead of /etc/rc.d/init.d/

* Fri Sep 11 2009 - jpriebe at cbcnewmedia dot com 1.0-1
- redis updated to version 1.0 stable

* Mon Jun 01 2009 - jpriebe at cbcnewmedia dot com 0.100-1
- Massive redis changes in moving from 0.09x to 0.100
- removed log timestamp patch; this feature is now part of standard release

* Tue May 12 2009 - jpriebe at cbcnewmedia dot com 0.096-1
- A memory leak when passing more than 16 arguments to a command (including
  itself).
- A memory leak when loading compressed objects from disk is now fixed.

* Mon May 04 2009 - jpriebe at cbcnewmedia dot com 0.094-2
- Patch: applied patch to add timestamp to the log messages
- moved redis-server to /usr/sbin
- set %config(noreplace) on redis.conf to prevent config file overwrites
  on upgrade

* Fri May 01 2009 - jpriebe at cbcnewmedia dot com 0.094-1
- Bugfix: 32bit integer overflow bug; there was a problem with datasets
  consisting of more than 20,000,000 keys resulting in a lot of CPU usage
  for iterated hash table resizing.

* Wed Apr 29 2009 - jpriebe at cbcnewmedia dot com 0.093-2
- added message to init.d script to warn user that shutdown may take a while

* Wed Apr 29 2009 - jpriebe at cbcnewmedia dot com 0.093-1
- version 0.093: fixed bug in save that would cause a crash
- version 0.092: fix for bug in RANDOMKEY command

* Fri Apr 24 2009 - jpriebe at cbcnewmedia dot com 0.091-3
- change permissions on /var/log/redis and /var/run/redis to 755; this allows
  non-root users to check the service status and to read the logs

* Wed Apr 22 2009 - jpriebe at cbcnewmedia dot com 0.091-2
- cleanup of temp*rdb files in /var/lib/redis after shutdown
- better handling of pid file, especially with status

* Tue Apr 14 2009 - jpriebe at cbcnewmedia dot com 0.091-1
- Initial release.
