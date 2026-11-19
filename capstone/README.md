---
title: Scam SMS Detector
emoji: 📱
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
pinned: false
---

# 📱 Scam SMS detector

NLP capstone project – *[team name]* – [Name 1], [Name 2], [Name 3]

**Live demo:** [Hugging Face Space link]  ·  **Run locally:** see [How to run](#how-to-run)

## The problem

Fake SMS about a parcel, an unpaid fine, a blocked bank account or a new carte Vitale are among the most common scams in France. One click on the link can cost a victim their bank details.

**Who it is for:** anyone who receives an SMS and wonders "is this real?", especially people less used to spotting scams (older relatives, newcomers to France). They paste the message and get a verdict, the warning signs and the words that drove the decision.

**Research question:** a classifier trained on the classic SMS spam dataset scores ~96% F1. *Does it still detect the scams people receive today, in French and English?*

## Data

| Dataset | Use | Content | Size |
|---|---|---|---|
| [UCI SMS Spam Collection](https://huggingface.co/datasets/ucirvine/sms_spam) (Almeida et al., 2011) | train + test | English SMS, ham vs spam, 2010–2012 | 5,572 → 5,158 after cleaning |
| [88milSMS](http://88milsms.huma-num.fr) – CIRAD 1000 extract (Panckhurst et al., 2014) | real-world test | real French personal SMS, Montpellier, 2011 | 50 ham |
| NUS SMS Corpus (Chen & Kan, 2015 release) | real-world test | real English personal SMS, Singapore | 50 ham |
| [Fishing for Smishing](https://discovery.ucl.ac.uk/id/eprint/10214522) (Agarwal et al., IMC 2025) | real-world test | scam SMS reported by users on public forums | 50 FR + 50 EN scams |
| Public victim reports, collected by the team | real-world test | French scams from signal-arnaques.com, forum-assures.ameli.fr and the press, with source link and date | 39 FR scams |

**What the exploration found** ([notebook 01](notebooks/01_exploration.ipynb)):
- **Imbalanced:** 13% spam. A model that always says "ham" gets 87% accuracy, so we report precision, recall and F1 on the spam class.
- **414 duplicates (7.4%)**, removed before the train/test split so no test message is seen in training.
- **An encoding leak:** 309 ham messages contain HTML codes (`&lt;#&gt;`) that never appear in spam. They are decoded so the model cannot use them as a shortcut.
- **Biases:** the UCI data is old, English-only and mostly UK premium-rate spam ("text WIN to 80086"). Its ham comes largely from Singaporean students. Only 18% of its spam contains a link, while almost every modern scam does.

## Pipeline

1. **Cleaning** (notebook 01): HTML decoding, removal of the anonymisation placeholder, deduplication.
2. **Normalisation** (`src/preprocess.py`): every link becomes `URL` and every number becomes `NUM`, in every dataset. Without it, the model would learn each dataset's *format* (`[url]` placeholders appear only in the scams of the 2025 dataset) instead of the message.
3. **Split:** stratified 80/20 split of UCI, fixed seed, saved to `data/train.csv` / `data/test.csv`.
4. **Models**, all with logistic regression (`class_weight="balanced"`):
   - **A**: TF-IDF on words (1–2 grams)
   - **B**: TF-IDF on character n-grams (2–5), robust to spelling tricks and to other languages
   - **C**: multilingual sentence embeddings (`paraphrase-multilingual-MiniLM-L12-v2`)
5. **Evaluation:** on the UCI test set, with 5-fold cross-validation for stability, and on a separate **real-world test set** of 239 messages that is never used for training.
6. **Error analysis:** missed scams, false alarms, the words the model relies on, and threshold choice.

## Results

| Model | Test set | Precision | Recall | F1 | ROC AUC |
|---|---|---|---|---|---|
| Baseline (always ham) | UCI test | 0.00 | 0.00 | 0.00 | – |
| A – TF-IDF words | UCI test | 0.92 | 0.96 | 0.94 | 1.00 |
| B – TF-IDF characters | UCI test | 0.95 | 0.97 | **0.96** | 1.00 |
| A – TF-IDF words | **Real world** | 0.92 | 0.51 | 0.66 | 0.89 |
| B – TF-IDF characters | **Real world** | 0.96 | 0.48 | **0.64** | 0.95 |
| C – Multilingual embeddings | both | *[to fill after running notebook 03]* | | | |

(Normalised text. Full details in [notebook 02](notebooks/02_models.ipynb) and [notebook 03](notebooks/03_real_world_test.ipynb).)

**Main findings:**
- **The UCI score does not transfer.** F1 falls from 0.96 to 0.64 on recent real messages.
- **French is the weak point.** Model B catches 64% of English scams but only 38% of French ones, and about 25% of French bank and parcel scams.
- **The model ranks scams well but is under-confident** (AUC 0.95). Lowering the threshold from 0.5 to 0.3 catches 90% of scams for 14% false alarms, instead of 47% for 3%. The app uses three levels: safe (< 30%), suspicious (30–50%), scam (≥ 50%).
- **Bias inherited from the training data:** numbers push towards "spam" (78% of UCI spam contains a phone number), so French messages with times or dates get flagged.
- **Label noise:** some UCI "ham" messages are clearly spam (and vice versa). The model is sometimes right when the label is wrong.

## Limits

- The real-world test is small (239 messages): one message moves a percentage by 1–2 points.
- **Source = label** in the real-world test: all normal messages are 2011–2015 personal SMS and all scams are 2021–2026 reports. A model could partly separate them by era and style.
- No genuine automatic notifications (real Colissimo, bank codes, Ameli) among the normal messages. These are the hardest cases, so our false-alarm rate is probably optimistic.
- 5 messages in the 2025 dataset look like genuine notifications. They are flagged in `doubtful_label`, and removing them barely changes the results.
- **Next step:** to be useful in France, the model must be *trained* on recent French scams and genuine French notifications, not only tested on them.

## How to run

```bash
pip install -r requirements.txt
python app.py              # http://127.0.0.1:7860
python app.py --share      # temporary public link (while the laptop runs)
```

Notebooks: `pip install -r requirements-dev.txt`, then `jupyter notebook` and open `notebooks/` in order (01 → 02 → 03). Model C (embeddings) needs internet the first time, to download ~470 MB from Hugging Face.

To rebuild the real-world test set: `python scripts/build_real_scams.py data/real_world_scams.csv` then `python scripts/prepare_real_world_test.py`.

## Repository structure

```
app.py                      Gradio app (model B, three-level verdict, explanations)
src/preprocess.py           text normalisation shared by notebooks and app
notebooks/
  01_exploration.ipynb      data quality, duplicates, leak, biases
  02_models.ipynb           models A / B / C on UCI, cross-validation, error analysis
  03_real_world_test.ipynb  test on 239 real recent messages, thresholds, limits
data/
  raw/sms.tsv               UCI SMS Spam Collection (original)
  sms_clean.csv             cleaned UCI (5,158 messages)
  train.csv, test.csv       fixed 80/20 split
  external_test_raw.csv     200 messages from 88milSMS, NUS and Fishing for Smishing
  real_world_scams.csv      39 French scams from public reports, with sources
  real_world_test.csv       final real-world test set (239 messages)
models/                     trained models (.joblib) and result tables
scripts/                    scripts that build the real-world test set
```

## Who did what

| Member | Main responsibility |
|---|---|
| [Name 1] | Data: collection, exploration, cleaning (notebook 01, real-world test set) |
| [Name 2] | Models and evaluation (notebooks 02 and 03, error analysis) |
| [Name 3] | Application, README, deployment, slides |

AI assistants were used for parts of the code. Every member can explain and modify every part of the project.
