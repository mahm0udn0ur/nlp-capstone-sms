"""Text normalisation shared by the notebooks and the app.

Every dataset is put in the same format before training or predicting:
links become the token URL and numbers become NUM, whatever their original form
(raw "https://...", bare "ameli-secu.fr", or the placeholders [url] / [number] used by some datasets).
Without this, a model could learn the *format* of a dataset instead of the content of the message.
"""
import html
import re

_TLDS = r"(?:fr|com|net|org|info|co|uk|io|me|ly|ms|vc|be|de|es|it|eu|in|us|xyz|top|site|online|app|link|gouv)"
_URL = re.compile(
    r"\[url\]"                                        # placeholder used by some datasets
    r"|https?://\S*"                                  # full links, even truncated ("https://")
    r"|www\.\S+"
    r"|\b[\w-]+(?:\.[\w-]+)*\." + _TLDS + r"\b(?:/\S*)?",   # bare domains: ameli-secu.fr, bit.ly/abc
    re.IGNORECASE,
)
_NUM = re.compile(r"\[number\]|\+?\d[\d\s.,/-]*\d|\d")


def normalize(text: str) -> str:
    t = html.unescape(str(text)).replace("<#>", " ")
    t = _URL.sub(" URL ", t)
    t = _NUM.sub(" NUM ", t)
    return re.sub(r"\s+", " ", t).strip()
