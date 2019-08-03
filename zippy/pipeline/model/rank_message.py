"""Module to apply the rank algorithm to emails."""

import os
import pathlib
import pickle

import nltk
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from tensorflow import keras

from zippy.pipeline.data import parse_email

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

SIMPLE_MODEL = pathlib.Path(__file__).parents[3] / "output/models/simplerank"
INTENT_MODEL = (
    pathlib.Path(__file__).parents[3] / "output/models/intent/intent-bi-lstm-highest.h5"
)

with open(INTENT_MODEL.parents[0] / "tokenizer.pickle", "rb") as handle:
    TOKENIZER = pickle.load(handle)

try:
    VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words("english"))


def create_user_model(user):
    """Initialize directory and user models for given user."""
    user_model_dir = SIMPLE_MODEL / user
    user_model_dir.mkdir()

    from_wt = pd.DataFrame(columns=["From", "weight"])
    from_wt.to_csv(user_model_dir / "from_weight.csv", index=False)

    thread_sender_wt = pd.DataFrame(columns=["From", "freq", "weight"])
    thread_sender_wt.to_csv(user_model_dir / "thread_senders_weight.csv", index=False)

    thread_wt = pd.DataFrame(
        columns=["freq", "time_span", "weight", "min_time", "thread"]
    )
    thread_wt.to_csv(user_model_dir / "thread_weights.csv", index=False)

    thread_term_wt = pd.DataFrame(columns=["term", "weight"])
    thread_term_wt.to_csv(user_model_dir / "thread_term_weights.csv", index=False)

    msg_term_wt = pd.DataFrame(columns=["freq", "term", "weight"])
    msg_term_wt.to_csv(user_model_dir / "msg_terms_weight.csv", index=False)

    previous_ranks = pd.DataFrame(
        columns=["date", "from", "rank", "subject", "priority", "intent"]
    )
    previous_ranks.to_csv(user_model_dir / "rank_df.csv", index=False)
    threshold = 0

    return (
        from_wt,
        thread_sender_wt,
        thread_wt,
        thread_term_wt,
        msg_term_wt,
        threshold,
    )


def get_sequence(message, tokenizer):
    """Return the text as a sequence vector."""
    tokenizer.fit_on_texts([message])
    sequences = tokenizer.texts_to_sequences([message])
    sequence = keras.preprocessing.sequence.pad_sequences(sequences, maxlen=50)
    return sequence


def load_weights(user: str = "global"):
    """Load weights from the CSV."""
    from_wt = pd.read_csv(SIMPLE_MODEL / user / "from_weight.csv")
    thread_sender_wt = pd.read_csv(SIMPLE_MODEL / user / "thread_senders_weight.csv")
    thread_wt = pd.read_csv(SIMPLE_MODEL / user / "thread_weights.csv")
    thread_term_wt = pd.read_csv(SIMPLE_MODEL / user / "thread_term_weights.csv")
    msg_term_wt = pd.read_csv(SIMPLE_MODEL / user / "msg_terms_weight.csv")
    previous_ranks = pd.read_csv(SIMPLE_MODEL / user / "rank_df.csv")
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
    subject = msg["Subject"][0]
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


def calculate_rank(msg, weights=None):
    """Calculate the rank score."""
    # load weights if not passed.
    if not weights:
        if (SIMPLE_MODEL / msg["To"][0]).exists():
            weights = load_weights(msg["To"][0])
        else:
            weights = create_user_model(msg["To"][0])
    elif weights == "global":
        weights = load_weights("global")
    else:
        weights = weights

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
    print(
        "Weights are from: {0},\n\tthread_from: {1},\n\tthread: {2}, \n\tthread_term: {3}, \n\tmsg_term: {4}".format(
            msg_from_wt,
            msg_thread_from_wt,
            msg_thread_activity_wt,
            msg_thread_term_wt,
            msg_terms_wt,
        )
    )

    return [rank, threshold]


def rank_message(message):
    """Rank the email and determine if email should be prioritized."""
    msg = pd.DataFrame(parse_email.get_from_message(message))

    user_model_rank, user_model_threshold = calculate_rank(msg)
    global_model_rank, global_model_threshold = calculate_rank(msg, weights="global")

    rank = user_model_rank + global_model_rank

    threshold = user_model_threshold + 0.1 * global_model_threshold

    # rank = 1 / (1 + np.exp(-weighted_rank/weighted_threshold))

    intent_model = keras.models.load_model(INTENT_MODEL)

    content: str = msg["content"][0]

    # parts = (*content.splitlines(), msg["Subject"][0])
    # intent_score = intent_model.predict(
    #     [get_sequence(part, TOKENIZER) for part in parts]
    # )
    intent_score = intent_model.predict(get_sequence(msg["Subject"][0], TOKENIZER))

    return [msg, rank, rank > threshold, np.mean(intent_score) > 0.5, threshold]
