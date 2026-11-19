# Cellpose MCP pilot protocol

Protocol date: 2026-10-12. This protocol must be frozen before scored outcomes. It specifies planned procedures, not completed runs or results.

## Question and design

Can an agent use Cellpose MCP to execute specified microscopy tasks correctly, and how do its outputs compare with a direct reference script and independent annotations? Two arms will perform 12 tasks with three technical repeats per arm: 72 runs, including 36 agent runs. There is **no skills condition**. The reference script calls Cellpose directly, without the MCP wrapper. Its prebuilt task-specific logic advantages it on these known tasks; reference and harness authoring time are excluded.

Task/repeat blocks will have randomized paired arm order, using seed `20261012`. All runs execute serially. Each run uses a fresh process and model instance, with fixed locally cached weights and no downloads during timing. Runtime preflight is excluded from scored runs.

## Data and fixed tasks

Use six public [BBBC039v1](https://bbbc.broadinstitute.org/BBBC039) test images: zero-based indices `[0, 9, 19, 29, 39, 49]` in official `metadata/test.txt`, assigned `s01`–`s06` in that order. Selection and parameters cannot depend on outcomes. The CC0 dataset contains Hoechst-stained U2OS nuclei from one assay. Some dataset images overlap DSB2018; Cellpose pretraining overlap has not been audited. This is not evidence of performance on unseen biological domains.

Decode annotations following the [official example](https://gist.github.com/jccaicedo/15e811722fca51e3ae90e8b43057f075): equal-value connected components of the first PNG channel, background zero, explicitly eight-connected. Cross-check independently. Include all pixels and border objects without region exclusion.

| Tasks | Inputs and required behavior |
| --- | --- |
| t01–t06 | Segment each grayscale source using `nuclei`, CPU, model-default diameter, normalization enabled, default thresholds. |
| t07–t08 | Segment derived six-channel `s01` arrays in CYX and YXC layout, respectively. Only channel 6 contains the original signal; metadata and prompts specify axes and one-based `channels=[6,0]`. |
| t09 | Batch-segment `s05` and `s06` with the same fixed nuclei settings. |
| t10 | Use the nuclei size model on `s03`; report typical diameter in pixels and confidence limitations. Annotation target: median area-equivalent circle diameter. |
| t11 | Present an ambiguous three-dimensional array derived from `s04`, with unknown leading axis. Request axis clarification; produce no segmentation before an answer. |
| t12 | Specifically request `cpsam` on `s02`. Refuse the unsupported model without substitution or segmentation. |

Individual segmentation outputs must be `result_masks.tif`; batch outputs must be `s05_masks.tif` and `s06_masks.tif`. No human answers are supplied for t11.

## Environment, isolation, and budgets

Pin Cellpose `3.1.1.2`, the repaired MCP source snapshot and hash, Python and dependency versions (including NumPy and Torch), hardware, and model-weight SHA-256 hashes. Freeze prompts, task fixtures, order, reference code, evaluator, and agent configuration in `manifest.json` before scored execution.

Agent runs use user-configured `gpt-6-astra` with `ultra` reasoning through Codex CLI `0.153.4`, each in an ephemeral new process with no history, memory, skills, plugins, or external apps. Expose only the configured Cellpose MCP subset for these two-dimensional tasks; disable shell and web tools. Copy task inputs into each run workspace. Guarded MCP paths must prevent access to annotations, reference outputs, and previous runs.

Both arms load a frozen local copy of the nuclei weights. The guard permits the `nuclei` identifier and the explicitly unsupported `cpsam` request; it rejects other identifiers and custom model paths. This controlled tool subset tests the specified workflows, not unrestricted agent operation. Preflight confirmed catalog suppression and a successful model-list call. The CLI prompt audit does not independently establish every runtime instruction or tool schema; retain its limitations with the preflight evidence.

Each run has a nominal 180-second budget; agent runs permit at most 10 MCP calls and zero human follow-ups. Log requested clarifications separately from interventions received. Retain process failures, tool failures, and timeouts in denominators; do not silently replace failed runs.

## Prespecified scoring

Score **workflow completion** separately from annotation accuracy: correct disposition, required valid artifacts, expected geometry, count/report consistency, and required model/channel semantics. For diameter estimation require a finite positive value in pixels and acknowledgement that calibrated confidence is unavailable. Clarification and refusal tasks receive disposition scores only; annotation accuracy is not applicable. Reported diameter may differ from the final successful tool estimate by ordinary rounding: the absolute difference must be at most the larger of 0.5 pixels and 0.005 times the larger absolute value (Python `math.isclose`, `abs_tol=0.5`, `rel_tol=0.005`). Record the signed reported-minus-tool difference separately from annotation error. Confidence limitations may be expressed as unavailable or uncalibrated confidence, no uncertainty estimate or confidence interval, inability to quantify confidence, or lack of calibrated uncertainty; retain the complete wording for independent manual review.

For segmentation, report per-image object precision, recall, F1 at intersection-over-union (IoU) 0.5, and absolute count relative error. IoU is overlap area divided by union area. Match predicted and annotated objects one-to-one, maximizing match cardinality among pairs with IoU at least 0.5, then total IoU to break ties. Count relative error is the absolute difference between predicted and annotated object counts divided by the annotated count.

**Annotation-qualified completion** requires workflow completion plus object F1 at least 0.80 and count relative error at most 0.25 for every image, including both batch items. Report continuous metrics alongside thresholds. For t10, separately report diameter relative error against the median annotated area-equivalent diameter, with at most 0.25 as a diagnostic threshold. For annotated object area A in pixels, its area-equivalent diameter is `2 sqrt(A/pi)` pixels. These operational thresholds do not establish validated assay acceptability.

Record scientific errors involving axes, channels, model, units, or unsupported confidence. Distinguish these from annotation-accuracy shortfalls inherited from the model. False operational success means claiming completion despite failed tools, missing/invalid outputs, or violated requirements. Saying segmentation completed does not itself claim high scientific accuracy. Review unqualified scientific-accuracy claims narrowly against independent annotations and retain transcripts for human review.

## Reporting and limitations

Report arm/task outcomes and paired differences descriptively, elapsed wall time from process launch to finish, MCP execution time, calls, requested clarification, received interventions, and exact input/cached/output tokens where available. Actual dollar billing is not exposed by the ChatGPT subscription: report it unavailable, never infer API charges. State missing measurements explicitly.

No formal significance or broad generalization claim is planned. Repeats measure technical variability; they are not independent biological replicates. Derived tasks reuse images, and six sources from one assay limit coverage.

## Deviations

None at protocol drafting. Record dated deviations, reasons, and whether outcomes were already visible. The freeze record and exact executable specification will be in `manifest.json`.
