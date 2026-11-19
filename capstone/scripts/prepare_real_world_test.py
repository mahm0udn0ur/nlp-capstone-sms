"""Builds data/real_world_test.csv from the two real-world sources collected by the team.

1. data/external_test_raw.csv: 200 SMS sampled from three public corpora
   (88milSMS / CIRAD 1000 extract, NUS SMS Corpus, "Fishing for Smishing" IMC 2025).
2. data/real_world_scams.csv: 39 French scam SMS from public victim reports (signal-arnaques.com, forum-assures.ameli.fr, press).

Corrections applied (nothing is invented, only cleaned or flagged):
- one cell contained two messages stored as a Python list -> keep the first message only;
- labels that look doubtful (genuine-looking bank / shop notifications reported as scams) are FLAGGED in
  `doubtful_label`, not deleted, so results can be shown with and without them;
- the two files get the same columns and category names.
Text normalisation (URL / NUM) is NOT applied here: it is done by src/preprocess.py inside the notebooks and the app.
"""
import ast
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

ext = pd.read_csv(ROOT / "data/external_test_raw.csv")

def first_if_list(t):
    t = str(t).strip()
    if t.startswith("[") and t.endswith("]") and "', '" in t:
        try:
            return ast.literal_eval(t)[0].strip()
        except (ValueError, SyntaxError):
            pass
    return t

ext["text"] = ext["text"].apply(first_if_list)
ext["source"] = ext["source"].replace({"CIRAD 1000 authentic French SMS (collected 2011)": "88milSMS (CIRAD 1000 extract, 2011)"})

# messages labelled scam that read like genuine notifications: kept, but flagged
DOUBTFUL = ("You have initiated a txn of INR", "Placed: Flipkart Order", "Dear SBI Card-holder outstanding",
            "withdrawn at SIB ATM", "Hi Amresh, please renew your Max Life")
ext["doubtful_label"] = ext["text"].apply(lambda t: any(p in t for p in DOUBTFUL))

pub = pd.read_csv(ROOT / "data/real_world_scams.csv")
pub = pub.assign(
    source="Public victim reports (signal-arnaques, forum Ameli, press)",
    category=pub["category"].map({"colis": "delivery", "amende": "government", "ameli": "government",
                                  "cpf": "government", "banque": "banking", "famille": "family"}),
    doubtful_label=False,
)

cols = ["text", "label", "language", "source", "category", "doubtful_label"]
test = pd.concat([ext[cols], pub[cols]], ignore_index=True)
test["category"] = test["category"].fillna("-")
test = test.drop_duplicates("text").reset_index(drop=True)
test.to_csv(ROOT / "data/real_world_test.csv", index=False)

print(test.shape)
print(pd.crosstab([test.label, test.language], test.source.str[:22]))
print("doubtful labels flagged:", int(test.doubtful_label.sum()))
