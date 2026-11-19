"""Scam SMS detector – Gradio app.

    python app.py            # local, opens http://127.0.0.1:7860
    python app.py --share    # public link for the demo

Model: TF-IDF on character n-grams + logistic regression (model B), trained on the UCI SMS Spam Collection
with links and numbers normalised (notebook 03). If the saved model is missing, it is retrained from data/train.csv.
"""
import argparse
import re
from pathlib import Path

import gradio as gr
import joblib
import pandas as pd

from src.preprocess import normalize

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models/model_b_tfidf_chars_norm.joblib"
MAX_CHARS = 1000

# Thresholds chosen in notebook 03: at 0.3 the model catches ~90% of real scams for ~14% false alarms.
SUSPICIOUS, SCAM = 0.30, 0.50

FRENCH_WORDS = {"le", "la", "les", "de", "des", "du", "et", "est", "vous", "votre", "vos", "je", "tu", "pas",
                "une", "un", "pour", "sur", "avec", "ce", "ça", "que", "qui", "mon", "ma", "colis", "merci"}

RED_FLAGS = {
    "Contains a link": r"\bURL\b",
    "Urgency or threat": r"\b(urgent|immédiatement|immediately|dernier rappel|final|expire|expiration|suspendu|suspended|bloqué|blocked|majoration|sous \d+ ?h|within|avant le)\b",
    "Asks for payment or money": r"(€|£|\$|\beuros?\b|\bfrais\b|\bfee\b|\bpaiement\b|\bpayment\b|\bpay\b|\bamende\b|\bfine\b|\bremboursement\b|\brefund\b)",
    "Asks to update or confirm details": r"\b(mettre à jour|mise à jour|update|confirm|confirmer|vérifier|verify|formulaire|form)\b",
    "Impersonates a known organisation": r"\b(ameli|carte vitale|antai|chronopost|colissimo|la poste|dhl|ups|usps|royal mail|paypal|cpf|impots|banque|bank|amazon|netflix)\b",
}


def load_model():
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    # fallback: retrain (same settings as notebook 03)
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    train = pd.read_csv(ROOT / "data/train.csv")
    model = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True),
                          LogisticRegression(max_iter=1000, class_weight="balanced"))
    model.fit(train["text"].apply(normalize), (train["label"] == "spam").astype(int))
    return model


MODEL = load_model()


def p_spam(texts):
    return MODEL.predict_proba(texts)[:, 1]


def influential_words(norm_text, base, k=6):
    """Remove each word in turn and measure how much the scam probability changes (occlusion)."""
    words = norm_text.split()
    if len(words) < 2:
        return []
    variants = [" ".join(words[:i] + words[i + 1:]) for i in range(len(words))]
    deltas = base - p_spam(variants)           # > 0: the word pushed towards "scam"
    ranked = sorted(zip(words, deltas), key=lambda x: -abs(x[1]))
    seen, out = set(), []
    for w, d in ranked:
        if w.lower() not in seen and abs(d) >= 0.005:
            seen.add(w.lower())
            out.append((w, d))
        if len(out) == k:
            break
    return out


def analyse(text):
    text = (text or "").strip()
    if not text:
        return "Paste an SMS above to analyse it.", "", ""
    if not re.search(r"[A-Za-zÀ-ÿ]", text):
        return "This message has no words (only numbers, emojis or symbols): nothing to analyse.", "", ""

    note = []
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        note.append(f"Message cut to its first {MAX_CHARS} characters (an SMS is rarely longer).")

    norm = normalize(text)
    p = float(p_spam([norm])[0])
    if p >= SCAM:
        verdict = f"🔴 **Likely a scam** ({p:.0%})\n\nDo not click the link or reply. Contact the organisation through its official app or website. In France, forward the SMS to **33700**."
    elif p >= SUSPICIOUS:
        verdict = f"🟠 **Suspicious** ({p:.0%})\n\nSome signs of a scam. Do not click any link before checking with the sender through an official channel."
    else:
        verdict = f"🟢 **Probably safe** ({p:.0%})\n\nNo strong scam signal. Stay careful if the message asks for money, codes or personal details."

    words = set(re.findall(r"[a-zà-ÿ']+", text.lower()))
    if len(words & FRENCH_WORDS) >= 2:
        note.append("This message looks French. The model was trained on English SMS and misses many French scams (38% caught in our tests): treat a 🟢 with caution.")
    if len(words) < 3:
        note.append("Very short message: the verdict is unreliable.")
    if note:
        verdict += "\n\n> ⚠️ " + "\n>\n> ⚠️ ".join(note)

    flags = [name for name, pat in RED_FLAGS.items() if re.search(pat, norm + " " + text, re.IGNORECASE)]
    flags_md = "### Warning signs\n" + ("\n".join(f"- {f}" for f in flags) if flags else "- None of the usual warning signs")

    infl = influential_words(norm, p)
    infl_md = "### Words that drove the decision\n" + "\n".join(f"- `{w}` {'↑ towards scam' if d > 0 else '↓ towards safe'} ({d:+.0%})" for w, d in infl) or "- (message too short)"

    return verdict, flags_md, infl_md


EXAMPLES = [  # real messages from the test sets (notebooks 02 and 03), never seen in training
    ["Info ANTAI : Vous avez un retard de paiement de 35,00e, consulter mon dossier d'infraction via : https://reglements-contraventions-paiement.com"],
    ["Votre nouvelle carte vitale est disponible. Veuillez remplir le formulaire afin de continuer a etre couvert : ameli-secu.fr."],
    ["USPS: the scheduled delivery for the package [number] x [number] ba has been changed. Please confirm here: [url]"],
    ["Pour ce soir on se rejoint en ville ? je bois un coup et je vois les gens de ma classe en vous attendant. Ca vous va ? Genre vous me textotez des que vous etes en ville"],
    ["I gotta collect da car at 6 lei."],
    ["Royal Mail: Sorry we were unable to deliver your parcel please reschedule your delivery via:"],
]

with gr.Blocks(title="Scam SMS detector") as demo:
    gr.Markdown("# 📱 Scam SMS detector\nPaste a text message to estimate whether it is a scam (fake parcel, fine, bank, Ameli, CPF…).")
    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(lines=5, label="SMS", placeholder="Paste the message here…")
            btn = gr.Button("Analyse", variant="primary")
            gr.Examples(EXAMPLES, inputs=inp, label="Real examples from our test sets")
        with gr.Column(scale=2):
            verdict = gr.Markdown()
            flags = gr.Markdown()
            infl = gr.Markdown()
    with gr.Accordion("How it works and its limits", open=False):
        gr.Markdown(f"""
- **Model:** TF-IDF on character n-grams + logistic regression, trained on the UCI SMS Spam Collection (5,158 English SMS, 2010–2012). Links become `URL` and numbers `NUM` before analysis.
- **Thresholds:** ≥ {SCAM:.0%} scam, {SUSPICIOUS:.0%}–{SCAM:.0%} suspicious. Chosen on our real-world test: at {SUSPICIOUS:.0%}, about 90% of scams are flagged, for about 14% false alarms.
- **Words that drove the decision:** each word is removed in turn and the change in scam probability is measured.
- **Warning signs** are simple rules, independent of the model.
- **Limits:** trained on old English data. It catches ~64% of English scams but only ~38% of French ones at the 50% threshold. Never rely on it alone.
""")
    outputs = [verdict, flags, infl]
    btn.click(analyse, inp, outputs)
    inp.submit(analyse, inp, outputs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="create a public link")
    demo.launch(share=parser.parse_args().share)
