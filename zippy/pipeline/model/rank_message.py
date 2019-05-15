"""Module to apply the rank algorithm to emails."""

import os
import pandas as pd
import nltk
from sklearn.feature_extraction.text import CountVectorizer

from zippy.pipeline.data import parse_email

MODELS = os.curdir + '/../../output/models/simplerank/'
VEC = CountVectorizer(stop_words=nltk.corpus.stopwords.words('english'))

def load_weights():
    """Load weights from the CSV."""

    from_wt = pd.read_csv(MODELS + 'from_weight.csv', index_col=0)
    thread_sender_wt = pd.read_csv(MODELS + 'thread_senders_weight.csv', index_col=0)
    thread_wt = pd.read_csv(MODELS + 'thread_weights.csv', index_col=0)
    thread_term_wt = pd.read_csv(MODELS + 'thread_term_weights.csv', index_col=0)
    msg_term_wt = pd.read_csv(MODELS + 'msg_terms_weight.csv', index_col=0)
    previous_ranks = pd.read_csv(MODELS + 'rank_df.csv', index_col=0)
    threshold = previous_ranks['rank'].median()
    return (from_wt, thread_sender_wt, thread_wt, thread_term_wt, msg_term_wt, threshold)

def get_weights(search_term, weight_df, term=True):
    """Get weights from thread subject or frequent terms."""

    search_term = str(search_term)
    if (len(search_term)>0):
        if term:
            term_match = False
            for search_item in search_term:
                match = weight_df.term.str.contains(search_item, regex=False)
                term_match = term_match | match
        else:
            term_match = weight_df.thread.str.contains(search_term, regex=False)
        
        match_weights = weight_df.weight[term_match]
        if len(match_weights)<1:
            return 1
        else:
            return match_weights.mean()
    else:
        return 1

def rank_message(message, weights):
    """Rank the email and determine if email should be prioritized."""

    msg = pd.DataFrame(parse_email.from_message(message))
    msg['Date'] = pd.to_datetime(msg['Date'], infer_datetime_format=True)
    from_weight, *threads, msg_term_weights, threshold = weights
    senders_weight, thread_weights, thread_term_weights = threads
    # First, using the from weights
    from_wt = from_weight[from_weight['From'] == msg['From'][0]]
    if len(from_wt)>0:
        msg_from_wt = from_wt.weight
    else:
        msg_from_wt = 1
    
    # Second, using senders weights from threads
    senders_wt = senders_weight[senders_weight['From'] == msg['From'][0]]
    if len(senders_wt)>0:
        msg_thread_from_wt = senders_wt.weight
    else:
        msg_thread_from_wt = 1
        
    # Then, from thread activity
    is_thread = len(msg.Subject.str.split('re: ')) > 1
    if is_thread:
        subject = msg.Subject.str.split('re: ')[1]
        msg_thread_activity_wt = get_weights(subject, thread_weights, term=False)
    else:
        msg_thread_activity_wt = 1
        
    # Then, weights based on terms in threads
    try:
        VEC.fit_transform(list(msg['Subject']))
        msg_thread_terms = VEC.get_feature_names()
        msg_thread_term_wt = get_weights(msg_thread_terms, thread_term_weights)
    except:
        # Some subjects from the test set result in empty vocabulary
        msg_thread_term_wt = 1
    
    # Then, weights based on terms in message
    try:
        VEC.fit_transform(list(msg['content']))
        msg_terms = VEC.get_feature_names()
        msg_terms_wt = get_weights(msg_terms, msg_term_weights)
    except:
        # Some subjects from the test set result in empty vocabulary
        msg_terms_wt = 1
        
    
    # Calculating Rank
    rank = float(msg_from_wt) * float(msg_thread_from_wt) * float(msg_thread_activity_wt) * float(msg_thread_term_wt) * float(msg_terms_wt)

    priority = rank > threshold
    
    return [message, rank, priority]