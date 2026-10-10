import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from researchaudit.rule_checker import scan_project, has_tests

class CoverageTests(unittest.TestCase):
    def test_dependency_tests_do_not_count_as_project_tests(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.venv').mkdir();(root/'.venv'/'test_dependency.py').write_text('x=1')
            report=scan_project(root)
            self.assertEqual(report['python_files_considered'],0)
            self.assertEqual(report['scan_status'],'no_eligible_sources')
            self.assertFalse(has_tests(root));self.assertTrue(report['skipped'])
    def test_parse_error_does_not_prevent_other_file_checks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bad.py').write_text('def (:');(root/'good.py').write_text('x=1')
            r=scan_project(root);self.assertEqual(r['python_files_checked'],1);self.assertEqual(r['scan_status'],'partial')
            self.assertEqual(len(r['file_records']),2)
    def test_declared_non_utf8_encoding_is_supported(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'encoded.py').write_bytes(b'# coding: latin-1\nx="\xe9"\n')
            r=scan_project(root);self.assertEqual(r['python_files_checked'],1);self.assertEqual(len(r['file_records'][0]['sha256']),64)
    def test_bad_bytes_are_reported_not_a_scan_crash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bad.py').write_bytes(b'\xff');(root/'good.py').write_text('x=1')
            r=scan_project(root);self.assertEqual(r['scan_status'],'partial');self.assertIn('RC10',[f['rule_id'] for f in r['findings']])
    def test_symlink_source_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'actual.py').write_text('x=1');(root/'alias.py').symlink_to(root/'actual.py')
            r=scan_project(root);self.assertEqual(r['python_files_considered'],1);self.assertTrue(any(x['reason']=='symlink' for x in r['skipped']))
    def test_empty_directory_reports_no_sources(self):
        with tempfile.TemporaryDirectory() as d:
            r=scan_project(Path(d));self.assertEqual(r['scan_status'],'no_eligible_sources');self.assertIn('RC09',[f['rule_id'] for f in r['findings']])
    def test_cli_preserves_existing_reports(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'project';root.mkdir();(root/'a.py').write_text('x=1');out=Path(d)/'out'
            env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
            command=[sys.executable,'-m','researchaudit.rule_checker',str(root),'--out',str(out)]
            self.assertEqual(subprocess.run(command,env=env,capture_output=True).returncode,0)
            p=out/'rule_checker_project.json';before=p.read_bytes()
            self.assertNotEqual(subprocess.run(command,env=env,capture_output=True).returncode,0)
            self.assertEqual(before,p.read_bytes())
            self.assertEqual(subprocess.run(command+['--force'],env=env,capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
