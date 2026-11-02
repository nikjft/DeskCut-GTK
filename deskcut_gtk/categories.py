"""Freedesktop menu categories and helpers for the tag editor."""

import re

# Main categories: one of these is needed for a shortcut to show in app menus.
MAIN = [
    "AudioVideo", "Audio", "Video", "Development", "Education", "Game",
    "Graphics", "Network", "Office", "Science", "Settings", "System", "Utility",
]

# Additional categories from the Desktop Menu Specification, plus toolkit tags.
ADDITIONAL = [
    "Building", "Debugger", "IDE", "GUIDesigner", "Profiling", "RevisionControl",
    "Translation", "WebDevelopment",
    "Calendar", "ContactManagement", "Database", "Dictionary", "Chart", "Email",
    "Finance", "FlowChart", "PDA", "ProjectManagement", "Presentation",
    "Spreadsheet", "WordProcessor",
    "2DGraphics", "VectorGraphics", "RasterGraphics", "3DGraphics", "Scanning",
    "OCR", "Photography", "Publishing", "Viewer",
    "TextTools", "DesktopSettings", "HardwareSettings", "Printing",
    "PackageManager", "Security", "Accessibility",
    "Dialup", "InstantMessaging", "Chat", "IRCClient", "Feed", "FileTransfer",
    "HamRadio", "News", "P2P", "RemoteAccess", "Telephony", "VideoConference",
    "WebBrowser",
    "Midi", "Mixer", "Sequencer", "Tuner", "TV", "AudioVideoEditing", "Player",
    "Recorder", "DiscBurning", "Music",
    "ActionGame", "AdventureGame", "ArcadeGame", "BoardGame", "BlocksGame",
    "CardGame", "Emulator", "KidsGame", "LogicGame", "RolePlaying",
    "Shooter", "Simulation", "SportsGame", "StrategyGame",
    "Art", "Construction", "Languages", "ArtificialIntelligence", "Astronomy",
    "Biology", "Chemistry", "ComputerScience", "DataVisualization", "Economy",
    "Electricity", "Geography", "Geology", "Geoscience", "History",
    "Humanities", "ImageProcessing", "Literature", "Maps", "Math", "NumericalAnalysis",
    "MedicalSoftware", "Physics", "Robotics", "Spirituality", "ParallelComputing",
    "Sports", "Electronics", "Engineering",
    "Monitor", "Core", "Archiving", "Compression", "FileTools", "FileManager",
    "TerminalEmulator", "Filesystem", "Calculator", "Clock", "TextEditor",
    "Documentation", "ConsoleOnly",
    "GNOME", "GTK", "KDE", "Qt",
]

KNOWN = MAIN + sorted(set(ADDITIONAL) - set(MAIN))
_CANONICAL = {name.lower(): name for name in KNOWN}
_VALID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def normalize(text: str) -> str | None:
    """A clean category name, or None if `text` can't be one.

    Known names are matched case-insensitively and come back in their
    official casing. Anything else is kept as typed (extension categories).
    """
    text = text.strip().strip(";").strip()
    if not _VALID.match(text):
        return None
    return _CANONICAL.get(text.lower(), text)


def parse(value: str) -> list[str]:
    seen: list[str] = []
    for part in value.split(";"):
        name = part.strip()
        if name and name not in seen:
            seen.append(name)
    return seen


def join(categories: list[str]) -> str:
    return "".join(f"{c};" for c in categories)


def has_main(categories: list[str]) -> bool:
    return any(c in MAIN for c in categories)
