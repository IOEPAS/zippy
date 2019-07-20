"""Module for online training new email messages."""

import nltk
import pathlib

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

MODEL_DIR = pathlib.Path(__file__).parents[3] / "output/models/simplerank"

try:
    VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words("english"))

def load_weights():
    """Load weights from the CSV."""
    from_wt = pd.read_csv(MODEL_DIR / "from_weight.csv")
    thread_sender_wt = pd.read_csv(
        MODEL_DIR / "thread_senders_weight.csv"
    )
    thread_wt = pd.read_csv(MODEL_DIR / "thread_weights.csv")
    thread_term_wt = pd.read_csv(MODEL_DIR / "thread_term_weights.csv")
    msg_term_wt = pd.read_csv(MODEL_DIR / "msg_terms_weight.csv")
    rank_df = pd.read_csv(MODEL_DIR / "rank_df.csv")
    return (
        from_wt,
        thread_sender_wt,
        thread_wt,
        thread_term_wt,
        msg_term_wt,
        rank_df
    )

def update_from_weights(email, from_weight):
    """Update weights of email senders."""
    if email['From'][0] in from_weight.From.values:
        index = from_weight[from_weight.From == email['From'][0]].index.values
        current_weight = from_weight.loc[index, 'weight'].values
        from_weight.at[index, 'weight'] = np.log(np.exp(current_weight) + 1)
        print('senders weight updated')
    else:
        row = {
            'From': email['From'][0],
            'weight': np.log(2)
        }
        from_weight = from_weight.append(row, ignore_index=True)
        print('new sender added')
    from_weight.to_csv(MODEL_DIR / 'from_weight.csv', index=False)


def update_thread_senders_weights(email, thread_senders_weights):
    """Update weights of email senders using new threads."""
    if email['From'][0] in thread_senders_weights.From.values:
        index = thread_senders_weights[thread_senders_weights.From == email['From'][0]].index.values
        current_weight = thread_senders_weights.loc[index, 'weight'].values
        thread_senders_weights.at[index, 'weight'] = np.log(np.exp(current_weight) + 1)
        print('senders weight in thread updated')
    else:
        row = {
            'From': email['From'][0],
            'weight': np.log(2)
        }
        thread_senders_weights = thread_senders_weights.append(row, ignore_index=True)
        print('new sender from thread added')
        thread_senders_weights.to_csv(MODEL_DIR / 'thread_senders_weight.csv', index=False)


def update_thread_weights(email, thread_weights):
    """Update thread weights using new threads."""
    if email['Subject'][0] in thread_weights.thread.values:
        index = thread_weights[thread_weights.thread == email['Subject'][0]].index.values
        current_freq = thread_weights.loc[index, 'freq'].values
        if current_freq < 2:
            thread_weights.at[index, 'freq'] = current_freq + 1
        else:
            min_time = thread_weights.loc[index, 'min_time'].values
            new_timespan = (pd.to_datetime(email['Date']) - pd.to_datetime(min_time)).total_seconds()
            thread_weights.at[index, 'time_span'] = new_timespan
            thread_weights.at[index, 'weight'] = 10 + np.log10(current_freq / new_timespan)
        print('thread weight updated')
    else:
        row = {
            'thread': email['Subject'],
            'weight': 1.,
            'time_span': 0.,
            'freq': 1,
            'min_time': pd.to_datetime(email['Date'])
        }
        thread_weights = thread_weights.append(row, ignore_index=True)
        print('new thread added')
        thread_weights.to_csv(MODEL_DIR / 'thread_weights.csv', index=False)


def update_thread_terms_weights(thread_term_weights, thread_weights, thread_tdm):
    """Update threads weights using new terms in thread subjects."""
    for term in thread_tdm.columns:
        if term in thread_term_weights.term.values:
            index = thread_term_weights[thread_term_weights.term == term].index.values
            updated_weight = thread_weights.weight[thread_weights.thread.str.contains(term, regex=False)].mean()
            if type(updated_weight) == type(np.float):
                updated_weight = 1.0
            thread_term_weights.at[index, 'weight'] = updated_weight
            print('terms from thread subject updated')
        else:
            weight = thread_weights.weight[thread_weights.thread.str.contains(term, regex=False)].mean()
            if type(weight) == type(np.nan):
                weight = 1.0
            row = {
            'term': term,
            'weight': weight
            }
            thread_term_weights = thread_term_weights.append(row, ignore_index=True)
            print('new term from thread subject added')
            thread_term_weights.to_csv(MODEL_DIR / 'thread_term_weights.csv', index=False)


def update_msg_terms_weights(msg_term_weights, msg_tdm):
    """Update weights using new terms in email content."""
    for term in msg_tdm.columns:
        if term in msg_term_weights.term.values:
            index = msg_term_weights[msg_term_weights.term == term].index.values
            current_weight = msg_term_weights.loc[index, 'weight'].values[0]
            current_freq = msg_term_weights.loc[index, 'freq'].values[0]
            term_frequency = msg_tdm.loc[:, term].values
            msg_term_weights.at[index, 'weight'] = np.log(np.exp(current_weight) + term_frequency)
            msg_term_weights.at[index, 'freq'] = current_freq + term_frequency
            print('terms from message content updated')
        else:
            row = {
            'freq': msg_tdm.loc[:, term].values[0],
            'term': term,
            'weight': np.log(msg_tdm.loc[:, term].values + 1)[0],
            }
            msg_term_weights = msg_term_weights.append(row, ignore_index=True)
            print('new terms from message added')
    msg_term_weights.to_csv(MODEL_DIR / 'msg_terms_weight.csv', index=False)

def add_new_email(email, rank_df, rank, priority, intent):
    """Add new emails after ranking."""
    date = pd.to_datetime(email["Date"][0], infer_datetime_format=True)
    row = {
        'date': str(date),
        'from': email['From'][0],
        'subject': email['Subject'][0],
        'rank': rank,
        'priority': priority,
        'intent': intent
    }
    rank_df = rank_df.append(row, ignore_index=True)
    print('new email added to rank dataset.')
    rank_df.to_csv(MODEL_DIR / 'rank_df.csv', index=False)

def online_training(email, rank, priority, intent):
    """Online training for new emails."""
    from_weight, *threads, msg_term_weights, rank_df = load_weights()
    (thread_from_wt, thread_activity_wt, thread_term_wt) = threads

    update_from_weights(email, from_weight)

    update_thread_senders_weights(email, thread_from_wt)

    update_thread_weights(email, thread_activity_wt)

    thread_term_vector = VEC.fit_transform(email["Subject"])
    thread_tdm = pd.DataFrame(thread_term_vector.toarray(), columns=VEC.get_feature_names())
    update_thread_terms_weights(thread_term_wt, thread_activity_wt, thread_tdm)

    msg_term_vector = VEC.fit_transform(email["content"])
    msg_tdm = pd.DataFrame(msg_term_vector.toarray(), columns=VEC.get_feature_names())
    update_msg_terms_weights(msg_term_weights, msg_tdm)

    add_new_email(email, rank_df, rank, priority, intent)
