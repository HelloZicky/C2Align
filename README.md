# 🩺 C²Align: Calibrating Agentic LLMs for Clinical Prediction (NeurIPS 2026)


[![OpenReview](https://img.shields.io/badge/OpenReview-NeurIPS%202026-red)](https://openreview.net/forum?id=sTj2ZkCskP)
[![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b?logo=arxiv)](#)
[![Code](https://img.shields.io/badge/Code-Available-green?logo=github)](https://github.com/HelloZicky/C2Align_repo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)



This is the official repository for **Calibrating Agentic LLMs for Clinical Prediction**, accepted to **NeurIPS 2026**.

**C²Align** (Calibrated and Clinically Aligned framework) improves the calibration of agentic LLMs in clinical prediction while maintaining or improving discrimination. It aligns two frozen agent branches, an ensemble of task-homogeneous parallel agents and a set of clinical task-inspired specialist agents, through a lightweight downstream model trained with a discrimination- and calibration-aware loss.

<p align="center">
  <img src="assets/c2align_overview.png" alt="C2Align Overview" width="800">
</p>


## ✨ Highlights

- **Calibration without sacrificing discrimination**: C²Align lowers Brier score and ECE while maintaining or improving AUROC, AUPRC, and P@S95.
- **Dual-branch agents**: homogeneous parallel agents reduce generative variance; clinical specialist agents inject task knowledge as fixed JSON indicators.
- **Mixture of Calibrated Alignment (MoCAL) loss**: cross-entropy + Brier score + dual KL alignment to both agent branches, implemented as a custom XGBoost objective.
- **Frozen LLMs, lightweight training**: only the downstream XGBoost model is trained; any LLM can be plugged in through an inference callback.
- **Fail-closed feature policy**: a task-level allowlist builds the model matrix and rejects labels, annotations, outcomes, post-index fields, and identifiers.
- **Theory-motivated design**: conditional analyses of how agent architecture, task knowledge, and tool use affect calibration.

## 🔔 News

- **[Sept 2026]** C²Align was accepted to [NeurIPS 2026](https://openreview.net/forum?id=sTj2ZkCskP) (poster).
- **[Coming Soon]** arXiv preprint.

## 📖 Citation

If you find C²Align useful, please consider citing:

```bibtex
@inproceedings{lv2026calibrating,
  author    = {Zheqi Lv and Fuying Ding and Meihan Wei and Haoyang Li and Christos Faloutsos and Fei Wang and Chengxi Zang},
  title     = {Calibrating Agentic {LLMs} for Clinical Prediction},
  booktitle = {Advances in Neural Information Processing Systems},
  year      = {2026}
}
```

## 🖼️ Figures

The following paper figures are included as PDF files under [`assets/`](assets/).

| Figure | Description | Link |
|---|---|---|
| Figure 1 | The clinical calibration gap, the C²Align framework, and the performance comparison | [PDF](assets/introduction.pdf) |
| Figure 2 | ROC curve, precision-recall curve, and reliability diagram on the HF benchmark (Qwen3-Max) | [PDF](assets/exp_fig1.pdf) |

## 🧩 Supported Tasks

| Task | Dataset | C²Align entry point | Cohort construction |
|---|---|---|---|
| Heart failure (HF) diagnosis and phenotyping | MIMIC-IV | `C2Align/HF/c2align_hf.ipynb` | `Cohort_construction/build_hf_cohort.ipynb` |
| Alzheimer's disease and related dementias (ADRD) diagnosis and phenotyping | MIMIC-IV | `C2Align/ADRD/c2align_adrd.ipynb` | `Cohort_construction/build_adrd_cohort.ipynb` |
| 30-day unplanned readmission, Readmission (IV) | MIMIC-IV | `C2Align/Readmission/c2align_readmission_mimic4.ipynb` | Prepared from MIMIC-IV (see Quick Start) |
| 30-day unplanned readmission, Readmission (III) | MIMIC-III | `C2Align/Readmission/c2align_readmission_mimic3.ipynb` | Prepared from MIMIC-III (see Quick Start) |

The notebooks are LLM-agnostic. The paper reports results with Qwen3-Max, ChatGPT-4o, Gemini-2.5, DeepSeek-V4, and LLaMA-3.1-8B.

## ⚙️ Installation

```bash
git clone https://github.com/HelloZicky/C2Align_repo.git
cd C2Align_repo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10 or later is recommended.

## 🔐 Data Access

This repository does not contain patient records, identifiers, clinical notes, credentials, completed physician annotation forms, or generated branch outputs.

- MIMIC-III and MIMIC-IV are available through [PhysioNet](https://physionet.org/) to credentialed researchers under the PhysioNet Credentialed Health Data Use Agreement.
- Send clinical text only to LLM endpoints that are permitted under that agreement; see PhysioNet's guidance on the responsible use of credentialed data with online services.
- Keep all protected data and every generated table outside the repository.

## 🚀 Quick Start

Each task notebook defines its prompts, branch workflow, feature allowlist, and training code. Run the definition cells from top to bottom, then follow the steps below.

```text
C2Align_repo/
├── Cohort_construction/
│   ├── build_hf_cohort.ipynb       # Step 1 for HF
│   └── build_adrd_cohort.ipynb     # Step 1 for ADRD
└── C2Align/
    ├── HF/c2align_hf.ipynb                                # Steps 2-3 for HF
    ├── ADRD/c2align_adrd.ipynb                            # Steps 2-3 for ADRD
    └── Readmission/
        ├── c2align_readmission_mimic4.ipynb               # Steps 2-3 for Readmission (IV)
        └── c2align_readmission_mimic3.ipynb               # Steps 2-3 for Readmission (III)
```

### Step 1: Build the cohort

For HF and ADRD, open the cohort-construction notebook and set:

| Variable | Meaning |
|---|---|
| `DATA_ROOT` | Local MIMIC-IV directory (reads `hosp/diagnoses_icd.csv`, `hosp/admissions.csv`, `hosp/patients.csv`) |
| `CODE_DICTIONARY` | Excel file whose `dx code` column lists the target ICD codes |
| `ANNOTATION_INPUT` | Completed physician annotation sheet |
| `OUTPUT_DIR` | Output directory outside the repository |

Then run:

1. `prepare_annotation_sheet()` selects 500 code-positive and 500 matched code-negative patients and writes an annotation template.
2. Two physicians label each patient independently, and a senior expert adjudicates disagreements.
3. `finalize_patient_level_cohort()` applies the adjudication rules and writes the patient-level train/test split (HF: 730/243; ADRD: 712/238).

The branch notebooks read each patient's clinical note from a `text` column. Add it to both tables from your authorized MIMIC note data before Step 2.

For Readmission (III) and (IV), prepare one row per patient (800 train / 200 test) with `subject_id`, `label_numerical`, `admit_age`, `los_days`, `gender`, `race`, `admission_type`, `discharge_location`, `all_icd_codes`, and `text`. All inputs must end at discharge from the index hospitalization.

### Step 2: Run the two agent branches

Connect an LLM through `configure_inference_callback`. The callback receives the system prompt and the user prompt and returns a JSON object (or a string containing one) that follows the schema in the prompt.

```python
import pandas as pd

def my_llm(system_prompt, prompt, seed, temperature):
    # Call an LLM endpoint that is approved for your data and return its JSON answer.
    ...

configure_inference_callback(my_llm)

train = pd.read_csv("path/to/hf_train_patient_level.csv")
test = pd.read_csv("path/to/hf_test_patient_level.csv")
for split, rows in (("train", train), ("test", test)):
    generate_branch_outputs(rows, "specialist", f"path/to/outputs/specialist_{split}.csv")
    generate_branch_outputs(rows, "parallel", f"path/to/outputs/parallel_{split}.csv")
```

In the readmission notebooks the call is `generate_branch_outputs(rows, TARGET_TASK, branch, output_path, USE_CHART_REVIEW, NUM_PARALLEL_AGENTS)`.

### Step 3: Train and evaluate C²Align

```python
model, cv_metrics, test_metrics, predictions = run_method5_from_csv(
    "path/to/outputs/specialist_train.csv",
    "path/to/outputs/specialist_test.csv",
    "path/to/outputs/parallel_train.csv",
    "path/to/outputs/parallel_test.csv",
)
print(test_metrics["auc"], test_metrics["brier"])
```

`run_method5_from_csv` aligns the two branches by patient, checks that the train and test patients are disjoint, builds the allowlisted model matrix, runs patient-level five-fold cross-validation on the training set, and evaluates on the test set. In the notebooks, "Method 5 MoE_b (Dual KL Calib)" is C²Align.

### Verification

```bash
python -m unittest discover -s tests -v
```

The tests check the feature allowlist, the notebook integration, clean notebook state, and that no data files or machine-specific paths are committed.

## 📊 Results

Results depend on the cohort construction and the patient-level split, so all methods below are evaluated on the same test patients. LLM-based methods use the Qwen3-Max backbone (Table 1 of the paper). *LLM + post-hoc calibration* reports the best of Platt scaling, isotonic regression, and BBQ; *MAS + trajectory calibration* is agentic confidence calibration. For BS and ECE, the gain is a reduction.

### HF diagnosis and phenotyping (MIMIC-IV; 973 patients, 730 train / 243 test)

| Method | AUROC ↑ | AUPRC ↑ | P@S95 ↑ | BS ↓ | ECE ↓ |
|---|---:|---:|---:|---:|---:|
| LR | 0.9191 | 0.9250 | 0.6920 | 0.1029 | 0.0498 |
| XGBoost | 0.9157 | 0.9240 | 0.6415 | 0.0957 | 0.0528 |
| LLM | 0.9386 | 0.9069 | 0.8967 | 0.0670 | 0.0535 |
| LLM + post-hoc calibration | 0.9386 | 0.9069 | 0.8967 | 0.0689 | 0.0545 |
| MAS-Sequential | 0.8619 | 0.7943 | 0.7977 | 0.1345 | 0.1059 |
| MAS-Parallel | 0.9614 | 0.9449 | 0.9130 | 0.0657 | 0.0547 |
| MAS + trajectory calibration | 0.9806 | 0.9865 | 0.9034 | 0.0459 | 0.0428 |
| **C²Align (ours)** | **0.9927** | **0.9940** | **0.9530** | **0.0336** | **0.0294** |
| *Gain over the strongest baseline* | *+0.0121 (1.23%)* | *+0.0075 (0.76%)* | *+0.0400 (4.38%)* | *+0.0123 (26.80%)* | *+0.0134 (31.31%)* |

### ADRD diagnosis and phenotyping (MIMIC-IV; 950 patients, 712 train / 238 test)

| Method | AUROC ↑ | AUPRC ↑ | P@S95 ↑ | BS ↓ | ECE ↓ |
|---|---:|---:|---:|---:|---:|
| LR | 0.9357 | 0.9589 | 0.6482 | 0.0912 | 0.0464 |
| XGBoost | 0.9372 | 0.9562 | 0.7247 | 0.0901 | 0.0569 |
| LLM | 0.9680 | 0.9707 | 0.8944 | 0.0523 | 0.0868 |
| LLM + post-hoc calibration | 0.9680 | 0.9707 | 0.8944 | 0.0412 | 0.0280 |
| MAS-Sequential | 0.9501 | 0.9523 | 0.8567 | 0.1006 | 0.0821 |
| MAS-Parallel | 0.9727 | 0.9747 | 0.9604 | 0.0505 | 0.0841 |
| MAS + trajectory calibration | 0.9804 | 0.9855 | 0.8837 | 0.0641 | 0.0900 |
| **C²Align (ours)** | **0.9962** | **0.9971** | **1.0000** | **0.0210** | **0.0273** |
| *Gain over the strongest baseline* | *+0.0158 (1.61%)* | *+0.0116 (1.18%)* | *+0.0396 (4.12%)* | *+0.0202 (49.03%)* | *+0.0007 (2.50%)* |

### 30-day readmission, Readmission (IV) (MIMIC-IV; 1,000 patients, 800 train / 200 test)

| Method | AUROC ↑ | AUPRC ↑ | P@S95 ↑ | BS ↓ | ECE ↓ |
|---|---:|---:|---:|---:|---:|
| LR | 0.5540 | 0.5821 | 0.5360 | 0.4016 | 0.3831 |
| XGBoost | 0.6394 | 0.6344 | 0.5505 | 0.2638 | 0.1657 |
| LLM | 0.5788 | 0.6058 | 0.5285 | 0.3533 | 0.3220 |
| LLM + post-hoc calibration | 0.4212 | 0.5317 | 0.5280 | 0.2509 | 0.1400 |
| MAS-Sequential | 0.5842 | 0.6250 | 0.5285 | 0.3691 | 0.3358 |
| MAS-Parallel | 0.5874 | 0.6439 | 0.5285 | 0.3477 | 0.3048 |
| MAS + trajectory calibration | 0.5805 | 0.6023 | 0.5505 | 0.2456 | 0.1304 |
| **C²Align (ours)** | **0.7128** | **0.7098** | **0.6076** | **0.2210** | **0.1214** |
| *Gain over the strongest baseline* | *+0.0734 (11.48%)* | *+0.0659 (10.23%)* | *+0.0571 (10.37%)* | *+0.0246 (10.02%)* | *+0.0090 (6.90%)* |

### 30-day readmission, Readmission (III) (MIMIC-III; 1,000 patients, 800 train / 200 test)

| Method | AUROC ↑ | AUPRC ↑ | P@S95 ↑ | BS ↓ | ECE ↓ |
|---|---:|---:|---:|---:|---:|
| LR | 0.5240 | 0.3126 | 0.2803 | 0.3277 | 0.3100 |
| XGBoost | 0.5864 | 0.3255 | 0.3064 | 0.2467 | 0.1802 |
| LLM | 0.6331 | 0.3675 | 0.3444 | 0.3670 | 0.4012 |
| LLM + post-hoc calibration | 0.6331 | 0.3675 | 0.3444 | 0.1882 | 0.0830 |
| MAS-Sequential | 0.6420 | 0.3809 | 0.3352 | 0.3875 | 0.4228 |
| MAS-Parallel | 0.6414 | 0.3738 | 0.3408 | 0.3833 | 0.4184 |
| MAS + trajectory calibration | 0.4583 | 0.2643 | 0.2775 | 0.2216 | 0.1131 |
| **C²Align (ours)** | **0.6674** | **0.4068** | **0.3598** | **0.1851** | **0.0702** |
| *Gain over the strongest baseline* | *+0.0254 (3.96%)* | *+0.0259 (6.80%)* | *+0.0154 (4.47%)* | *+0.0031 (1.65%)* | *+0.0128 (15.42%)* |

Please refer to the paper for results with other LLM backbones (ChatGPT-4o, Gemini-2.5, DeepSeek-V4, LLaMA-3.1-8B), the ablation study, and the external TJH cohort.

## 🧠 Method Overview

C²Align runs in six steps:

1. **Parallel branch** (frozen): $M$ independent, homogeneous agents each return a probability, and their average gives $p_{\text{par}}$ (`run_parallel_branch`).
2. **Specialist branch** (frozen): symptom, medication/intervention, and risk agents extract fixed task indicators $x_{\text{spe}}$; a diagnosis agent followed by a chart-review agent returns $p_{\text{spe}}$ (`run_specialist_branch`).
3. **Join**: both outputs are joined with structured covariates by patient ID and schema-validated (`align_branch_outputs`).
4. **Allowlist**: a task-level allowlist builds the feature vector $x_{\text{struct}} \oplus x_{\text{spe}} \oplus p_{\text{par}} \oplus p_{\text{spe}}$ (`MODEL_FEATURE_COLUMNS`, `c2align_feature_policy.py`).
5. **Train**: only the downstream XGBoost model is trained, with the MoCAL loss as a custom objective (`get_custom_xgb_obj_bin_dual_kl`):

   $$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{Dis}} + \alpha\,\mathcal{L}_{\text{Cal}} + \beta_{\text{par}}\,D_{\mathrm{KL}}(p_{\text{par}} \,\|\, p_{\text{ML}}) + \beta_{\text{spe}}\,D_{\mathrm{KL}}(p_{\text{spe}} \,\|\, p_{\text{ML}})$$

   where $\mathcal{L}_{\text{Dis}}$ is cross-entropy and $\mathcal{L}_{\text{Cal}}$ is the Brier score.
6. **Evaluate**: the model's probability $p_{\text{ML}}$ is evaluated on the held-out test patients.

## 📁 Repository Structure

```text
C2Align_repo/
├── C2Align/
│   ├── ADRD/                       # ADRD prompts, branches, and C²Align training
│   ├── HF/                         # HF prompts, branches, and C²Align training
│   └── Readmission/                # Readmission (III) and (IV) notebooks
├── Cohort_construction/            # HF and ADRD cohort construction and annotation workflow
├── assets/                         # Paper figure PDFs and the README overview image
├── tests/                          # Feature-policy, notebook-integration, and hygiene tests
├── c2align_feature_policy.py       # Fail-closed feature allowlist
├── requirements.txt
├── LICENSE
└── README.md
```

## 📖 Citation

If you find C²Align useful, please consider citing:

```bibtex
@inproceedings{lv2026calibrating,
  author    = {Zheqi Lv and Fuying Ding and Meihan Wei and Haoyang Li and Christos Faloutsos and Fei Wang and Chengxi Zang},
  title     = {Calibrating Agentic {LLMs} for Clinical Prediction},
  booktitle = {Advances in Neural Information Processing Systems},
  year      = {2026}
}
```

## 🙏 Acknowledgements

We thank the MIT Laboratory for Computational Physiology and PhysioNet for MIMIC-III and MIMIC-IV, the providers of the TJH dataset, and the developers of XGBoost, scikit-learn, and pandas.

## 📄 License

This project is released under the MIT License.

## ⚠️ Responsible Use

C²Align is research code for clinical prediction, not a medical device, and it has not been validated for clinical deployment. Its outputs are meant to support, not replace, clinician judgment. Calibration can shift across hospitals and populations, so re-evaluate calibration on local data before any use. Use protected health data only under the applicable data-use agreements and only with LLM services that those agreements permit.
