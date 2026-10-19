import hashlib
from dataclasses import asdict

import pytest

from aluclu.alc_r0.attempt_journal import AttemptJournal
from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.manifest_publication import (
    ManifestOwner,
    PublicationConflict,
    PublicationError,
    prepare_publication,
)
from aluclu.alc_r0.paged_history import declaration_root, page_identity

ROOT = "a" * 64
SPEC = RunSpec("alc-r0-v1-dev-publication-s20260916", False, ("w1",))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest(heads=()):
    data = canonical_json_bytes(
        dict(
            version=1,
            spec_sha256=declaration_root(SPEC),
            pages=[asdict(h) for h in heads],
        )
    )
    return data, digest(data)


def event(source=ROOT):
    return canonical_json_bytes(
        dict(
            run_id=SPEC.run_id,
            attempt_id="a001",
            kind="intent",
            source_sha256=source,
            invocation_sha256=ROOT,
            retry_kind="INITIAL",
            prior_source_sha256=None,
            prior_artifact_sha256=None,
            review_sha256=None,
        )
    )


def setup(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    old = owner.create()
    journal = AttemptJournal(
        pages / "page-0000.jsonl", page_identity(declaration_root(SPEC), 0, None)
    )
    head = journal.append(journal.create(), event())
    data, root = manifest((head,))
    prepared = prepare_publication(SPEC, old.data, old.sha256, data, root, ROOT)
    return owner, old, prepared, journal, head


def test_genesis_is_explicit_empty_and_never_overwritten(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    receipt = owner.create()
    assert receipt.view.state == "UNSTARTED"
    assert parse_canonical_json(receipt.data)["generation"] == 0
    assert owner.read(receipt.sha256) == receipt
    with pytest.raises(FileExistsError):
        owner.create()


def test_publish_restart_and_explicit_reconcile_keep_exact_generation(tmp_path):
    owner, old, prepared, _, _ = setup(tmp_path)
    new = owner.publish(prepared)
    restarted = ManifestOwner(owner.path, owner.pages, SPEC)
    assert restarted.read(new.sha256) == new
    assert new.data == prepared.candidate
    assert parse_canonical_json(new.data)["generation"] == 1
    with pytest.raises(PublicationConflict):
        restarted.publish(prepared)
    assert restarted.reconcile(prepared) == new
    assert restarted.reconcile(prepared) == new
    with pytest.raises(PublicationConflict):
        restarted.read(old.sha256)


def test_reconcile_never_publishes_unseen_candidate(tmp_path):
    owner, old, prepared, _, _ = setup(tmp_path)
    with pytest.raises(PublicationConflict):
        owner.reconcile(prepared)
    assert owner.path.read_bytes() == old.data


def test_failed_page_verification_preserves_old_owner(tmp_path):
    owner, old, prepared, journal, _ = setup(tmp_path)
    journal.path.write_bytes(b"truncated")  # Own corruption fixture only.
    with pytest.raises((PublicationError, ValueError, RuntimeError)):
        owner.publish(prepared)
    assert owner.path.read_bytes() == old.data


@pytest.mark.parametrize(
    "mutation", ["root", "review", "bool_generation", "extra", "noop"]
)
def test_prepare_rejects_invalid_inputs_without_io(tmp_path, mutation):
    owner, old, prepared, _, _ = setup(tmp_path)
    current = parse_canonical_json(old.data)
    candidate = canonical_json_bytes(
        parse_canonical_json(prepared.candidate)["manifest"]
    )
    old_root, review = old.sha256, ROOT
    if mutation == "root":
        old_root = "b" * 64
    elif mutation == "review":
        review = None
    elif mutation == "bool_generation":
        current["generation"] = False
    elif mutation == "extra":
        current["extra"] = 1
    else:
        candidate = manifest()[0]
    previous = canonical_json_bytes(current)
    if mutation != "root":
        old_root = digest(previous)
    with pytest.raises((PublicationError, ValueError)):
        prepare_publication(
            SPEC, previous, old_root, candidate, digest(candidate), review
        )
    assert owner.path.read_bytes() == old.data


def test_forged_prepared_candidate_is_not_a_capability_token(tmp_path):
    from dataclasses import replace

    owner, old, prepared, _, _ = setup(tmp_path)
    forged = replace(prepared, candidate=old.data)
    with pytest.raises(PublicationError):
        owner.publish(forged)
    assert owner.path.read_bytes() == old.data


def test_owner_cannot_live_inside_closed_page_namespace(tmp_path):
    with pytest.raises(PublicationError):
        ManifestOwner(tmp_path / "owner.json", tmp_path, SPEC)


@pytest.mark.parametrize("field,value", [("generation", 2), ("previous", "b" * 64)])
def test_rehashed_forged_transition_rejected_by_reconstruction(tmp_path, field, value):
    from dataclasses import replace

    owner, old, prepared, _, _ = setup(tmp_path)
    changed = parse_canonical_json(prepared.candidate)
    changed[field] = value
    data = canonical_json_bytes(changed)
    forged = replace(prepared, candidate=data, candidate_sha256=digest(data))
    with pytest.raises(PublicationError, match="exact transition"):
        owner.publish(forged)
    assert owner.path.read_bytes() == old.data


def test_controlled_lock_removal_mutant_acknowledges_twice(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import nullcontext
    from threading import Barrier

    owner, _, prepared, _, _ = setup(tmp_path)
    both_read = Barrier(2)

    class UnlockedMutant(ManifestOwner):
        def _lock(self):
            return nullcontext()

        def _load(self):
            observed = super()._load()
            both_read.wait(timeout=10)
            return observed

    def contender(_):
        return UnlockedMutant(owner.path, owner.pages, SPEC).publish(prepared)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(contender, range(2)))
    assert len(results) == 2  # Negative control breaks exactly-once CAS.
    assert all(result.data == prepared.candidate for result in results)
    assert owner.path.read_bytes() == prepared.candidate


@pytest.mark.parametrize("content", [b"", b"{}", b"x" * 16385])
def test_bad_owner_never_reset_or_adopted(tmp_path, content):
    owner, old, _, _, _ = setup(tmp_path)
    owner.path.write_bytes(content)  # Own malformed fixture.
    with pytest.raises((PublicationError, PublicationConflict)):
        owner.read(old.sha256)
    assert owner.path.read_bytes() == content


def test_two_cooperating_publishers_acknowledge_only_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    owner, _, prepared, _, _ = setup(tmp_path)
    barrier = Barrier(2)

    def contender():
        other = ManifestOwner(owner.path, owner.pages, SPEC)
        barrier.wait(timeout=10)
        try:
            return other.publish(prepared)
        except PublicationConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: contender(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert owner.path.read_bytes() == prepared.candidate
    assert parse_canonical_json(prepared.candidate)["generation"] == 1


def test_valid_rewritten_page_cannot_be_published(tmp_path):
    owner, old, _, journal, head = setup(tmp_path)
    # Publish the actual first intent, then prepare a valid but rewritten history.
    data, root = manifest((head,))
    current = owner.publish(
        prepare_publication(SPEC, old.data, old.sha256, data, root, ROOT)
    )
    journal.path.unlink()  # Own adversarial fixture only, never production recovery.
    head = journal.append(journal.create(), event("b" * 64))
    start = canonical_json_bytes(
        dict(run_id=SPEC.run_id, attempt_id="a001", kind="start", receipt_sha256=ROOT)
    )
    head = journal.append(head, start)
    data, root = manifest((head,))
    altered = prepare_publication(SPEC, current.data, current.sha256, data, root, ROOT)
    with pytest.raises(ValueError, match="prefix"):
        owner.publish(altered)
    assert owner.path.read_bytes() == current.data


@pytest.mark.parametrize("target", ["owner", "lock"])
def test_hardlinked_owner_or_lock_rejected_before_write(tmp_path, target):
    import os

    owner, old, prepared, _, _ = setup(tmp_path)
    path = (
        owner.path
        if target == "owner"
        else owner.path.with_name(owner.path.name + ".lock")
    )
    os.link(path, tmp_path / "alias")
    with pytest.raises(PublicationError, match="single-link"):
        owner.publish(prepared)
    assert owner.path.read_bytes() == old.data


@pytest.mark.parametrize("boundary", ["before", "after"])
def test_fresh_process_exit_preserves_exact_old_or_new_owner(tmp_path, boundary):
    import subprocess
    import sys

    owner, old, prepared, _, _ = setup(tmp_path)
    # Child receives only this synthetic prepared transition, no model/assets.
    program = """
import os, sys
from pathlib import Path
from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.manifest_publication import ManifestOwner, PreparedPublication
owner = ManifestOwner(Path(sys.argv[1]), Path(sys.argv[2]), RunSpec(sys.argv[3], False, ('w1',)))
p = PreparedPublication(bytes.fromhex(sys.argv[4]), sys.argv[5], bytes.fromhex(sys.argv[6]), sys.argv[7])
if sys.argv[8] == 'after':
    owner.publish(p)
os._exit(73)
"""
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            program,
            str(owner.path),
            str(owner.pages),
            SPEC.run_id,
            old.data.hex(),
            old.sha256,
            prepared.candidate.hex(),
            prepared.candidate_sha256,
            boundary,
        ],
        capture_output=True,
        timeout=45,
    )
    assert result.returncode == 73, result.stderr.decode(errors="replace")
    expected = old.data if boundary == "before" else prepared.candidate
    assert owner.path.read_bytes() == expected
    if boundary == "after":
        assert (
            ManifestOwner(owner.path, owner.pages, SPEC).reconcile(prepared).data
            == expected
        )
    else:
        with pytest.raises(PublicationConflict):
            owner.reconcile(prepared)


@pytest.mark.parametrize(
    "stage", ["temp_write", "temp_fsync", "pre_replace", "post_replace", "pre_receipt"]
)
@pytest.mark.parametrize("mode", ["fault", "kill"])
def test_actual_atomic_writer_boundaries_keep_exact_owner(tmp_path, stage, mode):
    import json
    import os
    import subprocess
    import sys
    import sysconfig
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    owner, old, prepared, _, _ = setup(tmp_path)
    checkout = Path(__file__).resolve().parents[1]
    helper = checkout / "tests/helpers/manifest_publication_boundary_child.py"
    args = [
        sys._base_executable,
        "-B",
        str(helper),
        str(owner.path),
        str(owner.pages),
        SPEC.run_id,
        old.data.hex(),
        old.sha256,
        prepared.candidate.hex(),
        prepared.candidate_sha256,
        stage,
        mode,
        str(checkout),
    ]
    # Windows venv executable redirects into another PID. Launch actual base
    # interpreter with explicit SAME already-installed package paths; no installs.
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys(
            [
                str(checkout / "src"),
                sysconfig.get_paths()["purelib"],
                sysconfig.get_paths()["platlib"],
            ]
        )
    )
    child = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    with ThreadPoolExecutor(max_workers=1) as reader:
        try:
            line = reader.submit(child.stdout.readline).result(timeout=45)
            marker = json.loads(line)
            assert marker["stage"] == stage and marker["mode"] == mode
            assert marker["pid"] == child.pid
            assert marker["python_version"] == sys.version
            assert (
                Path(marker["python_executable"]).resolve()
                == Path(sys._base_executable).resolve()
            )
            source = checkout / "src/aluclu/cognition/persistence.py"
            assert Path(marker["source"]) == source
            assert marker["source_sha256"] == digest(source.read_bytes())
            if mode == "kill":
                assert child.poll() is None
                child.kill()  # Exact Popen-owned child only.
            stdout, stderr = child.communicate(timeout=15)
            if mode == "fault":
                assert child.returncode == 74, stderr.decode(errors="replace")
                assert b"receipt=false" in stdout
            else:
                assert child.returncode != 0
                assert b"receipt=false" not in stdout
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=15)
    candidate_visible = stage in {"post_replace", "pre_receipt"}
    expected = prepared.candidate if candidate_visible else old.data
    assert owner.path.read_bytes() == expected
    if candidate_visible:
        reconciled = ManifestOwner(owner.path, owner.pages, SPEC).reconcile(prepared)
        assert (
            reconciled.data == expected
            and reconciled.sha256 == prepared.candidate_sha256
        )
        assert parse_canonical_json(reconciled.data)["generation"] == 1
    else:
        with pytest.raises(PublicationConflict):
            owner.reconcile(prepared)
        assert owner.path.read_bytes() == old.data
