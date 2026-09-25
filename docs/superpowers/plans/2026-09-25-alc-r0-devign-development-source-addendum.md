# ALC-R0 Devign development-source acquisition addendum

Status: verified train/validation **source**, development-only and
non-authorizing. This does not implement Devign clone filtering or inspect the
official test split. The byte-frozen ALC-R0 plan remains unchanged.

The [pinned dataset repository](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/tree/69bd48c03223c2104342acd9a807caf61ac3efb8)
declares C-UDA licensing. Only these exact Parquet files from commit
`69bd48c03223c2104342acd9a807caf61ac3efb8` were acquired into the
plan's non-OneDrive local research directory:

| Split | Bytes | SHA-256 | Source rows |
|---|---:|---|---:|
| train | 17,847,670 | `e319c83e2e816a10aeeebe78668aa95b757b04e555700bf5f826766b0e80bb06` | 21,854 |
| validation | 2,214,315 | `a17a76ed040d7f8657d1ff741f967b44704c008101ac958e2990ad468203cfa4` | 2,732 |

The source directory's `data/` contains exactly train and validation; a test
file or any extra entry fails closed. `devign_source.py` independently checks
file lengths and SHA-256 before parsing, exact Arrow schema and row counts,
nonnull fields, supported upstream project names, 40-hex commit IDs, and
unique official source IDs within and across splits. IDs become
`devign:<zero-padded eight-digit official id>`. That ID convention is fixed
here before development model training or confirmatory access, but it is not
yet a clone-group root or a statistical unit.

The canonical LF candidate receipt is
`results/alc_r0_devign_development_candidate_20260925.json`, SHA-256
`09926c5742825b274efb9e00fb536c2950811c8c01615cf5ef8ad1826c1e7d73`.
It contains exact file hashes, source-ID roots, target-class counts, and
`training_authority=false`; it contains no function text or test metadata.
The pinned-source test regenerates the receipt byte-for-byte and a subprocess
CLI test checks the same output. No dataset bytes are committed.

The next Devign prerequisite is the plan's deterministic code normalization,
five-token shingles, 256-permutation MinHash/LSH candidate generation,
Jaccard confirmation, transitive union-find grouping, conflicting-label
rejection, and train/validation root filtering. The official test split and
its exclusion identities must stay in the independent sealer. The current
source receipt does not authorize training or R0.0 PASS.
