"""Module to apply the rank algorithm to emails."""

import pathlib

import nltk
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from tensorflow import keras

from zippy.pipeline.data import parse_email

SIMPLE_MODEL = pathlib.Path(__file__).parents[3] / "output/models/simplerank"
INTENT_MODEL = (
    pathlib.Path(__file__).parents[3] / "output/models/intent/intent-model-lstm.h5"
)

VOCABULARY_SIZE = 20000
TOKENIZER = keras.preprocessing.text.Tokenizer(num_words=VOCABULARY_SIZE)

try:
    VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words("english"))


def get_sequence(message, tokenizer):
    """Return the text as a sequence vector."""
    tokenizer.fit_on_texts([message])
    sequences = tokenizer.texts_to_sequences([message])
    sequence = keras.preprocessing.sequence.pad_sequences(sequences, maxlen=50)
    return sequence


def load_weights():
    """Load weights from the CSV."""
    from_wt = pd.read_csv(SIMPLE_MODEL / "from_weight.csv", index_col=0)
    thread_sender_wt = pd.read_csv(
        SIMPLE_MODEL / "thread_senders_weight.csv", index_col=0
    )
    thread_wt = pd.read_csv(SIMPLE_MODEL / "thread_weights.csv", index_col=0)
    thread_term_wt = pd.read_csv(SIMPLE_MODEL / "thread_term_weights.csv", index_col=0)
    msg_term_wt = pd.read_csv(SIMPLE_MODEL / "msg_terms_weight.csv", index_col=0)
    previous_ranks = pd.read_csv(SIMPLE_MODEL / "rank_df.csv", index_col=0)
    threshold = previous_ranks["rank"].median()
    return (
        from_wt,
        thread_sender_wt,
        thread_wt,
        thread_term_wt,
        msg_term_wt,
        threshold,
    )


def get_weights(search_term, weight_df, term=True):
    """Get weights from thread subject or frequent terms."""
    search_term = str(search_term)
    search_length = len(search_term)
    if search_length > 0:
        if term:
            term_match = False
            for search_item in search_term:
                match = weight_df.term.str.contains(search_item, regex=False)
                term_match = term_match | match
        else:
            term_match = weight_df.thread.str.contains(search_term, regex=False)

        match_weights = weight_df.weight[term_match]
        match_length = len(match_weights)
        if match_length < 1:
            return 1
        return match_weights.mean()
    return 1


def get_weights_from_sender(message, from_weight):
    """Get weights from email sender."""
    from_wt = from_weight[from_weight["From"] == message["From"][0]]
    len_from = len(from_wt)
    if len_from > 0:
        return from_wt.weight
    return 1


def get_weights_from_thread(msg, thread_weights, count_vector):
    """Get weights for threads."""
    # using senders weights from threads
    senders_weight, thread_weights, thread_term_weights = thread_weights
    senders_wt = senders_weight[senders_weight["From"] == msg["From"][0]]
    len_senders = len(senders_wt)
    if len_senders > 0:
        msg_thread_from_wt = senders_wt.weight
    else:
        msg_thread_from_wt = 1

    # Then, from thread activity
    subject = msg["Subject"]
    msg_thread_activity_wt = get_weights(subject, thread_weights, term=False)

    # Then, weights based on terms in threads
    try:
        count_vector.fit_transform(list(msg["Subject"]))
        msg_thread_terms = count_vector.get_feature_names()
        msg_thread_term_wt = get_weights(msg_thread_terms, thread_term_weights)
    except ValueError:
        # Some subjects from the test set result in empty vocabulary
        msg_thread_term_wt = 1

    return (msg_thread_from_wt, msg_thread_activity_wt, msg_thread_term_wt)


def get_weights_from_terms(msg, msg_term_weights, count_vector):
    """Get weights from message terms."""
    try:
        count_vector.fit_transform(list(msg["content"]))
        msg_terms = count_vector.get_feature_names()
        msg_terms_wt = get_weights(msg_terms, msg_term_weights)
    except ValueError:
        # Some subjects from the test set result in empty vocabulary
        msg_terms_wt = 1
    return msg_terms_wt


def rank_message(message, weights=None):  # pylint: disable=too-many-locals
    """Rank the email and determine if email should be prioritized."""
    # load weights if not passed.
    if not weights:
        weights = load_weights()

    msg = pd.DataFrame(parse_email.get_from_message(message))
    msg["Date"] = pd.to_datetime(msg["Date"], infer_datetime_format=True)
    from_weight, *threads, msg_term_weights, threshold = weights
    # First, using the from weights
    msg_from_wt = get_weights_from_sender(msg, from_weight)
    # Secondly, from threads
    if msg["is_thread"][0]:
        threads = get_weights_from_thread(msg, threads, VEC)
        msg_thread_from_wt, msg_thread_activity_wt, msg_thread_term_wt = threads
    else:
        msg_thread_from_wt, msg_thread_activity_wt, msg_thread_term_wt = 1, 1, 1

    # Then, weights based on terms in message
    msg_terms_wt = get_weights_from_terms(msg, msg_term_weights, VEC)

    # Calculating Rank
    rank = (
        float(msg_from_wt)
        * float(msg_thread_from_wt)
        * float(msg_thread_activity_wt)
        * float(msg_thread_term_wt)
        * float(msg_terms_wt)
    )

    intent_model = keras.models.load_model(INTENT_MODEL)

    content: str = msg["content"][0]

    parts = (*content.splitlines(), msg["Subject"][0])
    intent_score = intent_model.predict(
        [get_sequence(part, TOKENIZER) for part in parts]
    )

    return [msg, rank, rank > threshold, np.mean(intent_score) > 0.5, threshold]
