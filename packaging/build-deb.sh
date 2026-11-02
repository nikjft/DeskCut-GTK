#!/bin/sh
# Build a .deb from the source tree: packaging/build-deb.sh VERSION [OUTDIR]
set -eu

VERSION="${1:?usage: build-deb.sh VERSION [OUTDIR]}"
OUTDIR="${2:-dist}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
umask 022

make -C "$HERE" install PREFIX=/usr DESTDIR="$STAGE/pkg" >/dev/null

install -d "$STAGE/pkg/usr/share/doc/deskcut-gtk" "$STAGE/pkg/DEBIAN"
cp "$HERE/README.md" "$STAGE/pkg/usr/share/doc/deskcut-gtk/"
cat > "$STAGE/pkg/usr/share/doc/deskcut-gtk/copyright" <<'COPYRIGHT'
Upstream-Name: DeskCut-GTK
Source: https://github.com/nikjft/DeskCut-GTK
License: GPL-2.0-only

Based on DeskCut by Nayam Amarshe. The full text of the GNU General Public
License version 2 is in /usr/share/common-licenses/GPL-2.
COPYRIGHT

SIZE="$(du -sk "$STAGE/pkg/usr" | cut -f1)"
cat > "$STAGE/pkg/DEBIAN/control" <<CONTROL
Package: deskcut-gtk
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Installed-Size: $SIZE
Depends: python3, python3-gi, gir1.2-gtk-4.0 (>= 4.10), gir1.2-adw-1 (>= 1.4)
Maintainer: nikjft <nik@inik.net>
Homepage: https://github.com/nikjft/DeskCut-GTK
Description: Create and edit desktop shortcuts
 DeskCut-GTK creates and edits .desktop launchers with a native GTK4 and
 libadwaita interface: set a name, description, path and categories, and
 choose an icon by pasting, dropping, cropping, or picking from your icon
 theme. Existing shortcuts can be opened and edited without losing the keys
 DeskCut does not manage.
CONTROL

mkdir -p "$OUTDIR"
dpkg-deb --root-owner-group --build "$STAGE/pkg" "$OUTDIR/deskcut-gtk_${VERSION}_all.deb" >/dev/null
echo "$OUTDIR/deskcut-gtk_${VERSION}_all.deb"
