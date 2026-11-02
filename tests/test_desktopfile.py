import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from deskcut_gtk import desktopfile  # noqa: E402
from deskcut_gtk.desktopfile import Shortcut  # noqa: E402


class DesktopFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        desktopfile.APPS_DIR = os.path.join(self.tmp.name, "applications")

    def test_new_file_quotes_bare_paths_with_spaces(self):
        script = os.path.join(self.tmp.name, "my app.sh")
        open(script, "w").close()
        path = desktopfile.save(Shortcut("My App", "", script, "", True))
        loaded = desktopfile.load(path)
        self.assertEqual(loaded.exec, f'"{script}"')
        self.assertTrue(loaded.terminal)
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o755)

    def test_command_lines_are_left_alone(self):
        self.assertEqual(desktopfile.format_exec("/opt/x/x --flag %U"), "/opt/x/x --flag %U")
        self.assertEqual(desktopfile.format_exec('"/a b/c" %U'), '"/a b/c" %U')

    def test_multiline_comment_round_trips(self):
        path = desktopfile.save(Shortcut("Note", "line1\nline2", "/bin/true"))
        self.assertEqual(desktopfile.load(path).comment, "line1\nline2")

    def test_second_new_file_with_same_name_does_not_overwrite(self):
        a = desktopfile.save(Shortcut("Dup", "", "/bin/true"))
        b = desktopfile.save(Shortcut("Dup", "", "/bin/false"))
        self.assertNotEqual(a, b)
        self.assertEqual(desktopfile.load(a).exec, "/bin/true")

    def test_editing_keeps_unmanaged_keys(self):
        original = (
            "[Desktop Entry]\nName=Antigravity\nName[de]=Schwerkraft\n"
            "Comment=Agent & IDE\nExec=/opt/ag/ag %U\nIcon=ag\nTerminal=false\n"
            "Type=Application\nCategories=Development;IDE;\nStartupWMClass=Antigravity\n"
            "MimeType=x-scheme-handler/antigravity;\n"
        )
        path = os.path.join(self.tmp.name, "ag.desktop")
        with open(path, "w") as f:
            f.write(original)

        shortcut = desktopfile.load(path)
        self.assertEqual(shortcut.comment, "Agent & IDE")
        shortcut.comment = "changed"
        shortcut.terminal = True
        self.assertEqual(desktopfile.save(shortcut, path), path)

        text = open(path).read()
        for kept in (
            "Name[de]=Schwerkraft",
            "Categories=Development;IDE;",
            "StartupWMClass=Antigravity",
            "MimeType=x-scheme-handler/antigravity;",
            "Exec=/opt/ag/ag %U",
        ):
            self.assertIn(kept, text)
        self.assertIn("Comment=changed", text)
        self.assertIn("Terminal=true", text)

    def test_type_is_always_application_and_categories_round_trip(self):
        path = os.path.join(self.tmp.name, "odd.desktop")
        with open(path, "w") as f:
            f.write("[Desktop Entry]\nType=Link\nName=Odd\nURL=x\nCategories=Network;WebBrowser;\n")
        shortcut = desktopfile.load(path)
        self.assertEqual(shortcut.categories, ["Network", "WebBrowser"])
        shortcut.categories.append("GTK")
        desktopfile.save(shortcut, path)
        text = open(path).read()
        self.assertIn("Type=Application", text)
        self.assertNotIn("Type=Link", text)
        self.assertIn("Categories=Network;WebBrowser;GTK;", text)

    def test_empty_categories_removes_the_key(self):
        path = desktopfile.save(Shortcut("Cat", "", "/bin/true", categories=["Utility"]))
        self.assertIn("Categories=Utility;", open(path).read())
        shortcut = desktopfile.load(path)
        shortcut.categories = []
        desktopfile.save(shortcut, path)
        self.assertNotIn("Categories", open(path).read())


class CategoriesTest(unittest.TestCase):
    def test_normalize(self):
        from deskcut_gtk import categories as c

        self.assertEqual(c.normalize("  utility; "), "Utility")
        self.assertEqual(c.normalize("webbrowser"), "WebBrowser")
        self.assertEqual(c.normalize("X-My-Thing"), "X-My-Thing")
        self.assertIsNone(c.normalize("two words"))
        self.assertIsNone(c.normalize(""))

    def test_parse_join_and_main(self):
        from deskcut_gtk import categories as c

        self.assertEqual(c.parse("A;B;;A;"), ["A", "B"])
        self.assertEqual(c.join(["A", "B"]), "A;B;")
        self.assertTrue(c.has_main(["GTK", "Utility"]))
        self.assertFalse(c.has_main(["GTK"]))


if __name__ == "__main__":
    unittest.main()
