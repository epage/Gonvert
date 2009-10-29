Name:           gonvert
Version:        0.1.9
Release:        0.fdr.1
Epoch:          0
Summary:        Units conversion utility.

Group:          Applications/Engineering
License:        GPL
URL:            http://unihedron.com/projects/gonvert/gonvert.php
Source0:        http://www.unihedron.com/projects/gonvert/downloads/gonvert-0.1.9.tar.gz
Source1:        gonvert.desktop
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  desktop-file-utils
Requires:       python >= 0:2.0
Requires:       pygtk2 >= 0:1.99.0
Requires:       libglade2

BuildArch:      noarch

%description
gonvert is a conversion utility that allows conversion between many units 
like CGS, Ancient, Imperial with many categories like length, mass, numbers, 
etc. All units converted values shown at once as you type. Easy to add/change 
your own units. Written in Python,pygtk,libgade. 



%prep 
%setup



%build 
make %{?_smp_mflags}



%install 
rm -rf ${RPM_BUILD_ROOT}
%makeinstall DESTDIR="${RPM_BUILD_ROOT}"

chmod 0644 doc/*
rm -rf ${RPM_BUILD_ROOT}%{_prefix}/doc

rm ${RPM_BUILD_ROOT}%{_datadir}/gnome/apps/Utilities/gonvert.desktop
desktop-file-install --vendor fedora                    \
  --dir ${RPM_BUILD_ROOT}%{_datadir}/applications       \
  --add-category X-Fedora                               \
  %{SOURCE1}



%clean 
rm -rf ${RPM_BUILD_ROOT}



%files 
%defattr(-,root,root,-) 
%doc doc/*
%attr(0755,root,root) %{_bindir}/*
%{_libdir}/*
%attr(0644,root,root) %{_datadir}/applications/fedora-%{name}.desktop
%attr(0644,root,root) %{_datadir}/pixmaps/*



%changelog
* Thu Feb 05 2004 Phillip Compton <pcompton[AT]proteinmedia.com> - 0:0.1.9-0.fdr.1
- Update to 0.1.9.

* Sun Jan 25 2004 Phillip Compton <pcompton[AT]proteinmedia.com> - 0:0.1.7-0.fdr.1
- Update to 0.1.7.

* Sun Nov 16 2003 Phillip Compton <pcompton[AT]proteinmedia.com> - 0:0.1.6-0.fdr.3
- BuildReq desktop-file-utils.

* Tue Aug 05 2003 Phillip Compton <pcompton[AT]proteinmedia.com> - 0:0.1.6-0.fdr.2
- Corrected file permissions.
- Corrects path of Source0.

* Wed Jul 30 2003 Phillip Compton <pcompton[AT]proteinmedia.com> - 0:0.1.6-0.fdr.1
- Fedorafication.

* Sat Jun 29 2003 Dag Wieers <dag@wieers.com> - 0.1.6-0
- Updated to release 0.1.6.

* Wed Feb 26 2003 Dag Wieers <dag@wieers.com> - 0.1.5-0
- Initial package. (using DAR)
