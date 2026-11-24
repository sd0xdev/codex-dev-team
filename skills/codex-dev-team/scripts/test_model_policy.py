# SPDX-License-Identifier: MPL-2.0
"""Offline policy and launch/resume regressions; no live Claude/tmux or usage API."""
import contextlib
import datetime as dt
import io
import json
import os
import shlex
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import claude_run as cr
from model_policy import POLICY_ENV, PolicyError, select_model

NOW = dt.datetime(2030, 1, 3, tzinfo=dt.timezone.utc)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='model-policy-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.policy = self.root / 'policy.json'
        self.snapshot = self.root / 'usage.json'
        self.config = {'version': 1, 'stage_models': {
            'research': 'custom-reasoner-r7', 'design': 'custom-architect-z3',
            'acceptance': 'custom-checker-v2', 'development': 'custom-builder-b9',
            'test-writing': 'custom-tester-t4'},
            'quota': {'enabled': True, 'strategy': 'projected_exhaustion',
                      'snapshot_path': 'usage.json', 'max_age_seconds': 3600,
                      'fallback_model': 'custom-pressure-p8', 'projected_fraction_threshold': 1,
                      'min_elapsed_seconds': 60}}
        self.usage = {'scope': 'shared', 'used_fraction': .6,
                      'period_start': '2030-01-01T00:00:00Z',
                      'observed_at': NOW.isoformat(), 'resets_at': '2030-01-08T00:00:00Z'}
        self.write()

    def write(self):
        self.policy.write_text(json.dumps(self.config))
        self.snapshot.write_text(json.dumps(self.usage))

    def choose(self, **kwargs):
        return select_model(policy_path=self.policy, stage='research', now=NOW, **kwargs)

    def test_explicit_overrides_quota_and_stage(self):
        model, audit = self.choose(explicit='user-override-123')
        self.assertEqual((model, audit['source']), ('user-override-123', 'explicit'))
        self.assertEqual(audit['quota']['state'], 'pressure')

    def test_same_usage_day_two_and_day_six_differ(self):
        model, audit = self.choose()
        self.assertEqual(model, 'custom-pressure-p8')
        self.assertAlmostEqual(audit['quota']['projected_fraction'], 2.1)
        self.usage['observed_at'] = '2030-01-07T00:00:00Z'
        self.write()
        model, audit = select_model(policy_path=self.policy, stage='research', now=NOW + dt.timedelta(days=4))
        self.assertEqual((model, audit['source']), ('custom-reasoner-r7', 'stage'))
        self.assertAlmostEqual(audit['quota']['projected_fraction'], .7)

    def test_all_stages_have_custom_models_and_quota_override(self):
        for stage, expected in self.config['stage_models'].items():
            with self.subTest(stage=stage):
                model, _ = select_model(stage=stage, policy_path=self.policy, now=NOW)
                self.assertEqual(model, 'custom-pressure-p8')
                model, audit = select_model(stage=stage, policy_path=self.policy, now=NOW + dt.timedelta(hours=2))
                self.assertEqual(model, expected)
                self.assertEqual(audit['quota']['state'], 'unknown')

    def test_missing_stale_future_reset_and_invalid_usage_use_stage(self):
        variants = [None, {'used_fraction': None}, {'used_fraction': -1}, {'used_fraction': float('nan')},
                    {'used_fraction': True}, {'used_fraction': 1.1}, {'scope': 'unknown'},
                    {'observed_at': '2030-01-02T22:00:00Z'},
                    {'observed_at': '2030-01-03T00:01:00Z'},
                    {'period_start': '2030-01-04T00:00:00Z'},
                    {'resets_at': '2030-01-03T00:00:00Z'},
                    {'observed_at': '2030-01-03T00:00:00'}, {'observed_at': 'invalid'}]
        initial = dict(self.usage)
        for change in variants:
            with self.subTest(change=change):
                self.usage = {**initial, **(change or {})};self.write()
                if change is None:
                    self.snapshot.unlink()
                model, audit = self.choose()
                self.assertEqual(model, 'custom-reasoner-r7')
                self.assertEqual(audit['quota']['state'], 'unknown')
        self.snapshot.write_text('{bad json')
        self.assertEqual(self.choose()[0], 'custom-reasoner-r7')

    def test_disabled_quota_does_not_read_snapshot_or_block(self):
        self.config['quota'] = {'enabled': False};self.usage['used_fraction'] = 1;self.write()
        self.assertEqual(self.choose()[1]['quota']['state'], 'disabled')
        self.assertEqual(self.choose()[0], 'custom-reasoner-r7')

    def test_fresh_shared_exhaustion_blocks_even_explicit_before_model_switch(self):
        self.usage['used_fraction'] = 1;self.write()
        for explicit in (None, 'user-override-123'):
            with self.subTest(explicit=explicit), self.assertRaises(PolicyError) as error:
                self.choose(explicit=explicit)
            self.assertEqual(error.exception.code, 'SHARED_QUOTA_EXHAUSTED')
        # Model-scoped exhaustion can select the user's configured fallback.
        self.usage['scope'] = 'model';self.write()
        self.assertEqual(self.choose()[0], 'custom-pressure-p8')

    def test_usage_threshold_is_configurable(self):
        self.config['quota'].update(strategy='usage_threshold', used_fraction_threshold=.7)
        del self.config['quota']['projected_fraction_threshold'];del self.config['quota']['min_elapsed_seconds']
        self.write();self.assertEqual(self.choose()[0], 'custom-reasoner-r7')
        self.config['quota']['used_fraction_threshold'] = .5;self.write()
        self.assertEqual(self.choose()[0], 'custom-pressure-p8')

    def test_projection_threshold_and_elapsed_are_configurable(self):
        self.config['quota']['projected_fraction_threshold'] = 2.2;self.write()
        self.assertEqual(self.choose()[0], 'custom-reasoner-r7')
        self.config['quota']['projected_fraction_threshold'] = 1
        self.config['quota']['min_elapsed_seconds'] = 3 * 86400;self.write()
        self.assertEqual(self.choose()[1]['quota']['reason'], 'insufficient_elapsed_time')
        self.usage['period_start'] = NOW.isoformat();self.write()
        self.assertEqual(self.choose()[0], 'custom-reasoner-r7')

    def test_no_config_and_unmatched_rule_keep_legacy_behavior(self):
        self.assertEqual(select_model(explicit='arbitrary-id')[0], 'arbitrary-id')
        self.assertEqual(select_model(previous='legacy-choice', stage='development')[0], 'legacy-choice')
        with self.assertRaises(PolicyError) as error:
            select_model(stage='research')
        self.assertEqual(error.exception.code, 'MODEL_REQUIRED')
        self.config = {'version': 1};self.write()
        self.assertEqual(self.choose(previous='legacy-choice')[1]['source'], 'previous_run')
        with self.assertRaises(PolicyError): self.choose()

    def test_invalid_policy_fails_without_echoing_contents(self):
        for config in [{'version': True}, {'version': 2}, {'version': 1, 'unknown': 'secret-value'},
                       {'version': 1, 'stage_models': {'typo': 'model'}},
                       {'version': 1, 'stage_models': {'research': ''}},
                       {'version': 1, 'quota': {'enabled': 'true'}},
                       {'version': 1, 'quota': {'enabled': True}}]:
            with self.subTest(config=config):
                self.config = config;self.write()
                with self.assertRaises(PolicyError) as error: self.choose()
                self.assertEqual(error.exception.code, 'MODEL_POLICY_INVALID')
                self.assertNotIn('secret-value', str(error.exception))
        self.policy.unlink()
        with self.assertRaises(PolicyError): self.choose()

    def test_path_resolution_errors_follow_policy_and_usage_error_rules(self):
        # Simulate missing home-directory lookup and symlink-resolution errors.
        for error in (RuntimeError('no home'), OSError('symlink loop')):
            with self.subTest(error=type(error).__name__):
                with patch.object(Path, 'expanduser', side_effect=error):
                    with self.assertRaises(PolicyError) as caught:
                        self.choose()
                self.assertEqual(caught.exception.code, 'MODEL_POLICY_INVALID')
                from model_policy import evaluate_quota
                with patch.object(Path, 'expanduser', side_effect=error):
                    audit = evaluate_quota(self.config['quota'], self.policy, NOW)
                self.assertEqual(audit['state'], 'unknown')

    def test_audit_does_not_copy_raw_usage_fields(self):
        self.usage['irrelevant_private_value'] = 'do-not-copy';self.write()
        audit = self.choose()[1]
        self.assertNotIn('do-not-copy', json.dumps(audit))
        self.assertTrue(audit['policy_sha256'].startswith('sha256:'))
        self.assertEqual(audit['policy_path'], str(self.policy))


class RunnerSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='stage-run-');self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve();self.repo = self.root/'repo';self.repo.mkdir()
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        self.mission = self.root/'mission.md';self.mission.write_text('Synthetic offline mission')
        self.cli = self.root/'fake-claude'
        help_text = '--remote-control --session-id --effort\n  --permission-mode <mode> (choices: "manual")'
        self.cli.write_text('#!/bin/sh\ncase "$1" in\n--help) printf "%s\\n" ' + shlex.quote(help_text) +
                            ';;\n--version) echo fake-offline;;\n*) exit 91;;\nesac\n')
        self.cli.chmod(0o700)
        self.policy = self.root/'policy.json'
        self.policy.write_text(json.dumps({'version':1,'stage_models':{'research':'custom-thinker-r1','development':'custom-coder-d2','test-writing':'custom-test-t3','acceptance':'custom-review-a4'}}))
        env = patch.dict(os.environ,{POLICY_ENV:''});env.start();self.addCleanup(env.stop)

    def invoke(self, *args):
        out=io.StringIO()
        with patch('sys.argv',['claude_run.py',*args]), patch.object(cr,'session_processes',return_value=[]), contextlib.redirect_stdout(out): cr.main()
        return json.loads(out.getvalue())

    def launch(self, *args):
        return self.invoke('launch','--repo',str(self.repo),'--mission',str(self.mission),'--runs-root',str(self.root/'runs'),
                           '--claude-bin',str(self.cli),'--tmux-socket',str(self.root/'s'),'--permission-mode','manual','--prepare-only',*args)

    def resume(self, previous, *args):
        return self.invoke('resume','--from',previous['run_dir'],'--mission',str(self.mission),'--prepare-only',*args)

    def close_fixture(self, result):
        path=Path(result['run_dir']);meta=json.loads((path/'meta.json').read_text());meta['started']=True
        (path/'meta.json').write_text(json.dumps(meta));(path/'exit.json').write_text('{"exit_code":0}')
        return meta

    def test_same_session_research_development_acceptance_and_readback(self):
        first=self.launch('--model-policy',str(self.policy),'--stage','research','--effort','high')
        prev=first;identities=[]
        for stage,expected in [('research','custom-thinker-r1'),('development','custom-coder-d2'),('acceptance','custom-review-a4')]:
            current=first if stage=='research' else self.resume(prev,'--stage',stage)
            path=Path(current['run_dir']);meta=json.loads((path/'meta.json').read_text());identities.append(meta['session_id'])
            self.assertEqual(meta['requested_model'],expected);self.assertEqual(meta['requested_effort'],'high')
            self.assertEqual(meta['permission_mode'],'manual');self.assertEqual(meta['tmux_socket'],str(self.root/'s'))
            self.assertEqual(meta['mode'],'interactive_rc');self.assertIn('--remote-control',meta['argv'])
            self.assertEqual(meta['argv'][meta['argv'].index('--model')+1],expected)
            self.assertEqual(meta['model_selection']['stage'],stage)
            self.assertFalse((path/'dispatch.json').exists())
            if stage!='research':
                self.assertEqual(meta['argv'][meta['argv'].index('--resume')+1],identities[0])
                self.assertEqual(meta['model_selection']['policy_path'],str(self.policy))
            meta.update(started=True,pane_id='%7');(path/'meta.json').write_text(json.dumps(meta))
            def tmux(socket,*args,**kwargs):
                self.assertEqual(str(socket),str(self.root/'s'))
                return subprocess.CompletedProcess(args,0,meta['tmux_session'].encode() if args[0]=='display-message' else b'idle',b'')
            attestation=type('Args',(),dict(run_dir=str(path),confirm_rc_active_and_idle=True,remote_url='https://claude.ai/code/session_offline',actual_model='incorrect'))()
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):cr.dispatch(attestation)
            self.assertFalse((path/'dispatch.json').exists())
            attestation.actual_model=expected
            with patch.object(cr,'tmux_alive',return_value=True),patch.object(cr,'tmux',side_effect=tmux),contextlib.redirect_stdout(io.StringIO()):cr.dispatch(attestation)
            self.assertEqual(json.loads((path/'dispatch.json').read_text())['actual_model'],expected)
            self.close_fixture(current);prev=current
        self.assertEqual(len(set(identities)),1)
        self.assertNotEqual(first['run_dir'],prev['run_dir'])

    def test_policy_path_persists_but_stage_is_not_inherited(self):
        with patch.dict(os.environ,{POLICY_ENV:str(self.policy)}):first=self.launch('--stage','research')
        self.close_fixture(first)
        self.assertEqual(self.resume(first)['model_selection']['source'],'previous_run')
        self.assertIsNone(self.resume(first)['model_selection']['stage'])
        new=self.resume(first,'--stage','test-writing');self.assertEqual(new['requested_model'],'custom-test-t3')
        config=json.loads(self.policy.read_text());config['stage_models']['development']='reconfigured-id';self.policy.write_text(json.dumps(config))
        self.assertEqual(self.resume(first,'--stage','development')['requested_model'],'reconfigured-id')
        self.assertEqual(self.resume(first,'--stage','development','--model','explicit-new')['requested_model'],'explicit-new')
        self.assertEqual(self.resume(first,'--stage','development','--no-model-policy')['requested_model'],'custom-thinker-r1')

    def test_old_run_without_policy_metadata_and_unconfigured_launch(self):
        with self.assertRaises(SystemExit),contextlib.redirect_stderr(io.StringIO()):self.launch('--stage','research')
        self.assertFalse((self.root/'runs').exists())
        first=self.launch('--model','legacy-model','--effort','medium');meta=self.close_fixture(first)
        del meta['model_selection'];Path(first['run_dir'],'meta.json').write_text(json.dumps(meta))
        resumed=self.resume(first);new=json.loads(Path(resumed['run_dir'],'meta.json').read_text())
        self.assertEqual(new['requested_model'],'legacy-model');self.assertEqual(new['requested_effort'],'medium')
        self.assertEqual(new['session_id'],meta['session_id'])
        opted_in=self.resume(first,'--model-policy',str(self.policy),'--stage','development')
        self.assertEqual(opted_in['requested_model'],'custom-coder-d2')

    def test_cli_resume_rechecks_quota_and_blocks_shared_exhaustion(self):
        first=self.launch('--model-policy',str(self.policy),'--stage','research');self.close_fixture(first)
        now=dt.datetime.now(dt.timezone.utc)
        usage={'scope':'shared','used_fraction':.6,'period_start':(now-dt.timedelta(days=2)).isoformat(),
               'observed_at':now.isoformat(),'resets_at':(now+dt.timedelta(days=5)).isoformat()}
        (self.root/'usage.json').write_text(json.dumps(usage))
        config=json.loads(self.policy.read_text());config['quota']={'enabled':True,'strategy':'projected_exhaustion','snapshot_path':'usage.json','max_age_seconds':600,'fallback_model':'custom-pressure-q9','projected_fraction_threshold':1};self.policy.write_text(json.dumps(config))
        resumed=self.resume(first,'--stage','acceptance');self.assertEqual(resumed['requested_model'],'custom-pressure-q9')
        self.assertEqual(self.resume(first,'--stage','acceptance','--model','custom-explicit')['requested_model'],'custom-explicit')
        before=set((self.root/'runs').iterdir());usage['used_fraction']=1;(self.root/'usage.json').write_text(json.dumps(usage))
        for action in [lambda:self.resume(first,'--stage','development'),lambda:self.launch('--model-policy',str(self.policy),'--model','custom-explicit')]:
            with self.assertRaises(SystemExit),contextlib.redirect_stderr(io.StringIO()):action()
        self.assertEqual(set((self.root/'runs').iterdir()),before)
        (self.root/'usage.json').unlink()
        self.assertEqual(self.resume(first,'--stage','acceptance')['requested_model'],'custom-review-a4')

    def test_no_policy_does_not_disable_existing_live_session_guard(self):
        first=self.launch('--model-policy',str(self.policy),'--stage','research')
        with self.assertRaises(SystemExit),contextlib.redirect_stderr(io.StringIO()):self.resume(first,'--stage','development')
        self.assertEqual(len(list((self.root/'runs').glob('resume-*'))),0)


if __name__ == '__main__':
    unittest.main()
