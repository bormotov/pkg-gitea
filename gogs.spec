%global with_bundled 1
%global with_debug 0

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         gogits
%global repo            gogs
# https://github.com/coreos/etcd
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          6bcff7828f117af8d51285ce3acba01a7e40a867
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:		gogs
Version:	0.9.97
Release:	1%{shortcommit}%{?dist}
Summary:	Gogs (Go Git Service) is a painless self-hosted Git service
License:	ASL 2.0
URL:		https://%{provider_prefix}
Source0:	https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
Source1:	%{name}.service
Source2:	%{name}.conf

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{ix86} x86_64 %{arm} aarch64 ppc64le
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  golang
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  sqlite-devel
BuildRequires:  pam-devel
BuildRequires:	systemd
BuildRequires:  git

Requires(pre):	shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Gogs (Go Git Service) is a painless self-hosted Git serviceю

%prep
%setup -q -n %{name}-%{commit}

%build
export GOPATH=$(pwd)/_gopath
export GOBIN=${GOPATH}/bin
export PATH=${PATH}:${GOPATH}/bin
export GO15VENDOREXPERIMENT=1

mkdir -p $GOPATH

git clone -b 0.10.2 https://github.com/Masterminds/glide ${GOPATH}/src/github.com/Masterminds/glide
pushd ${GOPATH}/src/github.com/Masterminds/glide
make build
go install
popd
go get -v github.com/jteeuwen/go-bindata/go-bindata github.com/bradfitz/gomemcache/memcache github.com/go-xorm/builder github.com/jaytaylor/html2text github.com/klauspost/compress/gzip github.com/shurcooL/sanitized_anchor_name gopkg.in/asn1-ber.v1 gopkg.in/redis.v2 github.com/go-macaron/inject
mkdir -p $GOPATH/src/github.com/gogits
ln -s ../../../../ _gopath/src/github.com/gogits/gogs
pushd _gopath/src/github.com/gogits/gogs
glide update && glide install
#go get github.com/codegangsta/cli
sed -i "s|github.com/gogits/gogs/modules/setting.BuildGitHash=.*$|github.com/gogits/gogs/modules/setting.BuildGitHash=%{commit}\"|g" Makefile
#rm -rf _gopath/src/github.com/gogits/gogs/vendor/github.com/codegangsta/cli
sed -i 's|^RUN_MODE = dev|RUN_MODE = prod|g' conf/app.ini
sed -i 's|^STATIC_ROOT_PATH =|STATIC_ROOT_PATH = /usr/share/gogs|g' conf/app.ini
sed -i 's|^LANDING_PAGE = home|LANDING_PAGE = explore|g' conf/app.ini
sed -i 's|^DB_TYPE = mysql|DB_TYPE = sqlite3|g' conf/app.ini
sed -i 's|^DISABLE_REGISTRATION = false|DISABLE_REGISTRATION = true|g' conf/app.ini
sed -i 's|^SHOW_FOOTER_VERSION = true|SHOW_FOOTER_VERSION = false|g' conf/app.ini
sed -i 's|^ROOT_PATH =|ROOT_PATH = /var/log/gogs|g' conf/app.ini
make bindata
make build TAGS="sqlite pam"
popd

%install
mkdir -p %{buildroot}%{_bindir}/
install -D -p -m 0755 gogs %{buildroot}%{_bindir}/
install -D -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
install -m 644 -T %{SOURCE2}  %{buildroot}/%{_sysconfdir}/sysconfig/%{name}
mkdir -p %{buildroot}/%{_datarootdir}/%{name}
cp -r public templates %{buildroot}/%{_datarootdir}/%{name}/
cp -r conf %{buildroot}/%{_sysconfdir}/%{name}/
mkdir -p %{buildroot}/var/log/%{name}
# And create /var/lib/etcd
install -d -m 0755 %{buildroot}%{_sharedstatedir}/%{name}

%pre
getent group git >/dev/null || groupadd -r git
getent passwd git >/dev/null || useradd -r -g git -d %{_sharedstatedir}/%{name} \
	-s /sbin/nologin -c "git user" git

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun %{name}.service

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE
%doc *.md
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_bindir}/%{name}
%config(noreplace) %attr(-,git,git)  %{_sysconfdir}/%{name}
%{_datarootdir}/%{name}/*
%dir /var/log/%{name}
%dir %attr(-,git,git) /var/log/%{name}
%dir %attr(-,git,git) %{_sharedstatedir}/%{name}
%{_unitdir}/%{name}.service

%changelog
* Sun May 15 2016 jchaloup <jchaloup@redhat.com> - 3.0.0-0.1.beta0
- Update to v3.0.0-beta0 (build from bundled until new deps appear in dist-git)
  resolves: #1333988
