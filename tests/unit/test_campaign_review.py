"""Owner-directed engineering gates never substitute for final player evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('campaign_check', ROOT / 'scripts/check_campaign.py')
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
REVISION = 'docs/campaigns/mvp/revisions/2026-10-09-owner-feedback.md'


def receipt(root, activity):
    document = root / REVISION
    document.parent.mkdir(parents=True)
    document.write_bytes((ROOT / REVISION).read_bytes())
    digest = hashlib.sha256(document.read_bytes()).hexdigest()
    result = dict(schema_version=1, activity_id=activity, outcome='pass',
                  summary='Engineering only; no player claim.', reviewer='root engineering review',
                  review_notes='Owner-authorized sequencing, without fictional participants.',
                  inputs={REVISION: digest}, artifacts=[dict(path=REVISION, sha256=digest,
                                                            kind='domain_review')],
                  limitations=['Comprehension and fun remain untested.'], participants=[],
                  acceptance_basis='engineering_and_owner_direction', scope_revision=REVISION,
                  human_validation='deferred_to_AE-029')
    path = root / f'docs/campaigns/mvp/evidence/{activity}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result))
    return path, result


@pytest.mark.parametrize('activity', ['AE-011', 'AE-019'])
def test_revised_early_gate_accepts_engineering_without_claiming_participants(tmp_path, activity):
    receipt(tmp_path, activity)
    checker.check_receipt(tmp_path, activity)


def test_revised_gate_requires_bound_owner_direction(tmp_path):
    path, result = receipt(tmp_path, 'AE-011')
    result.pop('scope_revision')
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match='scope revision'):
        checker.check_receipt(tmp_path, 'AE-011')


def test_final_player_gate_cannot_use_owner_feedback_as_participant_evidence(tmp_path):
    receipt(tmp_path, 'AE-029')
    with pytest.raises(ValueError, match='actual participant'):
        checker.check_receipt(tmp_path, 'AE-029')
