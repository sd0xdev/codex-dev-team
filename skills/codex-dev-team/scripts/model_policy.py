# SPDX-License-Identifier: MPL-2.0
"""Local, opt-in model selection. No network, credentials, commands or prompts."""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

STAGES = ('research', 'design', 'acceptance', 'development', 'test-writing')
POLICY_ENV = 'CODEX_DEV_TEAM_MODEL_POLICY'


class PolicyError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def model_id(value):
    if not isinstance(value, str) or not value or value.startswith('-') or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError('model IDs must be nonempty strings without whitespace or leading hyphens')
    return value


def number(value, name, minimum=0, maximum=None, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            or value < minimum or (positive and value == 0) or (maximum is not None and value > maximum)):
        raise ValueError('invalid ' + name)
    return value


def fields(obj, allowed, name):
    if not isinstance(obj, dict) or set(obj) - set(allowed):
        raise ValueError('invalid fields in ' + name)


def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw), 'sha256:' + hashlib.sha256(raw).hexdigest()


def load_policy(path):
    try:
        config, digest = read_json(path)
        fields(config, ('version', 'stage_models', 'quota'), 'policy')
        if type(config.get('version')) is not int or config['version'] != 1:
            raise ValueError('policy version must be 1')
        stages = config.get('stage_models', {})
        fields(stages, STAGES, 'stage_models')
        for model in stages.values():
            model_id(model)
        quota = config.get('quota', {'enabled': False})
        fields(quota, ('enabled', 'strategy', 'snapshot_path', 'max_age_seconds', 'fallback_model',
                       'projected_fraction_threshold', 'min_elapsed_seconds', 'used_fraction_threshold'), 'quota')
        if type(quota.get('enabled')) is not bool:
            raise ValueError('quota.enabled must be true or false')
        if quota['enabled']:
            if quota.get('strategy') not in ('projected_exhaustion', 'usage_threshold'):
                raise ValueError('unknown quota strategy')
            model_id(quota.get('fallback_model'))
            if not isinstance(quota.get('snapshot_path'), str) or not quota['snapshot_path'].strip():
                raise ValueError('quota.snapshot_path is required')
            number(quota.get('max_age_seconds'), 'max_age_seconds', positive=True)
            if quota['strategy'] == 'projected_exhaustion':
                number(quota.get('projected_fraction_threshold'), 'projected_fraction_threshold', positive=True)
                number(quota.get('min_elapsed_seconds', 0), 'min_elapsed_seconds')
                if 'used_fraction_threshold' in quota:
                    raise ValueError('used_fraction_threshold belongs to usage_threshold')
            else:
                number(quota.get('used_fraction_threshold'), 'used_fraction_threshold', maximum=1, positive=True)
                if 'projected_fraction_threshold' in quota or 'min_elapsed_seconds' in quota:
                    raise ValueError('projection settings belong to projected_exhaustion')
        return config, digest
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        # Never echo file contents or supplied credential-like values.
        raise PolicyError('MODEL_POLICY_INVALID', 'cannot read/validate policy: ' + str(path)) from exc


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be ISO 8601 with timezone')
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('timestamp requires timezone')
    return result.astimezone(dt.timezone.utc)


def evaluate_quota(quota, policy_path, now):
    if not quota.get('enabled', False):
        return {'state': 'disabled'}
    try:
        snapshot_path = Path(quota['snapshot_path']).expanduser()
        if not snapshot_path.is_absolute():
            snapshot_path = policy_path.parent / snapshot_path
        snapshot, digest = read_json(snapshot_path)
        if not isinstance(snapshot, dict):
            raise ValueError('snapshot must be an object')
        # Only these scalar observations enter the audit; never retain the raw file.
        observed = timestamp(snapshot.get('observed_at'))
        start = timestamp(snapshot.get('period_start'))
        reset = timestamp(snapshot.get('resets_at'))
        used = number(snapshot.get('used_fraction'), 'used_fraction', maximum=1)
        scope = snapshot.get('scope')
        if scope not in ('shared', 'model') or not start <= observed < reset:
            raise ValueError('invalid scope or period')
        if observed > now:
            return {'state': 'unknown', 'reason': 'future_observation'}
        if (now - observed).total_seconds() > quota['max_age_seconds'] or now >= reset:
            return {'state': 'unknown', 'reason': 'stale_or_reset'}
        audit = {'state': 'normal', 'snapshot_sha256': digest, 'scope': scope,
                 'used_fraction': used, 'observed_at': observed.isoformat(),
                 'period_start': start.isoformat(), 'resets_at': reset.isoformat(),
                 'strategy': quota['strategy']}
        if scope == 'shared' and used >= 1:
            raise PolicyError('SHARED_QUOTA_EXHAUSTED',
                              'fresh shared quota is exhausted; changing models does not restore it')
        if quota['strategy'] == 'usage_threshold':
            pressure = used >= quota['used_fraction_threshold']
            audit['threshold'] = quota['used_fraction_threshold']
        else:
            elapsed = (observed - start).total_seconds()
            if elapsed <= 0 or elapsed < quota.get('min_elapsed_seconds', 0):
                return {**audit, 'state': 'unknown', 'reason': 'insufficient_elapsed_time'}
            # Linear estimate from the observation, not from the later decision time.
            projected = used * ((reset - start).total_seconds() / elapsed)
            if not math.isfinite(projected):
                return {'state': 'unknown', 'reason': 'invalid_projection'}
            audit.update(projected_fraction=projected, threshold=quota['projected_fraction_threshold'])
            pressure = projected >= quota['projected_fraction_threshold']
        audit['state'] = 'pressure' if pressure else 'normal'
        return audit
    except PolicyError:
        raise
    except (OSError, ValueError, TypeError, OverflowError, RuntimeError):
        return {'state': 'unknown', 'reason': 'missing_or_invalid_snapshot'}


def select_model(explicit=None, stage=None, policy_path=None, previous=None, now=None):
    """Return (model, audit). Fresh exhausted shared quota is a preflight block,
    not a competing model rule. Otherwise explicit > quota > stage > legacy.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    if stage is not None and stage not in STAGES:
        raise PolicyError('MODEL_STAGE_INVALID', 'unknown work stage')
    audit = {'stage': stage, 'policy_path': None, 'evaluated_at': now.isoformat(),
             'quota': {'state': 'unconfigured'}}
    config = {}
    if policy_path:
        try:
            path = Path(policy_path).expanduser().resolve()
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            raise PolicyError('MODEL_POLICY_INVALID', 'cannot resolve policy path') from exc
        config, digest = load_policy(path)
        audit.update(policy_path=str(path), policy_sha256=digest)
        audit['quota'] = evaluate_quota(config.get('quota', {}), path, now)
    if explicit is not None:
        model, source = explicit, 'explicit'
    elif audit['quota']['state'] == 'pressure':
        model, source = config['quota']['fallback_model'], 'quota'
    elif stage in config.get('stage_models', {}):
        model, source = config['stage_models'][stage], 'stage'
    elif previous:
        model, source = previous, 'previous_run'
    else:
        raise PolicyError('MODEL_REQUIRED', 'launch requires --model when no configured rule applies')
    try:
        model_id(model)
    except ValueError as exc:
        raise PolicyError('MODEL_INVALID', 'selected model ID must be a nonempty full ID without whitespace') from exc
    audit['source'] = source
    return model, audit
