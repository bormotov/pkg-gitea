%global with_bundled 1
%global with_debug 0

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         go-gitea
%global repo            gitea
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          f0a989c1d0843ab47a48be5219470a93a462e302
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:		gitea
Version:	0.9.97
Release:	3%{?dist}
Summary:	Gogs (Go Git Service) is a painless self-hosted Git service
License:	MIT
URL:		https://%{provider_prefix}
Source0:	https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
Source1:	%{name}.service
Source2:	%{name}.conf

ExclusiveArch:  %{ix86} x86_64 %{arm} aarch64 ppc64le
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
Gitea: Git with a cup of tea

%prep
%setup -q -n %{name}-%{commit}

%build
export GOPATH=$(pwd)/_gopath
export GOBIN=${GOPATH}/bin
export PATH=${PATH}:${GOPATH}/bin
export GO15VENDOREXPERIMENT=1

mkdir -p $GOPATH/src/code.gitea.io/
ln -s ../../../ _gopath/src/code.gitea.io/gitea
pushd $GOPATH/src/code.gitea.io/gitea
make generate
popd
go get -v -tags "sqlite bindata" code.gitea.io/gitea

%install
mkdir -p %{buildroot}%{_bindir}/
install -D -p -m 0755 _gopath/bin/gitea %{buildroot}%{_bindir}/
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -D -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -D -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -d -m 0755 %{buildroot}%{_sharedstatedir}/%{name}

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
%{_bindir}/%{name}
%dir %attr(-,git,git) %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
#%config(noreplace) %attr(-,git,git)  %{_sysconfdir}/%{name}/%{name}.conf
%dir %attr(-,git,git) %{_sharedstatedir}/%{name}
%{_unitdir}/%{name}.service

%changelog
* Sun May 15 2016 jchaloup <jchaloup@redhat.com> - 3.0.0-0.1.beta0
- Update to v3.0.0-beta0 (build from bundled until new deps appear in dist-git)
  resolves: #1333988
