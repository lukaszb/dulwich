# test_patch.py -- tests for patch.py
# Copyright (C) 2010 Jelmer Vernooij <jelmer@samba.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your option) a later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

"""Tests for patch.py."""

from cStringIO import StringIO

from dulwich.objects import (
    Blob,
    Commit,
    Tree,
    )
from dulwich.object_store import (
    MemoryObjectStore,
    )
from dulwich.patch import (
    git_am_patch_split,
    write_blob_diff,
    write_commit_patch,
    write_tree_diff,
    )
from dulwich.tests import (
    TestCase,
    TestSkipped,
    )


class WriteCommitPatchTests(TestCase):

    def test_simple(self):
        f = StringIO()
        c = Commit()
        c.committer = c.author = "Jelmer <jelmer@samba.org>"
        c.commit_time = c.author_time = 1271350201
        c.commit_timezone = c.author_timezone = 0
        c.message = "This is the first line\nAnd this is the second line.\n"
        c.tree = Tree().id
        write_commit_patch(f, c, "CONTENTS", (1, 1), version="custom")
        f.seek(0)
        lines = f.readlines()
        self.assertTrue(lines[0].startswith("From 0b0d34d1b5b596c928adc9a727a4b9e03d025298"))
        self.assertEquals(lines[1], "From: Jelmer <jelmer@samba.org>\n")
        self.assertTrue(lines[2].startswith("Date: "))
        self.assertEquals([
            "Subject: [PATCH 1/1] This is the first line\n",
            "And this is the second line.\n",
            "\n",
            "\n",
            "---\n"], lines[3:8])
        self.assertEquals([
            "CONTENTS-- \n",
            "custom\n"], lines[-2:])
        if len(lines) >= 12:
            # diffstat may not be present
            self.assertEquals(lines[8], " 0 files changed\n")


class ReadGitAmPatch(TestCase):

    def test_extract(self):
        text = """From ff643aae102d8870cac88e8f007e70f58f3a7363 Mon Sep 17 00:00:00 2001
From: Jelmer Vernooij <jelmer@samba.org>
Date: Thu, 15 Apr 2010 15:40:28 +0200
Subject: [PATCH 1/2] Remove executable bit from prey.ico (triggers a lintian warning).

---
 pixmaps/prey.ico |  Bin 9662 -> 9662 bytes
 1 files changed, 0 insertions(+), 0 deletions(-)
 mode change 100755 => 100644 pixmaps/prey.ico

-- 
1.7.0.4
"""
        c, diff, version = git_am_patch_split(StringIO(text))
        self.assertEquals("Jelmer Vernooij <jelmer@samba.org>", c.committer)
        self.assertEquals("Jelmer Vernooij <jelmer@samba.org>", c.author)
        self.assertEquals("Remove executable bit from prey.ico "
            "(triggers a lintian warning).\n", c.message)
        self.assertEquals(""" pixmaps/prey.ico |  Bin 9662 -> 9662 bytes
 1 files changed, 0 insertions(+), 0 deletions(-)
 mode change 100755 => 100644 pixmaps/prey.ico

""", diff)
        self.assertEquals("1.7.0.4", version)

    def test_extract_spaces(self):
        text = """From ff643aae102d8870cac88e8f007e70f58f3a7363 Mon Sep 17 00:00:00 2001
From: Jelmer Vernooij <jelmer@samba.org>
Date: Thu, 15 Apr 2010 15:40:28 +0200
Subject:  [Dulwich-users] [PATCH] Added unit tests for
 dulwich.object_store.tree_lookup_path.

* dulwich/tests/test_object_store.py
  (TreeLookupPathTests): This test case contains a few tests that ensure the
   tree_lookup_path function works as expected.
---
 pixmaps/prey.ico |  Bin 9662 -> 9662 bytes
 1 files changed, 0 insertions(+), 0 deletions(-)
 mode change 100755 => 100644 pixmaps/prey.ico

-- 
1.7.0.4
"""
        c, diff, version = git_am_patch_split(StringIO(text))
        self.assertEquals('Added unit tests for dulwich.object_store.tree_lookup_path.\n\n* dulwich/tests/test_object_store.py\n  (TreeLookupPathTests): This test case contains a few tests that ensure the\n   tree_lookup_path function works as expected.\n', c.message)

    def test_extract_pseudo_from_header(self):
        text = """From ff643aae102d8870cac88e8f007e70f58f3a7363 Mon Sep 17 00:00:00 2001
From: Jelmer Vernooij <jelmer@samba.org>
Date: Thu, 15 Apr 2010 15:40:28 +0200
Subject:  [Dulwich-users] [PATCH] Added unit tests for
 dulwich.object_store.tree_lookup_path.

From: Jelmer Vernooy <jelmer@debian.org>

* dulwich/tests/test_object_store.py
  (TreeLookupPathTests): This test case contains a few tests that ensure the
   tree_lookup_path function works as expected.
---
 pixmaps/prey.ico |  Bin 9662 -> 9662 bytes
 1 files changed, 0 insertions(+), 0 deletions(-)
 mode change 100755 => 100644 pixmaps/prey.ico

-- 
1.7.0.4
"""
        c, diff, version = git_am_patch_split(StringIO(text))
        self.assertEquals("Jelmer Vernooy <jelmer@debian.org>", c.author)
        self.assertEquals('Added unit tests for dulwich.object_store.tree_lookup_path.\n\n* dulwich/tests/test_object_store.py\n  (TreeLookupPathTests): This test case contains a few tests that ensure the\n   tree_lookup_path function works as expected.\n', c.message)

    def test_extract_no_version_tail(self):
        text = """From ff643aae102d8870cac88e8f007e70f58f3a7363 Mon Sep 17 00:00:00 2001
From: Jelmer Vernooij <jelmer@samba.org>
Date: Thu, 15 Apr 2010 15:40:28 +0200
Subject:  [Dulwich-users] [PATCH] Added unit tests for
 dulwich.object_store.tree_lookup_path.

From: Jelmer Vernooy <jelmer@debian.org>

---
 pixmaps/prey.ico |  Bin 9662 -> 9662 bytes
 1 files changed, 0 insertions(+), 0 deletions(-)
 mode change 100755 => 100644 pixmaps/prey.ico

"""
        c, diff, version = git_am_patch_split(StringIO(text))
        self.assertEquals(None, version)

    def test_extract_mercurial(self):
        raise TestSkipped("git_am_patch_split doesn't handle Mercurial patches properly yet")
        expected_diff = """diff --git a/dulwich/tests/test_patch.py b/dulwich/tests/test_patch.py
--- a/dulwich/tests/test_patch.py
+++ b/dulwich/tests/test_patch.py
@@ -158,7 +158,7 @@
 
 '''
         c, diff, version = git_am_patch_split(StringIO(text))
-        self.assertIs(None, version)
+        self.assertEquals(None, version)
 
 
 class DiffTests(TestCase):
"""
        text = """From dulwich-users-bounces+jelmer=samba.org@lists.launchpad.net Mon Nov 29 00:58:18 2010
Date: Sun, 28 Nov 2010 17:57:27 -0600
From: Augie Fackler <durin42@gmail.com>
To: dulwich-users <dulwich-users@lists.launchpad.net>
Subject: [Dulwich-users] [PATCH] test_patch: fix tests on Python 2.6
Content-Transfer-Encoding: 8bit

Change-Id: I5e51313d4ae3a65c3f00c665002a7489121bb0d6

%s

_______________________________________________
Mailing list: https://launchpad.net/~dulwich-users
Post to     : dulwich-users@lists.launchpad.net
Unsubscribe : https://launchpad.net/~dulwich-users
More help   : https://help.launchpad.net/ListHelp

""" % expected_diff
        c, diff, version = git_am_patch_split(StringIO(text))
        self.assertEquals(expected_diff, diff)
        self.assertEquals(None, version)


class DiffTests(TestCase):
    """Tests for write_blob_diff and write_tree_diff."""

    def test_blob_diff(self):
        f = StringIO()
        write_blob_diff(f, ("foo.txt", 0644, Blob.from_string("old\nsame\n")),
                           ("bar.txt", 0644, Blob.from_string("new\nsame\n")))
        self.assertEquals([
            "diff --git a/foo.txt b/bar.txt",
            "index 3b0f961..a116b51 644",
            "--- a/foo.txt",
            "+++ b/bar.txt",
            "@@ -1,2 +1,2 @@",
            "-old",
            "+new",
            " same"
            ], f.getvalue().splitlines())

    def test_blob_add(self):
        f = StringIO()
        write_blob_diff(f, (None, None, None),
                           ("bar.txt", 0644, Blob.from_string("new\nsame\n")))
        self.assertEquals([
            'diff --git /dev/null b/bar.txt',
             'new mode 644',
             'index 0000000..a116b51 644',
             '--- /dev/null',
             '+++ b/bar.txt',
             '@@ -1,0 +1,2 @@',
             '+new',
             '+same'
            ], f.getvalue().splitlines())

    def test_blob_remove(self):
        f = StringIO()
        write_blob_diff(f, ("bar.txt", 0644, Blob.from_string("new\nsame\n")),
                           (None, None, None))
        self.assertEquals([
            'diff --git a/bar.txt /dev/null',
            'deleted mode 644',
            'index a116b51..0000000',
            '--- a/bar.txt',
            '+++ /dev/null',
            '@@ -1,2 +1,0 @@',
            '-new',
            '-same'
            ], f.getvalue().splitlines())

    def test_tree_diff(self):
        f = StringIO()
        store = MemoryObjectStore()
        added = Blob.from_string("add\n")
        removed = Blob.from_string("removed\n")
        changed1 = Blob.from_string("unchanged\nremoved\n")
        changed2 = Blob.from_string("unchanged\nadded\n")
        unchanged = Blob.from_string("unchanged\n")
        tree1 = Tree()
        tree1.add(0644, "removed.txt", removed.id)
        tree1.add(0644, "changed.txt", changed1.id)
        tree1.add(0644, "unchanged.txt", changed1.id)
        tree2 = Tree()
        tree2.add(0644, "added.txt", added.id)
        tree2.add(0644, "changed.txt", changed2.id)
        tree2.add(0644, "unchanged.txt", changed1.id)
        store.add_objects([(o, None) for o in [
            tree1, tree2, added, removed, changed1, changed2, unchanged]])
        write_tree_diff(f, store, tree1.id, tree2.id)
        self.assertEquals([
            'diff --git /dev/null b/added.txt',
            'new mode 644',
            'index e69de29..76d4bb8 644',
            '--- /dev/null',
            '+++ b/added.txt',
            '@@ -1,0 +1,1 @@',
            '+add',
            'diff --git a/changed.txt b/changed.txt',
            'index bf84e48..1be2436 644',
            '--- a/changed.txt',
            '+++ b/changed.txt',
            '@@ -1,2 +1,2 @@',
            ' unchanged',
            '-removed',
            '+added',
            'diff --git a/removed.txt /dev/null',
            'deleted mode 644',
            'index 2c3f0b3..e69de29',
            '--- a/removed.txt',
            '+++ /dev/null',
            '@@ -1,1 +1,0 @@',
            '-removed',
            ], f.getvalue().splitlines())
