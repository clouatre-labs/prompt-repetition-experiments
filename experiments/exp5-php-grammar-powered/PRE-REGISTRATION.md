# Exp5 Pre-registration

Pre-registration record for Exp5 (PHP grammar scout task with a model factor). The protocol is `protocol.md`; `AMENDMENTS.md` records the one amendment made before deposit (#131, 2026-11-27) and is appended to after deposit.

## Deposit contents

The deposit is the `experiments/exp5-php-grammar-powered/` package, exactly as `protocol.md` `## Deposit` lists it: `protocol.md`, `PRE-REGISTRATION.md`, `AMENDMENTS.md`, `plans/main.csv`, `gen_recipes.py`, `run.py`, `runner-prompt.md`, `scorer/`, `analysis/`, `tests/` and `.zenodo.json`. After the main run, `outputs/` is added. Nothing else is deposited: `README.md`, the pilot and smoke plans and the generated `recipes/` stay in the repository only. Metadata is `.zenodo.json`, with `publication_date` fixed at 2026-11-27 before deposit so that its sha256 below is the deposited file's.

`label-map.json` is produced by `run.py` at seal time and is never hand-written: it does not exist at deposit, so its sha256 is written here by the owner at seal time, and the deposit timestamp is earlier than its earliest `sealed_at`.

`AMENDMENTS.md` holds one dated entry at deposit: the #131 change (mechanical contamination exclusion, output overlap descriptive, `outputs/` deposited). Any later change to the protocol is appended there with a date.

## Files to deposit

sha256 computed by `shasum -a 256 <file>` run from the experiment directory (`experiments/exp5-php-grammar-powered/`).

| File | sha256 |
|------|--------|
| `protocol.md` | `0c77ca6c9bde13337653773e600b547008d20c3ccfd98a051d5e117a16c01ea3` |
| `label-map.json` (as sealed) | written at seal time by `run.py`; recorded here by the owner before the first spawn, together with its `sealed_at` |
| `plans/main.csv` | `cdfb4e506cf377a07f6a1e2ffc47b4e3ba2af584b5efef9b9fca665a2a85786a` |
| `runner-prompt.md` | `aacb053091f6157478d126ad8429e040c295e89d3aec09a3dead330833c33ec6` |
| `scorer/HEADROOM-pilot.md` | `20db6f4cca249de6b53821d37b6dd50a356c4aedc2c4ec2b85f27285542c179d` |
| `gen_recipes.py` | `db6f404690058e892fb0bcd50322168f01f3efcba73461278375c5072c803692` |
| `run.py` | `044f10830096ecd9adab881dd457acc13f251975b911c9cca6496b692be6e271` |
| `AMENDMENTS.md` | `58d72202573737697baaf5033447c6774cae5828f484efc54c0cf1b738e5df80` |
| `.zenodo.json` | `695cbbee6ed809fe3e44ba4809130ecac5328cc0083c4aededf0863fb416991c` |

`sha256_scorer` and `sha256_analysis` in `label-map.json` are the `tree_sha256` of `scorer/` and `analysis/` at seal time (`.py`, `.md`, `.json`, `.toml`, `.lock` and `.csv` files, `tests/` excluded); they are recorded by `run.py`, not here.

## Directory contents

Per-file sha256 of every tracked file under `scorer/`, `analysis/` and `tests/` (`shasum -a 256`, run from the experiment directory).

```text
ce632ce44d9a118a8809f3f2330ca6be6600142ae75df4a27f006e6618c58579  analysis/README.md
66a4beed8837808b7e5bf608842dbb6da7da7f7751aadf06870261a0977bc445  analysis/analysis.py
75920c982581609ebf349806ad274b9cccf1682b5df01797bc8d1607085bb335  analysis/contamination.py
19a278b5b7fc25ee1153d02de1cd58c019cdbbb32e0aae4f2795a05c143d372b  analysis/overlap.py
0156281e8571f7ad95f05fb498f1c1722aa1a55e80dd5e16cc2e0eb96683865b  analysis/pricing.json
db67d472e36faca69231765773d981007171ef0faaad51aec13b139617f9f12c  analysis/pyproject.toml
08d73fba58e666afd581ceb398bc43141619fbc9ebe919157de90895ccee7e7b  analysis/stats.py
c1fb385b9ffdf68b96284d0a5dac89331ab49c749a1d383385f0f5107dad2b0f  analysis/tests/fixtures/label-map-flat.json
28c68de2b9ceeddedb1182a386b6cfe413d333d2b0ad5cbd67a6e2d25039aaf0  analysis/tests/fixtures/label-map.json
1e81a3528f1e74cd1c450816fc5cd3c3c98a60cbb66e15d92d7e68ea289ba74f  analysis/tests/fixtures/latency-log.jsonl
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-c1/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-c2/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-c3/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-c4/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-c5/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-t1/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-t2/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-t3/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-t4/exp5-output.json
83b90787b2cc4dced9fb038090a707b3736d5196a6521d2f3fa7f9bcd45c2ffc  analysis/tests/fixtures/outputs/run-t5/exp5-output.json
aea26447b22c5b5c1bc661e79c0fd144d4f18edae45a186457d162db60f74fb8  analysis/tests/fixtures/scores.json
ef84bc6c2c778285c7d0b1a5cc987c87f7d3ec1f5534e40356c663403bc1b6d3  analysis/tests/fixtures/transcripts/h45-control.json
d5f1962ad7a276284eed52f6c1951b3b7b9e313184b85fab3496ffc9043cabe5  analysis/tests/fixtures/transcripts/h45-treatment.json
ea049354e3e55789b166ee6cec0a46ee583da73ec638e5dfdb325813bd1d3494  analysis/tests/fixtures/transcripts/h55-control.json
873bfacc55e08c89b1be401c9de8c8891fdd399d7f0c6c62609e7da966e343f1  analysis/tests/fixtures/transcripts/h55-treatment.json
650cf993eafa2ea28648492bd83cd8088d99dc579e702e9f7e5cdd5fdb36025c  analysis/tests/test_analysis.py
7e54605f3beb03588eed4803bc11d9809ff15d4bfcdd1baa1b462c4f7415ca21  analysis/tests/test_contamination.py
f97cdd688e7e1d23faf8f45c135e433660aa771bc8b9f028ea9dd8af5da36ad5  analysis/tests/test_stats.py
dc00407611e167f50c5e194de405af42519bc10bc7c5c758fe1332821a57d3af  analysis/uv.lock
20db6f4cca249de6b53821d37b6dd50a356c4aedc2c4ec2b85f27285542c179d  scorer/HEADROOM-pilot.md
5f09de7455275319e2552e042b6acba07e4c99bb6fc42ea6eab1042d7da5be87  scorer/README.md
62c4f0e8134f3dddaa3dae708ea497f26e58adcc3e000801ebbd7e632ea7ab7a  scorer/checks.py
b020ad5e195e0cb3fa8831fec181dcefe0b7b5f2c2f63ddb2e3b2387027d8aae  scorer/fixtures/php/classes.php
40c41febb2f52a082771dd3a828d94680f026951f3360e3a2d53b73916d3d187  scorer/fixtures/php/defuse.php
62735d15a818206248e69a4360fd799a4ba46828b657903217e4b421cb9040aa  scorer/fixtures/php/enums.php
fe649bcb017c0c74e535d51ae0c85c8c6f787192e2d2def776fe5482296400ea  scorer/fixtures/php/functions.php
ff4155864a5da2f8ca6411dfb445798e1ff87acaeb9e059fb907c0f71a94afa0  scorer/fixtures/php/interfaces.php
740448fec1746ca671ba7e8edd7ae64f3e457d1055fb4323aa047083d04087a5  scorer/fixtures/php/traits.php
63aa506cb175ac3860e81901e5e5539f301e381bd027614740b32729be007522  scorer/fixtures/sessions/known-bad.json
34d6d19e75b334a32b9181dc7a27a1118e2717a0544fe1ac6ec644298af03163  scorer/fixtures/sessions/known-good.json
8d91cdc0c56c0ae39234e449ae130f0eb9d8158b78f709981a4482ab2a68d612  scorer/pilot-evidence/fenced-repilot/SHA256SUMS
9dc4a805af1069ce9a30b2d15ba62fc9846de9ca0cd70ad7f3cfd869e0ec04cb  scorer/pilot-evidence/fenced-repilot/contamination-narrow.txt
92492de31772e7f5cfda374f8849f459e648ed60b32225be022dd1be5b2c71e8  scorer/pilot-evidence/fenced-repilot/fence.txt
4d7084738d23f5719cdf81f7ff17a54f05e48cc5cc2ab944634e293b2679e66d  scorer/pilot-evidence/fenced-repilot/h45-control/exp5-output.json
6e51c2ccb9531007f83957b29d2a76cb67d46e9a3a1a220e58b07bd4b6bd155f  scorer/pilot-evidence/fenced-repilot/h45-treatment/exp5-output.json
70c004d7ead6504cc45158e748d233795d98cbad7027cedff69d5dd2d50c263f  scorer/pilot-evidence/fenced-repilot/h55-control/exp5-output.json
8afc2569546ff20678fbbed0bfc10d33880a4095efc13aac3190d9a2217fca0f  scorer/pilot-evidence/fenced-repilot/h55-treatment/exp5-output.json
970dd168d2e94095aea457d46496c95752e889db38639ac11378b39ccbf937bb  scorer/pilot-evidence/fenced-repilot/label-map.json
6673f549066df66915aa49d4730cada95974db6056dfdf01f7e1c92eee7be24c  scorer/pilot-evidence/fenced-repilot/latency-log.jsonl
7d3152baf73c14d14e7e62b582f275006048395df8fded32b3079fc1bbd62b1f  scorer/pilot-evidence/fenced-repilot/scores.json
d08b70953a16f9d54fd2dd64155685b6c93a2c016ba19a07932593453cbb3459  scorer/pilot-evidence/fenced-repilot/tool-log.jsonl
d3008942a2f09284e06335e0721650e2987994b49c0ce0b2c791931d834b43bd  scorer/pilot-evidence/fenced-repilot/variance.txt
9ea6b32aec468665aef3361a5cf192fce37f56aac5e2bbde42f9a817f111eb76  scorer/pilot-evidence/h45-recheck/SHA256SUMS
1b2a07122ac056c5fc1cf4aed3995e2127206fa2a9301f1e670999f710a09ef8  scorer/pilot-evidence/h45-recheck/contamination-narrow.txt
639e2885e409ae2c07fe8d068e0d1c9e2f958afb1274f228568661f58363d3e4  scorer/pilot-evidence/h45-recheck/h45-control-r2/exp5-output.json
08b15ccd9509ba10483479fb50438e229e04ebdafd8d75f7465aaaf0516baf8a  scorer/pilot-evidence/h45-recheck/h45-control-r3/exp5-output.json
63fe2ea90ad30ad5dccc6b6ef3ddae04efd14313c882362aae7d125bd112dc64  scorer/pilot-evidence/h45-recheck/label-map.json
d65e84040bd4b87ab9e275e85d0a63bac59a74da3759c251f08dac00b0a271c5  scorer/pilot-evidence/h45-recheck/latency-log.jsonl
7cff745b6481302a565bb88360e94ecea2fbdd45daacbb899795085c16e85f0f  scorer/pilot-evidence/h45-recheck/recheck-scores.json
6a5843fd84221a4d619a33c3503b930db039aec6f5eec550e03fb11e70745758  scorer/pilot-evidence/h45-recheck/tool-log.jsonl
907e0c6a376419088b26fc0444924517b3620874aadacc52a94aab2b85eed237  scorer/pyproject.toml
7063a4f9467bbae3fc09abe979499a0840be13868e3a9c19e45cac10b68bd459  scorer/scorer.py
71fc05461e0a617e23933b4e23d19157d3a7d02e4b558167b9d4ee5d4cdfaf56  scorer/tests/test_scorer.py
77cbbc99c1e8e015d3d3499c2560f46cd7a1dff1253f0328bd595d38006dd16f  scorer/uv.lock
5b35ef8c046ad2e124c15791f91cad46b56e3b78190c53ac6411d82495a6a2e2  scorer/vendor/aptu-coder/PIN.json
3fdd27899a04841e745ab2a156e428831541c251baaed98a3ada5cd00e0dcd00  scorer/vendor/aptu-coder/core.Cargo.toml
2b227c206f86cf8610e426c1459769b30553d62cefeaf83dd6e0b8ebaba6998f  scorer/vendor/aptu-coder/java.rs
6384835cae311518566f556d8ba2c48fa882d63a342279312e0da432838a86ee  scorer/vendor/aptu-coder/lang.rs
603002260503a3e171f51cbc0bc4a6195fa1291be8f3127f4c8727fc10df0960  scorer/vendor/aptu-coder/mod.rs
58bd0bc1805e7bd5b8677039e68d35f795ecffd52d7c8cede0662ec231f578ff  scorer/vendor/aptu-coder/workspace.Cargo.toml
eb073869d28245cc9e6ec17551b0895fc8e3a80d80762d6ecfd3af8076326f8d  scorer/vendor/tree-sitter-php-node-types.json
7e3fd9e47d6f3f0f0f27ff6fa016823d8be1298690381bd5c9eb96964d0dea0e  tests/test_gen_recipes.py
e72dcea0f5baf23a7ff4ac369e1d7ffcb5d4cf1459ee9cc150f573aed9f885af  tests/test_prereg.py
96801ae289fc0d50404912d9dd70d1e9268c0164d1ce0299f90e86041de0b085  tests/test_run.py
```text

## DOI

The pre-registration is published as version 1.1.0 of the dataset record, before the first main-run spawn:

- Concept DOI (all versions): `10.5281/zenodo.19696593`, https://zenodo.org/records/19696593.
- Version 1.1.0, the pre-registration to cite: `10.5281/zenodo.24611615`, https://zenodo.org/records/24611615, published `2026-11-27T22:54:59Z`.
- Content: one file, `prompt-repetition-experiments-v1.1.0.zip` (1,839,288 bytes, md5 `912c2928e5e00f061cab265de26881bc`, sha256 `2876818f3a602a3d3771774cfd4aa43f86965bdfb8d2b383e08fa16db0a0f2e2`), the source archive of GitHub release `v1.1.0` (tag on commit `8223be6`). It holds the complete package listed above with every sha256 unchanged, Experiment 4, and the Experiment 1 to 3 data of version 1.0.9. It holds no main-run output.
- The main-run data (`outputs/`, scores, analysis output) will be published as the next version of the same record after the run.
