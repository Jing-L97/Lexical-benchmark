import numpy as np
import math
from scipy.special import comb
from scipy.stats import norm
import pandas as pd
from lm_benchmark.utils import TokenCount

#################################################################################################
# function definitions useful for estimating theoretical probabilities of generations in the accumulator model
#################################################################################################
## custom numerical format
def custom_format(num):
    if (not np.isnan(num)) and num == int(num):  # Check if the number is effectively an integer
        return f"{int(num)}"
    elif 0.001 < abs(num) < 1000:  # Check if the number is between 0 and 0.001
        return f"{num:.3g}"
    else:  # For all other cases, print in scientific notation
        return f"{num:.3e}"

def p_miss(p, n):
    """Computes the probability of observing zero instances of an event with probability p after n draws
    Application: probability of not seeing a word with probability p in a corpus of size n words
    """
    return (1 - p) ** n


def p_obs_k_e(k, p, n):
    """
    Computes the probability of observing k instances of an event with probability p after n draws
    Exact formula using Bernouilli coefficients; crashes for k>50 and large n
    prob= C(n,k) * p^k * (1-p)^(n-k)
    """
    prob = np.nan
    if (k < 50) or (k > n - 50) or (n < 1000000):
        prob = comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    return prob


def p_obs_k_p(k, p, n):
    """
    Approximates the probability of observing k instances of an event with probability p after n draws
    Poisson approximation, crashes for k>150; valid only for p small, n large, np moderate
    prob= (l^k) * e^-l / n!   with l=n*p
    """
    lambd = p * n
    prob = np.nan
    # print(lambd,k)
    if (k < 150) and (np.log10(lambd) * k < 300):
        prob = (lambd ** k) * np.exp(-lambd) / math.factorial(k)
    return prob


def p_obs_k_ps(k, p, n):
    """
    Approximates the probability of observing k instances of an event with probability p after n draws
    Poisson approximation with Stirling approximation for factorial, crashes for k>800; valid only for p small, n large, np moderate
    prob= ((l/k*e)^k) * e^-l / sqrt(2k*pi)   with l=n*p
    """
    lambd = p * n
    prob = np.nan
    if (k > 0) and (np.log10(lambd / k * np.e) * k < 300):
        prob = ((lambd / k * np.e) ** k) * np.exp(-lambd) / np.sqrt(2 * k * np.pi)
    return prob


def phi(mu, sd, x):
    """Cumulative function for a gaussian of mean mu and standard deviation sd"""
    return norm.cdf((x - mu) / sd)


def p_obs_k_g(k, p, n):
    """
    Approximates the probability of observing k instances of an event with probability p after n draws
    Gaussian approximation, never crashes; valid only for np>5 and n(1-p)>5
    prob==phi(k+0.5)-phi(k-0.5); where phi(x)=unitnormalCDF((x-mu)/sd), mu=n*p, sd=np.sqrt(n*p*(1-p))
    """
    mu = n * p
    sd = np.sqrt(n * p * (1 - p))
    return phi(mu, sd, k + 0.5) - phi(mu, sd, k - 0.5)


def p_obs_k(k, p, n):
    """Computes the probability of observing k instances of an event with probability p after n draws
    Application: probability of seeing a word k times, assuming it has probability p, in a corpus of size n words
    Uses various approximations to avoid crashing, and being approx correct
    """

    prob = p_obs_k_e(k, p, n)  # exact bernouilli
    if np.isnan(prob):
        prob = p_obs_k_p(k, p, n)  # Poisson Approx
    if np.isnan(prob):
        prob = p_obs_k_ps(k, p, n)  # Poisson Stirling Approx
    if np.isnan(prob):
        prob = p_obs_k_g(k, p, n)  # Gaussian Approx
    return prob


def p_obs_less_than_k(k, p, n):
    """Computes the probability of observing strictly less than k instances of an event with probability p after n draws
    Application: probability of seeing a word k times, assuming it has probability p, in a corpus of size n words
    Uses various approximations to avoid crashing, and being approx correct
    """
    pless = 0
    for i in range(k):
        pless += p_obs_k(i, p, n)
    return pless


def p_obs_k_list(k, p, n):
    """function used to debug"""
    return {'exact': p_obs_k_e(k, p, n), 'Poisson': p_obs_k_p(k, p, n), 'PoissonStir': p_obs_k_ps(k, p, n),
            'Gaussian': p_obs_k_g(k, p, n), 'total': p_obs_k(k, p, n)}


def accu_model_tok_stats(token_count, ref_corpus_size, gen_corpus_size=None):
    """Token Frequency stats for a token observed token_count times in the reference corpus (of size ref_corpus_size)
    in new corpus generated by an accumulator model with perfect memory trained on the reference corpus.
    The generated corpus size (gen_corpus_size) by default is of the same size as the reference, but can differ.
    Returned values:
       p_miss: probability of missing the word in the generated corpus
       p_once: probability of observing the word once
       p_same: probability of observing the word with the expected count (taking into account differences in corpus size)
       p_less: probability of observing the word with less than the expected count (including zero)
       p_more: probability of observing the word with more than the expected count
       score: expected score where score=1 if observed count is seen more than expected and -1 if less
    """
    if gen_corpus_size is None:
        gen_corpus_size = ref_corpus_size

    prob_token = token_count / ref_corpus_size
    gen_token_count = int(round(1.0 * token_count / ref_corpus_size * gen_corpus_size))

    pmiss = p_miss(prob_token, gen_corpus_size)
    ponce = p_obs_k(1, prob_token, gen_corpus_size)
    psame = p_obs_k(gen_token_count, prob_token, gen_corpus_size)
    pless = p_obs_less_than_k(gen_token_count, prob_token, gen_corpus_size)
    pmore = 1 - psame - pless
    score = pless * -1 + pmore
    return {'p_miss': pmiss, 'p_once': ponce, 'p_same': psame, 'p_less': pless, 'p_more': pmore, 'score': score}


### defining an accumulator model based on a reference corpus
def make_accu(ref_count:TokenCount)->TokenCount:
   """Make a corpus from an accumulator model based on ref_count. Returns a TokenCount."""
   accucountarray=np.random.multinomial(ref_count.nb_of_tokens(), ref_count.df["count"]/ref_count.nb_of_tokens())
   accuwords=ref_count.df['word']
   accu_count=TokenCount(dict(zip(accuwords,accucountarray)),name="accu")
   accu_count.df=accu_count.df[accu_count.df["count"]!=0]
   return accu_count



# get the accumulator model from the largest training set
def segment_into_chunks(input_file, num_chunks):

    """only get the traindat freq"""
    # Read the text file into a DataFrame
    df = pd.read_csv(input_file)
    total_words = df['num_tokens'].sum()
    # Calculate the approximate number of words per chunk
    words_per_chunk = math.ceil(total_words / num_chunks)

    # Initialize variables
    current_chunk_number = 1
    current_chunk_word_count = 0
    chunk_numbers = []

    # Assign chunk numbers to each sentence
    for _, row in df.iterrows():
        sentence_word_count = row['count']
        if current_chunk_word_count + sentence_word_count > words_per_chunk and current_chunk_number < num_chunks:
            current_chunk_number += 1
            current_chunk_word_count = 0
        chunk_numbers.append(current_chunk_number)
        current_chunk_word_count += sentence_word_count

    # Add the chunk numbers to the DataFrame
    df['month'] = chunk_numbers
    return df
