import random
import string


def generate_random_string(n=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def chunk_list(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out
