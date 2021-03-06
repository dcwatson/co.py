#!/usr/bin/env python

import datetime
import os
import subprocess
import sys
import unittest


class AddCopyrightTests(unittest.TestCase):
    def setUp(self):
        self.name = "Dan Watson"
        self.year = datetime.date.today().year
        self.directory = os.path.abspath(os.path.dirname(__file__))
        self.script = os.path.join(self.directory, "co.py")

    def assertCopyright(self, args, original, expected):
        # Create a test file and call the script on it.
        filename = os.path.join(self.directory, "output.tmp")
        with open(filename, "w") as fp:
            fp.write(original)
        subprocess.call([sys.executable, self.script] + args + ["-q", "-e", "tmp", filename])
        with open(filename, "r", newline="") as fp:
            self.assertEqual(fp.read(), expected)
        os.remove(filename)
        # Test the backup file, if one was created.
        if os.path.exists(filename + ".bak"):
            with open(filename + ".bak", "r", newline="") as fp:
                self.assertEqual(fp.read(), original)
            os.remove(filename + ".bak")

    def test_basic(self):
        original = "pass"
        expected = "# Copyright 2020 %s\n\npass" % self.name
        self.assertCopyright(["-y", "2020", "-n", self.name, "-b"], original, expected)

    def test_shebang(self):
        original = "#!/usr/bin/env python\npass"
        expected = "#!/usr/bin/env python\n# Copyright %04d %s\n\npass" % (self.year, self.name)
        self.assertCopyright(["-n", self.name], original, expected)

    def test_coding(self):
        original = "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\npass"
        expected = "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n# Copyright %04d %s\n\npass" % (
            self.year,
            self.name,
        )
        self.assertCopyright(["-n", self.name], original, expected)

    def test_replace(self):
        original = "# Copyright 2010 Old Corp\npass"
        expected = "# Copyright %04d %s\npass" % (self.year, self.name)
        self.assertCopyright(["-n", self.name], original, expected)

    def test_update(self):
        original = "# Copyright 2010 blah blah\r\npass  \r\n"
        expected = "# Copyright 2010-%04d\r\npass  \r\n" % self.year
        self.assertCopyright(["-u"], original, expected)

    def test_keep_endings(self):
        original = "# Copyright 2010\r\npass  \r\n"
        expected = "# Copyright %04d\r\npass  \r\n" % self.year
        self.assertCopyright([], original, expected)

    def test_strip(self):
        original = "# Copyright 2010   \rpass    \r\r"
        expected = "# Copyright %04d\npass\n\n" % self.year
        self.assertCopyright(["-s"], original, expected)

    def test_comment(self):
        original = "pass"
        expected = "// Copyright %04d %s\n\npass" % (self.year, self.name)
        self.assertCopyright(["-n", self.name, "-c", "//"], original, expected)

    def test_no_newline(self):
        original = "pass"
        expected = "# Copyright %04d %s\npass" % (self.year, self.name)
        self.assertCopyright(["-n", self.name, "--no-newline"], original, expected)

    def test_print_only(self):
        self.assertCopyright(["-y", "2020", "-n", self.name, "-p"], "pass", "pass")


if __name__ == "__main__":
    unittest.main()
