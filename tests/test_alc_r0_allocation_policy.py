"""Synthetic arithmetic only; no historical observations or launch authority."""

import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from aluclu.alc_r0.allocation_policy import (
    AllocationAccounting, AllocationRequest, assess_allocation,
)

NS = 10**9
HOUR = 3600 * NS
DAY = 86400 * NS
GIB = 1 << 30
MAX = (1 << 63) - 1


def accounting(**changes):
    values = dict(policy_root="a"*64,coverage_root="b"*64,
        charge_kind="observed",effective_gpu_ns=HOUR,
        clock_kind="observed",clock_utc_ns=DAY)
    return AllocationAccounting(**(values | changes))


def request(**changes):
    values = dict(accounting=accounting(),phase="D",device="gpu",now_utc_ns=2*DAY,
        entry_monotonic_ns=NS,now_monotonic_ns=2*NS,research_bytes=4*GIB,
        free_c_bytes=30*GIB,projected_research_growth_bytes=GIB,
        projected_physical_growth_bytes=GIB,pending_research_growth_bytes=GIB,
        pending_physical_growth_bytes=GIB,pending_gpu_ns=HOUR)
    return AllocationRequest(**(values | changes))


def test_full_reserved_tail_and_original_origin_no_authority():
    result = assess_allocation(request())
    assert result.resource_fit and result.reasons == ()
    assert result.required_gpu_reservation_ns == 45*60*NS + 10*NS
    assert result.useful_deadline_monotonic_ns == NS + 45*60*NS
    assert result.cleanup_deadline_monotonic_ns == NS + 45*60*NS + 10*NS
    assert result.remaining_gpu_ns == 598*HOUR
    assert result.program_deadline_utc_ns == 46*DAY
    for name in ("launch_authority","training_authority","reservation","verified_context"):
        assert not hasattr(result,name)


@pytest.mark.parametrize("kind", ["observed","allocation_upper_bound"])
@pytest.mark.parametrize("clock", ["observed","conservative_boundary"])
def test_kinds_retained_not_relabelled(kind,clock):
    original = request(accounting=accounting(charge_kind=kind,clock_kind=clock))
    assert assess_allocation(original).resource_fit
    assert original.accounting.charge_kind == kind and original.accounting.clock_kind == clock


@pytest.mark.parametrize("phase,minutes", [("D",45),("E1",30),("E2",10),("E3",30),("pilot",120)])
def test_fixed_single_job_ceilings_with_one_tail(phase,minutes):
    result = assess_allocation(request(phase=phase))
    assert result.required_gpu_reservation_ns == (minutes*60 + 10)*NS


def test_cpu_zero_gpu_but_unknown_history_still_denies():
    assert assess_allocation(request(device="cpu")).required_gpu_reservation_ns == 0
    result = assess_allocation(request(device="cpu",
        accounting=accounting(charge_kind="unknown",effective_gpu_ns=None)))
    assert not result.resource_fit and result.remaining_gpu_ns is None
    assert result.reasons == ("history-unreconciled",)
    assert result.program_deadline_utc_ns == 46*DAY


@pytest.mark.parametrize("phase", ["E1","E2","E3","pilot"])
def test_no_implicit_cpu_route(phase):
    with pytest.raises(ValueError):
        assess_allocation(request(phase=phase,device="cpu"))


@pytest.mark.parametrize("field", ["policy_root","coverage_root"])
def test_missing_provenance_denies_not_zero_history(field):
    result = assess_allocation(request(accounting=accounting(**{field:None})))
    assert not result.resource_fit and result.remaining_gpu_ns is None
    assert "history-unreconciled" in result.reasons


@pytest.mark.parametrize("clock", ["prospective_pending","unknown"])
def test_pending_clock_does_not_start_new_window(clock):
    result = assess_allocation(request(accounting=accounting(clock_kind=clock,clock_utc_ns=None)))
    assert not result.resource_fit and result.program_deadline_utc_ns is None
    assert result.remaining_gpu_ns == 598*HOUR
    assert result.reasons == ("clock-unreconciled",)


def test_unknown_charge_does_not_hide_known_expired_calendar():
    result = assess_allocation(request(now_utc_ns=46*DAY,
        accounting=accounting(charge_kind="unknown",effective_gpu_ns=None)))
    assert result.reasons == ("history-unreconciled","program-window-invalid")
    assert result.program_deadline_utc_ns == 46*DAY and result.remaining_gpu_ns is None


def test_unknown_clock_does_not_hide_known_exhausted_budget():
    result = assess_allocation(request(accounting=accounting(effective_gpu_ns=601*HOUR,
        clock_kind="unknown",clock_utc_ns=None)))
    assert result.reasons == ("clock-unreconciled","gpu-budget-insufficient")
    assert result.remaining_gpu_ns == -2*HOUR


def test_charge_aggregate_overflow_keeps_provable_budget_denial():
    result = assess_allocation(request(accounting=accounting(effective_gpu_ns=MAX),
        pending_gpu_ns=MAX))
    assert result.remaining_gpu_ns is None
    assert result.reasons == ("gpu-budget-insufficient","resource-arithmetic-overflow")


@pytest.mark.parametrize("offset", [0,1,-1])
def test_budget_boundary_includes_cleanup_tail(offset):
    required = 45*60*NS + 10*NS
    result = assess_allocation(request(pending_gpu_ns=599*HOUR-required+offset))
    assert result.resource_fit is (offset <= 0)
    assert result.remaining_gpu_ns == required-offset


@pytest.mark.parametrize("offset", [0,1,-1])
def test_calendar_boundary_uses_remaining_work_plus_cleanup(offset):
    remaining = 45*60*NS - NS + 10*NS
    result = assess_allocation(request(now_utc_ns=46*DAY-remaining+offset))
    assert result.resource_fit is (offset <= 0)


def test_elapsed_preflight_never_renews_useful_allowance():
    original = request()
    later = replace(original,now_monotonic_ns=original.now_monotonic_ns+10*NS,
                    now_utc_ns=original.now_utc_ns+10*NS)
    first,second = assess_allocation(original),assess_allocation(later)
    assert first.useful_deadline_monotonic_ns == second.useful_deadline_monotonic_ns
    assert first.cleanup_deadline_monotonic_ns == second.cleanup_deadline_monotonic_ns


@pytest.mark.parametrize("now", [0,NS+45*60*NS,NS+45*60*NS+1])
def test_backwards_or_exhausted_monotonic_denies(now):
    result = assess_allocation(request(now_monotonic_ns=now))
    assert not result.resource_fit and "monotonic-window-invalid" in result.reasons


def test_original_deadline_overflow_explicit():
    result = assess_allocation(request(entry_monotonic_ns=MAX,now_monotonic_ns=MAX))
    assert result.useful_deadline_monotonic_ns is None
    assert result.cleanup_deadline_monotonic_ns is None
    assert "resource-arithmetic-overflow" in result.reasons
    assert "monotonic-window-invalid" in result.reasons


def test_calendar_overflow_explicit():
    result = assess_allocation(request(now_utc_ns=MAX,
        accounting=accounting(clock_utc_ns=MAX)))
    assert result.program_deadline_utc_ns is None
    assert "program-window-invalid" in result.reasons
    assert "resource-arithmetic-overflow" in result.reasons


def test_research_and_physical_growth_are_not_interchangeable():
    result = assess_allocation(request(research_bytes=23*GIB,
        free_c_bytes=22*GIB))
    assert result.resource_fit
    result = assess_allocation(request(research_bytes=23*GIB,
        projected_physical_growth_bytes=20*GIB))
    assert result.reasons == ("c-free-space-insufficient",)
    result = assess_allocation(request(projected_research_growth_bytes=21*GIB))
    assert result.reasons == ("research-storage-insufficient",)


def test_storage_overflow_explicit_with_unknown_history():
    result = assess_allocation(request(accounting=accounting(charge_kind="unknown",
        effective_gpu_ns=None),research_bytes=MAX,pending_research_growth_bytes=MAX,
        projected_research_growth_bytes=MAX))
    assert result.reasons == ("history-unreconciled","resource-arithmetic-overflow",
                              "research-storage-insufficient")


@pytest.mark.parametrize("field", ["now_utc_ns","entry_monotonic_ns","now_monotonic_ns",
    "research_bytes","free_c_bytes","projected_research_growth_bytes",
    "projected_physical_growth_bytes","pending_research_growth_bytes",
    "pending_physical_growth_bytes","pending_gpu_ns"])
@pytest.mark.parametrize("value", [True,-1,1.0,None,MAX+1])
def test_exact_numeric_observations(field,value):
    with pytest.raises(ValueError):
        assess_allocation(request(**{field:value}))


@pytest.mark.parametrize("changes", [dict(charge_kind="unknown"),
    dict(effective_gpu_ns=None),dict(clock_kind="unknown"),dict(clock_utc_ns=None),
    dict(policy_root="A"*64),dict(coverage_root="b"*63),dict(effective_gpu_ns=True),
    dict(clock_utc_ns=1.0),dict(charge_kind=True),dict(clock_kind="today")])
def test_malformed_accounting_combinations(changes):
    with pytest.raises(ValueError):
        assess_allocation(request(accounting=accounting(**changes)))


@pytest.mark.parametrize("changes", [dict(phase="qv"),dict(phase=True),dict(device="cuda"),
    dict(accounting={})])
def test_malformed_request_modes(changes):
    with pytest.raises(ValueError):
        assess_allocation(request(**changes))
    with pytest.raises(ValueError):
        assess_allocation({})


def test_immutable_records_and_known_zero():
    original = request(accounting=accounting(effective_gpu_ns=0,clock_utc_ns=0),
        now_utc_ns=0,pending_gpu_ns=0)
    result = assess_allocation(original)
    assert result.resource_fit and result.remaining_gpu_ns == 600*HOUR
    with pytest.raises(FrozenInstanceError):
        original.accounting.effective_gpu_ns = HOUR
    with pytest.raises(FrozenInstanceError):
        result.resource_fit = False


def test_fresh_process_stdlib_import_and_unknown_denial():
    source = Path(__file__).resolve().parents[1] / "src"
    environment = dict(os.environ,PYTHONPATH=str(source),PYTHONNOUSERSITE="1",
                       CUDA_VISIBLE_DEVICES="-1")
    script = """
import importlib.abc,sys
blocked={'torch','transformers','numpy','rfc8785','cryptography','safetensors'}
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in blocked:raise AssertionError('heavy import')
sys.meta_path.insert(0,Guard())
from aluclu.alc_r0.allocation_policy import AllocationAccounting,AllocationRequest,assess_allocation
facts=AllocationAccounting(None,None,'unknown',None,'unknown',None)
result=assess_allocation(AllocationRequest(facts,'D','cpu',0,0,0,0,25*(1<<30),0,0,0,0,0))
assert result.reasons==('history-unreconciled','clock-unreconciled')
assert not blocked.intersection(sys.modules)
print('allocation-isolated')
"""
    child = subprocess.run((sys.executable,"-S","-c",script),cwd=source.parent,
        env=environment,capture_output=True,text=True,timeout=15)
    assert child.returncode == 0,child.stdout+child.stderr
    assert child.stdout.strip() == "allocation-isolated" and child.stderr == ""
