"""
Performs offline solving against data using a set amount of MFCCS (defined by variable CONTROL_SIZE),
and prints out accuracy.
"""

import librosa
import os
import pickle
import random
import time
import matplotlib.pyplot as plt

from fastdtw import fastdtw
from operator import itemgetter


MFCC_PATH = "mfccs_all.pickle"
CONTROL_SIZE = 250

RUN_LIMIT = 10


def detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=10):
    trim_ms = 0  # ms
    while sound[trim_ms:trim_ms + chunk_size].dBFS < silence_threshold:
        trim_ms += chunk_size

    return trim_ms


def plot(f1, f2):
    plt.plot(f1, color='red', alpha=0.5)
    plt.plot(f2, color='blue', alpha=0.5)
    plt.show()


def mfcc(f):
    y1, sr1 = librosa.load(f)
    return librosa.feature.mfcc(y1, sr1).T


def build_mfccs(fs):
    mfccs = {}
    print "No MFCCs found, building..."
    for path in fs:
        if os.path.exists(path + "/oracle"):
            digits = [f for f in os.listdir(path) if "_0" in f]
            if len(digits) == 10:
                for i in range(0, 10):
                    m = mfcc(path + "/" + digits[i])
                    mfccs[path + "/" + digits[i]] = m
    with open(MFCC_PATH, 'wb') as handle:
        pickle.dump(mfccs, handle)
    return mfccs


def build_controls(fs):
    control = {}
    control_files = {}
    for path in fs:
        if os.path.exists(path + "/oracle"):
            oracle = open(path + "/oracle").read()
            oracle_nums = list(oracle)
            digits = [f for f in os.listdir(path) if "_0" in f]
            if len(digits) == 10:
                for i in range(0, 10):
                    num = int(oracle_nums[i])
                    if num not in control:
                        control[num] = []
                    if len(control[num]) < CONTROL_SIZE:
                        control[num].append(all_mfccs[path + "/" + digits[i]])
                        control_files[path + "/" + digits[i]] = True
    return control, control_files


control_files = {}
control = []
fs = []
bites = {}
all_mfccs = {}
for root, dirs, files in os.walk("data/"):
    fs.extend([root + f for f in dirs])
random.shuffle(fs)

if os.path.exists(MFCC_PATH):
    print("Found saved MFCCs, reading")
    with open(MFCC_PATH, 'rb') as handle:
        all_mfccs = pickle.load(handle)
else:
    all_mfccs = build_mfccs(fs)
    print("Processing...")
control, control_files = build_controls(fs)

correct = 0
wrong = 0
total = 0
accuracy = {}
totals = {}
to_break = False
time1 = time.time()
for path in fs:
    print total
    if to_break:
        break
    if os.path.exists(path + "/oracle"):
        oracle = open(path + "/oracle").read()
        oracle_nums = list(oracle)
        digits = [f for f in os.listdir(path) if "_0" in f]
        if len(digits) == 10:
            for i in range(0, 10):
                if total >= RUN_LIMIT:
                    to_break = True
                    break

                if path + "/" + digits[i] in control_files:
                    continue

                m = all_mfccs[path + "/" + digits[i]]
                if oracle_nums[i] not in accuracy:
                    accuracy[oracle_nums[i]] = 0
                    totals[oracle_nums[i]] = 0
                opts = []
                for digit in control:
                    ds = []
                    for cm in control[digit]:
                        ds.append(min(fastdtw(cm, m)[0], fastdtw(m, cm)[0]))
                    opts.append(min(ds))
                best = min(enumerate(opts), key=itemgetter(1))[0]
                if int(oracle_nums[i]) == best:
                    correct += 1
                    accuracy[oracle_nums[i]] += 1
                else:
                    wrong += 1
                totals[oracle_nums[i]] += 1
                total += 1

time2 = time.time()
print 'took %0.3f ms' % (time2 - time1)

print accuracy
print totals
print "CORRECT: %d (%f)" % (correct, correct / float(total))
print "INCORRECT: %d (%f)" % (wrong, wrong / float(total))
print "TOTAL: %d" % (total)
print "%d" % CONTROL_SIZE
