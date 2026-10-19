"""Bounded current status transaction, NOT installed origin or launch authority.

No generation rotation, archived update history or hostile rollback protection.
Cooperating namespace must stay present; atomic helper may recreate lost parents.
"""
from dataclasses import dataclass
import os

from aluclu.cognition.persistence import atomic_write_bytes
from .canonical import canonical_json_bytes,parse_canonical_json,sha256_bytes
from .control_consumption import _claim
from .deadline_file_lock import deadline_file_lock,_deadline
from .fixed_d_request_file import _local_path,_ancestors,_read_bytes
from .fixed_d_wire import _bounded_json,_hash
from .operator_status import OperatorStatus,decode_operator_status,read_operator_status
from .runtime_tree_inventory import _kind,_fingerprint,_same_open_identity

INTENT_LIMIT=16384


class StatusPublicationError(ValueError):
    """Unknown/pending/conflicting transaction, never permission to restart."""


@dataclass(frozen=True,slots=True)
class PreparedStatusIntent:
    data: bytes
    root: str


def _require(condition):
    if not condition: raise StatusPublicationError('invalid status transaction')


def _status(value):
    _require(type(value) is OperatorStatus and decode_operator_status(value.data)==value)
    return value


def _transition(previous,candidate):
    _status(candidate)
    if previous is None:
        _require(candidate.sequence==1)
    else:
        _status(previous)
        _require(previous.sequence<2**63-1 and candidate.sequence==previous.sequence+1
            and candidate.installation_root==previous.installation_root
            and candidate.generation_root==previous.generation_root
            and candidate.expires_utc_ns<=previous.expires_utc_ns
            and (not previous.revoked or candidate.revoked))


def decode_status_intent(data):
    value=_bounded_json(data,INTENT_LIMIT)
    _require(type(value) is dict and set(value)=={'schema','previous_status','candidate_status'}
             and value['schema']=='alc-r0-operator-status-intent-v1')
    previous=(None if value['previous_status'] is None else
              decode_operator_status(canonical_json_bytes(value['previous_status'])))
    candidate=decode_operator_status(canonical_json_bytes(value['candidate_status']))
    _transition(previous,candidate)
    return PreparedStatusIntent(data,sha256_bytes(data))


def prepare_status_intent(previous,candidate):
    _transition(previous,candidate)
    return decode_status_intent(canonical_json_bytes(dict(schema='alc-r0-operator-status-intent-v1',
        previous_status=None if previous is None else parse_canonical_json(previous.data),
        candidate_status=parse_canonical_json(candidate.data))))


def _parts(intent):
    _require(type(intent) is PreparedStatusIntent and decode_status_intent(intent.data)==intent)
    value=parse_canonical_json(intent.data)
    previous=(None if value['previous_status'] is None else
              decode_operator_status(canonical_json_bytes(value['previous_status'])))
    candidate=decode_operator_status(canonical_json_bytes(value['candidate_status']))
    return previous,candidate


def _present(path):
    try: path.lstat(); return True
    except FileNotFoundError: return False


def _file(value,limit):
    _require(_kind(value)=='file' and value.st_nlink==1 and 1<=value.st_size<=limit)
    return _fingerprint(value)


def _load(path,ancestors,deadline_ns):
    _deadline(deadline_ns)
    original=_file(path.lstat(),INTENT_LIMIT)
    _deadline(deadline_ns)
    with path.open('rb',buffering=0) as stream:
        _deadline(deadline_ns)
        opened=_file(os.fstat(stream.fileno()),INTENT_LIMIT)
        _require(_same_open_identity(original,opened))
        data=_read_bytes(stream,original[3],deadline_ns)
        _require(_file(os.fstat(stream.fileno()),INTENT_LIMIT)==opened)
    _deadline(deadline_ns)
    _require(_file(path.lstat(),INTENT_LIMIT)==original and _ancestors(path,deadline_ns)==ancestors)
    _deadline(deadline_ns)
    return data


@dataclass(frozen=True,slots=True)
class StatusPublicationStore:
    directory: object
    installation_root: str
    generation_root: str

    def __post_init__(self):
        object.__setattr__(self,'directory',_local_path(self.directory))
        _hash(self.installation_root); _hash(self.generation_root)

    def _paths(self,deadline_ns):
        _deadline(deadline_ns)
        _require(_kind(self.directory.lstat())=='directory'
                 and self.directory.resolve(strict=True)==self.directory)
        status=self.directory/'status.json'
        intent=self.directory/'status.intent.json'
        ancestors=_ancestors(status,deadline_ns)
        _require(_ancestors(intent,deadline_ns)==ancestors)
        return intent,status,ancestors

    def _bound(self,intent):
        previous,candidate=_parts(intent)
        _require(candidate.installation_root==self.installation_root
                 and candidate.generation_root==self.generation_root)
        return previous,candidate

    def _committed(self,ancestors,deadline_ns):
        path=self.directory/'status.intent.json'
        first=decode_status_intent(_load(path,ancestors,deadline_ns))
        _,candidate=self._bound(first)
        actual=read_operator_status(self.directory/'status.json',deadline_ns=deadline_ns)
        _require(_ancestors(path,deadline_ns)==ancestors)
        second=decode_status_intent(_load(path,ancestors,deadline_ns))
        _require(first==second and actual==candidate)
        _require(_ancestors(path,deadline_ns)==ancestors)
        _deadline(deadline_ns)
        return actual

    def read(self,*,deadline_ns):
        _,_,ancestors=self._paths(deadline_ns)
        return self._committed(ancestors,deadline_ns)

    def _write(self,path,data,ancestors,deadline_ns):
        _deadline(deadline_ns)
        _require(_ancestors(path,deadline_ns)==ancestors)
        atomic_write_bytes(path,data)
        _deadline(deadline_ns)
        _require(_ancestors(path,deadline_ns)==ancestors)

    def _persist_intent(self,intent,ancestors,deadline_ns):
        path=self.directory/'status.intent.json'
        self._write(path,intent.data,ancestors,deadline_ns)
        _require(_load(path,ancestors,deadline_ns)==intent.data)

    def publish(self,intent,*,deadline_ns):
        previous,candidate=self._bound(intent)
        self._paths(deadline_ns)
        with deadline_file_lock(self.directory/'operator.lock',deadline_ns):
            path,status,ancestors=self._paths(deadline_ns)
            if previous is None:
                _require(not _present(status) and not _present(path))
                claimed=_claim(path,deadline_ns)
                _require(_ancestors(path,deadline_ns)==ancestors
                         and _fingerprint(path.lstat())==claimed)
            else:
                _require(self._committed(ancestors,deadline_ns)==previous)
            self._persist_intent(intent,ancestors,deadline_ns)
            self._write(status,candidate.data,ancestors,deadline_ns)
            actual=self._committed(ancestors,deadline_ns)
            _require(actual==candidate)
        _deadline(deadline_ns)  # unlock/handle cleanup must not hide late success
        return actual

    def recover(self,intent,*,deadline_ns):
        previous,candidate=self._bound(intent)
        self._paths(deadline_ns)
        with deadline_file_lock(self.directory/'operator.lock',deadline_ns):
            path,status,ancestors=self._paths(deadline_ns)
            _require(_load(path,ancestors,deadline_ns)==intent.data)
            observed=(read_operator_status(status,deadline_ns=deadline_ns)
                      if _present(status) else None)
            _require(_ancestors(status,deadline_ns)==ancestors
                     and observed in (previous,candidate))
            if observed!=candidate: self._write(status,candidate.data,ancestors,deadline_ns)
            actual=self._committed(ancestors,deadline_ns)
            _require(actual==candidate)
        _deadline(deadline_ns)
        return actual


def read_committed_operator_status(directory,installation_root,generation_root,*,deadline_ns):
    """Committed transport observation, not authenticated origin/freshness."""
    return StatusPublicationStore(directory,installation_root,generation_root).read(deadline_ns=deadline_ns)
