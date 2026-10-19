# Preregistered single-route inventory integration

Parent ed78e828b6bbea8cb95e944ef44dc539a1ebfcc4; previous goal turn PROGRESS.
Standalone native observer passed42focused/329regression and independent review.
Fullscan actual_v4 still refused; neither small probe proved its cause.

Use the exact tested native DirectoryObservation for every Windows directory,
including root, in BOTH _walk calls. Existing lstat kind/reparse prechecks remain;
native path/status validation and single fixed104byte by-name query follow.
No fallback/tolerance/zero normalization. All14 native fields compare exactly,
including size, full128-bit/volume identity, creation/write/change ticks, attrs,
links, allocation and device metadata. Old coarse mode is derived equivalently;
ctime creation semantics retained, change time additionally retained. Access time
excluded as before. Different observation route/units explicitly represented;
do not pretend Python tuple and native record are interchangeable. Non-Windows
directories keep original path fingerprint; no new portability PASS.

Regular files retain existing8-field path/open metadata, exact size limits,
streamed hash and original continuity predicate. Canonical directory rows still
byte_length0 (not new); membership/count/path/casefold/reparse/regular-file bounds
and original deadline remain. Memory stays bounded by entry count plus fixed14
fields per directory. Native library reference releases finally; all blocking
calls remain inside original outer owned deadline. Cooperating host/non-atomic
FS only; no mapped-image/provenance or worker/training permission inferred.

Diagnostics support exact native14-field dicts as well as old8-field tuples,
membership/kind/schema changes and bounded preview/fullpathhash. They neither
perform new filesystem reads nor change the existing full-tree rejection.
Cross-schema differences are explicit, not comparison of different units.
Exact DirectoryObservation type is the internal native schema tag; diagnostics
emit windows-directory-by-name-v1 versus python-stat-v1 on native involvement.
Unknown fingerprint types/tuple lengths deny. Native directory mode/type and
non-reparse status must agree with preceding classification; no atomic identity
binding is inferred. Add explicit cross-schema negative before implementing.

TDD: RED new root/nested directory native-record integration assertion and14
individual native field-difference diagnostics (all fourteen, including size).
Then implement and run focused native+tree/binding and prior9-file regression.
No mocks/callback/API injection. Pure diagnostic negatives show field detection,
not exhaustive between-walk race reproduction. Real synthetic inventory tests
exercise native routing; file-only parity stays covered. Preserve failed results.
Review contract/source before GREEN; final artifact closure before commit/push.
Only after accepted integration: separately select new actual-only diagnostic,
same900s inner/960s outer and unchanged caps, fresh retained stem, serial execution.
No silent actual scan in regression, scientific budget reset or model/GPU call.
