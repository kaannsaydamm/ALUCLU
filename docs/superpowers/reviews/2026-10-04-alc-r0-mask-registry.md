# Checkpoint152: bounded actual mask registry closure

## Reproduced defect and repair

The old inventory executed its independently imported mask registry's getitem.
The real mask producer can resolve another registry from its own globals. Its
preprocessor additionally checks global-map presence before selection. Neither
that alias closure nor altered registry dispatch/maps was recorded completely.

The new helper statically checks exact AttentionMaskInterface class, native
attribute lookup and dictionary descriptor, absence of getattr overrides,
explicit instance schema, pinned getitem function/code and no closure. It
validates exact bounded ASCII dictionaries with Python-function values via
the existing shared mapping validator, then selects the reviewed eager/SDPA
function directly. No registry resolver or mapping descriptor is invoked.
Global route presence is mandatory even if an admitted local override exists.

The state alias and actual create_causal_mask functions from masking, host
wrapper and upstream Llama namespaces are recorded. Each producer's actual
preprocessor binding and both functions' actual registry globals are inspected;
copied functions with different globals therefore cannot hide that alias drift.
Selected functions receive bounded function-state records; unselected entries
are identity-bound. This is cooperating-process inventory, not authentication.

## Independent review at exact bytes

| Artifact | SHA-256 |
| --- | --- |
| src/aluclu/alc_r0/checkpoint_mask_registry.py | 95d5a18eec09554ec72f8163a3769cd2a0b219907bc2e9cda00a5adbeb596815 |
| src/aluclu/alc_r0/checkpoint_state.py | 83d53ad94836b8ebb6d6e669039fde5836ea5f68d0b69814f183c9c461b1ed80 |
| tests/test_alc_r0_mask_registry_dependencies.py | ec525dd73cdaf544b9e6862c53c08caebf0bd6599f74419d0a0b10a6b20c7b52 |

Independent GPT-6.1 Sol code/spec/security: APPROVE; no severity findings.
Independent GPT-6.1 Sol architecture: CLEAR. Both inspected all3 files, shared
mapping validator, integration diff and pinned installed Transformers5.17 mask
source. Actual preprocessing checks global presence at masking_utils.py:820–821;
producer selects through getitem at942. Neither lane ran tests or model code.

## Personally executed and parsed receipts

Windows locked CPython3.12.13 research environment; PYTHONPATH=src,
PYTHONDONTWRITEBYTECODE=1; python -B -m pytest -q -p no:cacheprovider --tb=short.
Actual pytest exits were printed from LASTEXITCODE, not inferred from shell exit.

| XML under results/ | Actual pytest exit | Tests/failures/errors/skips | Seconds | SHA-256 |
| --- | --- | --- | --- | --- |
| alc_r0_mask_registry_red_v1_20261004.xml | 1 | 33/32/0/0 | 52.441 | e2050c23566490934e10b2dc41ae5560fd97682509a8224ca16decb654ee25f6 |
| alc_r0_mask_registry_green_v2_20261004.xml | 0 | 206/0/0/0 | 34.277 | 6da530b26a0a1c58a2bd57a5a09a7304c2ceb960c63ba04fdac2bc99f88f6579 |
| alc_r0_mask_registry_regression_v3_20261004.xml | 0 | 1119/0/0/0 | 67.189 | d4d9876ac18c08d84fd0662a1350b86df9c867b164328358d73ce0e40f3354c4 |

RED reproduced missed alias/dispatch/map drift, foreign resolver invocation and
missing schema checks. Its boundary controls use nonempty metadata and require
mask/fingerprint errors, so unrelated unconsumed-ticket teardown cannot count
as a successful denial. Cleanup-control success is included, not hidden.

Focused GREEN ran33 new tests plus existing mask/subdependency/q-registry
controls. Then8 additional copied-producer/preprocessor, lookup-no-side-effect
and stable-admitted-alias cases were added. Final regression adds all41 cases
to checkpoint151's1078-case selection: the existing36 component targets plus
this new file, retaining the same two GPU/real-tokenizer deselections.
Root consumed terminal56391 and personally parsed1119 total/41 new cases,
verified hashes unchanged and Ruff/diff checks clean. Not a whole-repo suite.

## Residual limits and gate boundary

Import-time identities/code references do not authenticate installed source.
Other globals/builtins, tensor/vmap/native behavior and complete class/controller
semantics remain separate. No host weights, tokenizer/corpus, GPU or optimizer
training run occurred. Actual D parity, E resource stress and scientific R0/
durable neural learning/portability/ALC gates remain OPEN. Full goal ACTIVE.
