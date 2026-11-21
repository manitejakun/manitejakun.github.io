import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class JournalBuildTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "portfolio"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "_site", "__pycache__"))
        self.entries = self.root / "content" / "writing"
        for path in self.entries.glob("*.json"):
            path.unlink()
        self.output = self.root / "_site"

    def write_entry(self, filename, **fields):
        (self.entries / f"{filename}.json").write_text(
            json.dumps({"status": "published", "body": "A short paragraph.", **fields}), encoding="utf-8"
        )

    def build(self):
        return subprocess.run(
            [sys.executable, str(self.root / "build.py")], text=True, capture_output=True,
        )

    def page(self, path):
        return (self.output / path / "index.html").read_text(encoding="utf-8")

    def test_empty_journal(self):
        self.assertEqual(self.build().returncode, 0)
        self.assertIn('href="/journal/">Journal</a>', self.page(""))
        self.assertIn("The first entry is coming soon.", self.page("journal"))

    def test_articles_build_from_the_same_content_as_the_index(self):
        images = self.root / "media" / "images"
        for name in ("portrait", "draft-only"):
            shutil.copyfile(self.root / "images" / "sculpture.webp", images / f"{name}.webp")
        self.write_entry(
            "file-name", title="What I Learned from One Roll of Film and a Very Long Walk",
            slug="one-roll", publication_date="2026-11-20", description="A note on looking slowly.",
            subtitle="Eight frames from a walk.", cover="/media/images/portrait.webp",
            cover_alt="A portrait-format study", cover_caption="From the contact sheet.",
            body="## Notes\n\n> Take your time.\n\n- Look\n- Wait",
        )
        self.write_entry("text-only", title="Text-only note", publication_date="2026-11-12")
        self.write_entry(
            "private-draft", title="Private draft", publication_date="2026-11-21",
            status="draft", cover="/media/images/draft-only.webp",
        )

        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        index = self.page("journal")
        self.assertLess(index.index('href="/journal/one-roll/"'), index.index('href="/journal/text-only/"'))
        self.assertIn("A note on looking slowly.", index)
        self.assertNotIn("Private draft", index)

        photo = self.page("journal/one-roll")
        self.assertIn('content="https://maniteja.me/media/images/portrait.webp"', photo)
        self.assertIn('alt="A portrait-format study"', photo)
        self.assertIn("From the contact sheet.", photo)
        self.assertIn("Eight frames from a walk.", photo)
        self.assertIn("<blockquote>", photo)
        self.assertIn("<h2>Notes</h2>", photo)
        self.assertIn("Back to Journal", photo)
        self.assertIn('url=/journal/one-roll/', self.page("writing/file-name"))
        self.assertNotIn("journal-cover", self.page("journal/text-only"))
        self.assertNotIn('property="og:image"', self.page("journal/text-only"))
        self.assertFalse((self.output / "journal/private-draft").exists())
        self.assertFalse((self.output / "media/images/draft-only.webp").exists())

    def test_duplicate_published_slugs_fail_the_build(self):
        for name in ("first", "second"):
            self.write_entry(name, title=name, slug="same-slug", publication_date="2026-11-20")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the Journal slug 'same-slug' is already in use", result.stderr)
