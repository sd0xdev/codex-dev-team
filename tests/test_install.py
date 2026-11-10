# SPDX-License-Identifier: MPL-2.0
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_text('test skill')
        (self.source / 'script.py').write_text('print(1)')
        (self.source / 'script.py').chmod(0o755)
        self.target = self.root / 'profile' / 'skills'
        self.patch = patch.object(install, 'SOURCE', self.source)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_fresh_install_and_idempotence(self):
        result = install.install(self.target)
        self.assertEqual(result['status'], 'installed')
        self.assertEqual(install.contents(Path(result['path'])), install.contents(self.source))
        self.assertEqual(install.install(self.target)['status'], 'already_current')

    def test_dry_run_has_no_side_effects(self):
        self.assertEqual(install.install(self.target, dry_run=True)['status'], 'would_install')
        self.assertFalse(self.target.exists())

    def test_update_preserves_local_changes_and_unrelated_skills(self):
        install.install(self.target)
        dest = self.target / install.NAME
        (dest / 'custom.txt').write_text('local change')
        other = self.target / 'unrelated'
        other.mkdir()
        (other / 'SKILL.md').write_text('keep')
        with self.assertRaises(ValueError):
            install.install(self.target)
        result = install.install(self.target, update=True)
        self.assertEqual((Path(result['backup']) / 'custom.txt').read_text(), 'local change')
        self.assertEqual(install.contents(dest), install.contents(self.source))
        self.assertEqual((other / 'SKILL.md').read_text(), 'keep')

    def test_symlinks_are_not_followed(self):
        self.target.mkdir(parents=True)
        (self.target / install.NAME).symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            install.install(self.target, update=True)
        self.assertEqual((self.source / 'SKILL.md').read_text(), 'test skill')

    def test_source_symlinks_are_rejected(self):
        (self.source / 'alias').symlink_to(self.source / 'SKILL.md')
        with self.assertRaises(ValueError):
            install.install(self.target)

    def test_locked_install_does_not_modify_destination(self):
        install.install(self.target)
        (self.source / 'new').write_text('new version')
        (self.target / '.codex-dev-team-install.lock').write_text('busy')
        with self.assertRaises(FileExistsError):
            install.install(self.target, update=True)
        self.assertFalse((self.target / install.NAME / 'new').exists())

    def test_failed_replacement_restores_backup(self):
        install.install(self.target)
        dest = self.target / install.NAME
        (dest / 'custom.txt').write_text('preserve me')
        original = Path.rename
        def rename(path, target):
            if path.name.startswith('.codex-dev-team-stage-'):
                raise OSError('simulated replacement failure')
            return original(path, target)
        with patch.object(Path, 'rename', rename), self.assertRaises(OSError):
            install.install(self.target, update=True)
        self.assertEqual((dest / 'custom.txt').read_text(), 'preserve me')
        self.assertFalse((self.target / '.codex-dev-team-install.lock').exists())


if __name__ == '__main__':
    unittest.main()
