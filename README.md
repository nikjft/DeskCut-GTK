# DeskCut-GTK

Create and edit Linux desktop shortcuts (`.desktop` files) without touching the files by hand. A native GTK4 and libadwaita rewrite of [DeskCut](https://github.com/NayamAmarshe/DeskCut) by Nayam Amarshe.

## Features

- **Get-info style window:** name, description, path, categories and an "Open in terminal" switch. The file's `Type` is always `Application`.
- **Icon well:** select it and paste an image or an image URL, drop a file or link on it, or right-click for more. Pasted links are downloaded for you.
- **Browse:** pick an icon from your current icon theme, or from a file.
- **Categories:** type to get suggestions from the standard menu categories and press Enter to add one as a tag. Backspace on an empty field removes the last tag.
- **Crop:** drag and zoom to frame the icon before it's saved.
- **Edit existing shortcuts:** File → Open… loads any `.desktop` file. Keys DeskCut doesn't manage (Categories, MimeType, translations, comments) are kept as they were.
- **File and Edit menus:** New, Open…, Install, Quit, plus Undo, Redo, Cut, Copy, Paste, Delete and Select All.

Shortcuts are written to `~/.local/share/applications`. Cropped icons are stored in `~/.local/share/icons/deskcut`.

## Requirements

Python 3.10 or newer, GTK 4.10 or newer and libadwaita 1.4 or newer.

On Debian, Ubuntu and Pop!_OS:

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

On Fedora:

```bash
sudo dnf install python3-gobject gtk4 libadwaita
```

On Arch:

```bash
sudo pacman -S python-gobject gtk4 libadwaita
```

## Run from the source tree

```bash
./deskcut-gtk
```

Pass a `.desktop` file to open it straight away:

```bash
./deskcut-gtk ~/.local/share/applications/example.desktop
```

## Install

```bash
make install            # to ~/.local
sudo make install PREFIX=/usr/local
```

`make uninstall` removes it again.

## Tests

```bash
make test
```

## Disclaimer

This project was vibe coded with an AI assistant. It is provided as is, with no warranty of any kind. It writes files to `~/.local/share/applications` and `~/.local/share/icons`, so review what it does before relying on it.

## Credits and license

Based on [DeskCut](https://github.com/NayamAmarshe/DeskCut) by Nayam Amarshe. Licensed under the GPLv2, see [LICENSE](LICENSE).
