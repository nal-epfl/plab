# plab.py

This is a script that automates operations on PlanetLab, such as getting a list of all nodes that are up,
adding nodes to your project, copying files to/from all nodes etc.

Run `./plab.py --help` for more info.

# PlanetLab quickstart

## Accessing PlanetLab

### Slice
Each project running on PlanetLab is associated to a "slice", which is essentially a username for shell access to the network. Slices can be created only by the Principal Investigator of an institution which is part of PlanetLab, using the web interface of PlanetLab.

When creating the slice, one or more PlanetLab users which are members of the institution can be given access to it. Users should then add their public SSH keys to the slice, using the web interface.

### Virtual machines
To access a PlanetLab node, you first need to add your slice to it. This can be done either from the web interface, or from command line (e.g. using the python API). The result is a "sliver", a virtual machine.

Afterwards, you can SSH ino the virtual machine using the slice name as username and the private SSH key for authentication.

## Setting up the virtual machine
### Fixing the repositories
As of December 2014, repositories used by the virtual machines have a broken URL.
To fix them, first run `sudo su` and then use `vi` to edit the following files so that they have the following content:

Edit `/etc/yum.repos.d/fedora.repo`:

```
[fedora]
name=Fedora $releasever - $basearch
failovermethod=priority
baseurl=http://archives.fedoraproject.org/pub/archive/fedora/linux/releases/$releasever/Everything/$basearch/os/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-$releasever&arch=$basearch
enabled=1
metadata_expire=7d
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch

[fedora-debuginfo]
name=Fedora $releasever - $basearch - Debug
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/releases/$releasever/Everything/$basearch/debug/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-debug-$releasever&arch=$basearch
enabled=0
metadata_expire=7d
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch

[fedora-source]
name=Fedora $releasever - Source
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/releases/$releasever/Everything/source/SRPMS/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=fedora-source-$releasever&arch=$basearch
enabled=0
metadata_expire=7d
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch
Edit /etc/yum.repos.d/fedora-updates.repo:

[updates]
name=Fedora $releasever - $basearch - Updates
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/updates/$releasever/$basearch/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f$releasever&arch=$basearch
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch

[updates-debuginfo]
name=Fedora $releasever - $basearch - Updates - Debug
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/updates/$releasever/$basearch/debug/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-released-debug-f$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch

[updates-source]
name=Fedora $releasever - Updates Source
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/updates/$releasever/SRPMS/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-released-source-f$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch
Edit /etc/yum.repos.d/fedora-updates-testing.repo:

[updates-testing]
name=Fedora $releasever - $basearch - Test Updates
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/updates/testing/$releasever/$basearch/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-testing-f$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch

[updates-testing-debuginfo]
name=Fedora $releasever - $basearch - Test Updates Debug
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/updates/testing/$releasever/$basearch/debug/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-testing-debug-f$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch

[updates-testing-source]
name=Fedora $releasever - Test Updates Source
failovermethod=priority
baseurl=http://archive.fedoraproject.org/pub/archive/fedora/linux/updates/testing/$releasever/SRPMS/
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=updates-testing-source-f$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$basearch
```

### Updating the system

```
yum update
```

### Installing development tools
```
yum install -y gcc gcc-c++ make python
```
