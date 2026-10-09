"""Bounded AE-011 text projection of saved AE-010 facts; no world inference.

The study's delivery desk sees declared goals/work, decision provenance, delivery
and assurance records, and OutcomeObserved after its recorded tick. It has no
knowledge-catalog, world-outcome, incident or payment-attempt access. This is a
study projection, not a general actor snapshot or an authorization service.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'research/experiments/AE-010/causal-traces.json'
RELATIONS = {'direct_cause', 'supporting_evidence', 'association'}
CHOICES = {
    'retryable_types': {'transient_only': 'transient failures only', 'all_failures': 'all failures',
                        'selected_categories': 'selected categories'},
    'retry_count': {'none': 'no retries', 'one': 'one retry', 'three': 'three retries', 'adaptive': 'adaptive'},
    'backoff': {'immediate': 'immediate', 'fixed': 'fixed delay', 'capped_exponential': 'capped exponential delay'},
    'idempotency': {'stable_key': 'reuse an operation key', 'new_key': 'new operation key per retry',
                    'unspecified': 'unspecified operation key'},
    'declined_handling': {'do_not_retry': 'no decline retries', 'soft_only': 'soft declines only',
                         'retry_all': 'all declines'},
    'audit_requirement': {'attempt_lineage': 'attempt lineage', 'summary_only': 'summary only', 'no_audit': 'no audit'},
}
DIMENSIONS = {'implementation_conformance', 'verification_status', 'requirement_conformance',
              'architecture_conformance', 'policy_security_conformance', 'validation_status', 'outcome_fitness'}
PUBLIC_TYPES = {'GoalDeclared', 'WorkItemCreated', 'DecisionRequired', 'DecisionSelected',
                'DecisionRevised', 'AssumptionMade', 'WorkStarted', 'ChangeProposalCreated',
                'VerificationCompleted', 'DeploymentCompleted', 'OutcomeObserved'}
CASES = {'A': 'boundary/harmful_human', 'B': 'boundary/harmless_unsupported'}


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return value


def _index(history):
    if history.get('history_schema_version') != 1:
        raise ValueError('unsupported history schema')
    indexed, sequences = {}, set()
    for event in history['events']:
        identity = event['event_id']
        if not isinstance(identity, str) or not identity.strip() or identity in indexed:
            raise ValueError('invalid or duplicate event ID')
        sequence = _integer(event['sequence'], 'sequence')
        _integer(event['tick'], 'tick')
        if sequence in sequences or event['schema_version'] != 1:
            raise ValueError('duplicate sequence or unsupported event schema')
        sequences.add(sequence)
        indexed[identity] = event
    previous_tick = 0
    for event in sorted(indexed.values(), key=lambda e: e['sequence']):
        if event['tick'] < previous_tick:
            raise ValueError('event time goes backwards')
        previous_tick = event['tick']
        links = set()
        for link in event['parents']:
            parent = indexed.get(link['event_id'])
            pair = (link['event_id'], link['relation'])
            if parent is None or parent['sequence'] >= event['sequence']:
                raise ValueError('missing or non-earlier parent')
            if link['relation'] not in RELATIONS or pair in links:
                raise ValueError('invalid or duplicate relation')
            links.add(pair)
    return indexed


def causal_events(history, roots):
    """Union of ancestors in original total order; never equate edge types."""
    indexed = _index(history)
    pending, selected = list(roots), set()
    if any(root not in indexed for root in pending):
        raise ValueError('unknown root')
    while pending:
        identity = pending.pop()
        if identity in selected:
            continue
        selected.add(identity)
        pending.extend(link['event_id'] for link in indexed[identity]['parents'])
    return sorted((indexed[i] for i in selected), key=lambda e: e['sequence'])


def _enum(value, allowed):
    if value not in allowed:
        raise ValueError('unsupported public value')
    return value.replace('_', ' ')


def _decision_name(value):
    return _enum(value, CHOICES)


def _pinned_choices(payload):
    refs = payload.get('decision_refs', [])
    return ', '.join(f"{_decision_name(r['entity_id'])} v{_integer(r['version'], 'version', 1)}"
                     for r in refs if r['entity_type'] == 'decision') or 'not recorded'


def _public_summary(event):
    """Allowlist fields, not raw payload/metadata dumps or secret string filters."""
    kind, p = event['event_type'], event['payload']
    if kind == 'GoalDeclared':
        return (f"Goal: {p['intent']} Measure: {p['measure'].replace('_', ' ')}; "
                f"target {p['target']}; window {p['observation_window']} ticks.")
    if kind == 'WorkItemCreated':
        return f"Work item: {p['text']}"
    if kind == 'DecisionRequired':
        return f"Choice required: {_decision_name(p['decision_id'])}."
    if kind in ('DecisionSelected', 'DecisionRevised'):
        name = p['decision_id']
        label = CHOICES[name][p['selected']]
        version = _integer(p['version'], 'decision version', 1)
        authority = _enum(p['authority_basis'], {'explicit_authorization', 'policy_constraint',
            'delegated_discretion', 'inferred_without_authority', 'unresolved', 'conflicted'})
        support = _enum(p['support'], {'none', 'supported', 'conflicted', 'challenged', 'inconclusive', 'weak'})
        confidence = _enum(p['confidence'], {'unknown', 'low', 'medium', 'high'})
        return (f"Choice {_decision_name(name)} v{version}: {label}; authority: {authority}; "
                f"evidence support: {support}; stated confidence: {confidence}.")
    if kind == 'AssumptionMade':
        labels = {'no_authority_claimed': 'authority not recorded',
                  'insufficient_independent_support': 'independent support incomplete',
                  'missing_information': 'information missing'}
        # Unknown gap contents and missing-information references remain private.
        gaps = '; '.join(labels[g] for g in p['gaps'] if g in labels) or 'unclassified gap'
        return f"Recorded gaps for {_decision_name(p['decision_id'])} v{_integer(p['version'], 'version', 1)}: {gaps}."
    if kind == 'WorkStarted':
        return f"Work started; pinned choices: {_pinned_choices(p)}."
    if kind == 'ChangeProposalCreated':
        return f"Change proposal created; pinned choices: {_pinned_choices(p)}."
    if kind == 'VerificationCompleted':
        assessments = []
        for assessment in p['assessments']:
            if assessment['dimension'] in DIMENSIONS:
                status = _enum(assessment['status'], {'pass', 'fail', 'unknown', 'pending', 'conflicted'})
                assessments.append(f"{assessment['dimension'].replace('_', ' ')}: {status}")
        return 'Checks recorded: ' + '; '.join(assessments) + '.'
    if kind == 'DeploymentCompleted':
        return f"Proposal shipped; pinned choices: {_pinned_choices(p)}."
    if kind == 'OutcomeObserved':
        complete = p['completed']
        abandoned = p['abandoned']
        if type(complete) is not bool or type(abandoned) is not bool:
            raise ValueError('observation flags must be boolean')
        duplicates = _integer(p['duplicate_charges'], 'duplicate charges')
        outcome_tick = _integer(p['outcome_tick'], 'outcome tick')
        return (f"Observation received for outcome at tick {outcome_tick}: "
                f"completed: {str(complete).lower()}; abandoned: {str(abandoned).lower()}; "
                f"duplicate charges: {duplicates}; pinned choices: {_pinned_choices(p)}.")
    raise ValueError('no public summary for event type')


def render_trace(history, *, roots=None, view='player', at_tick=0):
    """Render typed ancestors; private nodes stay unavailable, never bridged."""
    _integer(at_tick, 'at_tick')
    if view not in ('player', 'audit'):
        raise ValueError('unknown view')
    indexed = _index(history)
    available = {identity for identity, e in indexed.items() if e['tick'] <= at_tick
                 and (view == 'audit' or e['event_type'] in PUBLIC_TYPES)}
    if roots is None:
        roots = sorted(available, key=lambda i: indexed[i]['sequence'])
    if any(root not in indexed for root in roots):
        raise ValueError('unknown root')
    if any(root not in available for root in roots):
        raise ValueError('unavailable root')
    selected = [e for e in causal_events(history, roots) if e['event_id'] in available]
    if view == 'audit':
        return json.dumps(dict(history_schema_version=1, run_id=history['run_id'], events=selected),
                          indent=2, sort_keys=True, allow_nan=False) + '\n'
    labels = {e['event_id']: f'N{number}' for number, e in enumerate(selected, 1)}
    lines = [f'# Delivery records through tick {at_tick}', '',
             'Links retain recorded relations: direct cause, supporting evidence, or association.',
             'An unavailable antecedent has no content in this view.', '']
    if not selected:
        lines.append('No records available.')
    for e in selected:
        parents = [link['relation'].replace('_', ' ') + ': ' +
                   labels.get(link['event_id'], 'unavailable antecedent') for link in e['parents']]
        suffix = ' Links: ' + '; '.join(parents) + '.' if parents else ''
        lines.append(f"- {labels[e['event_id']]} | tick {e['tick']} | {_public_summary(e)}{suffix}")
    return '\n'.join(lines) + '\n'


READER_INSTRUCTIONS = """# PaymentCo readback

PaymentCo is fictional. Its work item is to retry failed payments. Read the records
as an observer of the delivery desk. A tick is a unit of simulation time. A payment
operation key identifies an operation across attempts. The desk can see recorded
choices and checks; feedback arrives later. The records do not include everyone's
private information. There is no single required wording for your answers.

Read case A at shipping, before feedback, and answer the first prompt. Then read case A after
feedback and answer the remaining prompts. Freeze those answers before reading
case B. Use the same prompts for B, then describe any difference in your conclusions.

Before feedback: What do you expect to happen? What, if anything, would you want to
know or do before proceeding?

After feedback:
1. In your own words, what happened? Which records connect to your explanation?
2. What would you change, if anything, and why? What result would you expect, and
   what information would you need?
3. What can you conclude from these records, and what remains uncertain?
4. Which parts were confusing? Do you disagree with any part of the record?
"""


def author_packet(source, directory):
    """Author fixed retained cases once, with facilitator/audit material separate."""
    source, directory = Path(source), Path(directory)
    traces = json.loads(source.read_bytes())['traces']
    # Preflight rendering before creating files, including both complete audits.
    outputs = {'reader/instructions.md': READER_INSTRUCTIONS}
    manifest = dict(source='research/experiments/AE-010/causal-traces.json',
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), cases=CASES,
                    projection='delivery-desk-v1', before_tick=1, after_tick=8,
                    selection='AE-010 predeclared harmful/harmless boundaries; no population representativeness')
    for label, key in CASES.items():
        graph = traces[key]
        for phase, tick in (('before', 1), ('after', 8)):
            outputs[f'reader/case-{label}-{phase}.md'] = render_trace(graph, at_tick=tick)
        last_tick = max(e['tick'] for e in graph['events'])
        outputs[f'audit/case-{label}.json'] = render_trace(graph, view='audit', at_tick=last_tick)
    outputs['audit/manifest.json'] = json.dumps(manifest, indent=2, sort_keys=True) + '\n'
    directory.mkdir(parents=True, exist_ok=False)
    for name, text in outputs.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def verify_packet(source, directory):
    with tempfile.TemporaryDirectory() as temporary:
        fresh = Path(temporary) / 'packet'
        author_packet(source, fresh)
        expected = {p.relative_to(fresh) for p in fresh.rglob('*') if p.is_file()}
        actual = {p.relative_to(directory) for p in directory.rglob('*') if p.is_file()}
        if actual != expected or any((fresh / p).read_bytes() != (directory / p).read_bytes() for p in expected):
            raise ValueError('packet differs from regenerated evidence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--packet-dir', type=Path)
    action.add_argument('--verify-against', type=Path)
    action.add_argument('--case')
    parser.add_argument('--view', choices=('player', 'audit'), default='player')
    parser.add_argument('--at-tick', type=int, default=0)
    parser.add_argument('--root', action='append')
    args = parser.parse_args()
    if args.packet_dir:
        author_packet(args.source, args.packet_dir)
        print('PASS: reader and audit packets authored; no participant responses')
    elif args.verify_against:
        verify_packet(args.source, args.verify_against)
        print('PASS: packet reproduced without overwriting evidence')
    else:
        graph = json.loads(args.source.read_bytes())['traces'][args.case]
        print(render_trace(graph, roots=args.root, view=args.view, at_tick=args.at_tick), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
