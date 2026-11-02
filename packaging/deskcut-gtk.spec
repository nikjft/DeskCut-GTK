Name:           deskcut-gtk
Version:        2.0.0
Release:        1%{?dist}
Summary:        Create and edit desktop shortcuts
License:        GPL-2.0-only
URL:            https://github.com/nikjft/DeskCut-GTK
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  make
BuildRequires:  desktop-file-utils
Requires:       python3-gobject
Requires:       gtk4 >= 4.10
Requires:       libadwaita >= 1.4
Requires:       hicolor-icon-theme

%description
DeskCut-GTK creates and edits .desktop launchers with a native GTK4 and
libadwaita interface: set a name, description, path and categories, and
choose an icon by pasting, dropping, cropping, or picking from your icon
theme. Existing shortcuts can be opened and edited without losing the keys
DeskCut does not manage.

%prep
%autosetup

%build

%install
make install PREFIX=%{_prefix} DESTDIR=%{buildroot}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.nikjft.DeskCutGTK.desktop

%files
%license LICENSE
%doc README.md
%{_bindir}/deskcut-gtk
%{_datadir}/deskcut-gtk/
%{_datadir}/applications/io.github.nikjft.DeskCutGTK.desktop
%{_datadir}/icons/hicolor/*/apps/io.github.nikjft.DeskCutGTK.png

%changelog
* Sun Nov 01 2026 nikjft <nik@inik.net> - 2.0.0-1
- Rewrite as a native GTK4/libadwaita application
