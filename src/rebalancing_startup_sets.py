
import json
import copy
from copy import deepcopy
import random

# 1: Open original startup sets n=2000
# 2: Current (~500/1000) nS==2/nS==3 is 0.5 and shares nF==1, nF==2, nF==3 are 0.25, 0.47, 0.27
# 3: Rebalancing criteria: nS==2/nS==3 is 1 and within each group shares of nF==1, nF==2, nF==3 in the end shall be 0.33 each
# 4: To rebalance nS, set share nS==2/nS==3 to be 2. To rebalance nF, set share nF==1 and share nF==3 to be 0.4, share nF==2 to be 0.2
# 5: Steps
# 5.1: Subset each group for nS called nS2 and nS3
# 5.2: Within each group, rebalance nF
# 5.3: Copy all sets in nS2 and append to nS2 and append to nF3

# 1 Open
with open('startup_data.json', 'r') as f:
    data = json.load(f)

# Add composition variables to data

# Define list of names identifying female founders
female_names = ["Jessica", "Nancy", "Sarah"]

# Define exact self-evaluation phrases (copied from R logic)
self_eval_phrases = [
    "According to the founder's internal valuation model, the business is worth",
    "Using internal performance indicators, the founder estimates the start-up's value at",
    "The start-up valuation is based on the founder's long-term growth outlook, estimating it at"
]

for entry in data:
    startups = entry.get('startups', [])
    for startup in startups:
        # === Existing female founder flag ===
        first_name = startup['Assigned_Founder'].split()[0]
        startup['isfemale'] = 1 if first_name in female_names else 0

        # === Evaluator and Value extraction ===
        sentence = startup.get("Evaluation_sentence", "")
        if "$" in sentence:
            before_dollar, after_dollar = sentence.split("$", 1)
            evaluator = before_dollar.strip().rstrip(",.")
            value = "$" + after_dollar.strip().rstrip(".")
        else:
            evaluator = sentence.strip().rstrip(",.")
            value = None

        startup["Evaluator"] = evaluator
        startup["Value"] = value

        # === Self-evaluation flag ===
        startup["Selfevaluate"] = 1 if evaluator in self_eval_phrases else 0

    # === Count of female founders and self-evaluators per set ===
    entry['nFemInSet'] = sum(s['isfemale'] for s in startups)
    entry['nSelfInSet'] = sum(s['Selfevaluate'] for s in startups)


# 5.1. Subset nS
nS2_sets = [entry for entry in data if (entry['nSelfInSet'] == 2)]
nS3_sets = [entry for entry in data if (entry['nSelfInSet'] == 3)]

print(len(nS2_sets))
print(len(nS3_sets))

# 5.2. Rebalance nF within each nS
nS2_nF1 = [entry for entry in nS2_sets if (entry['nFemInSet'] == 1)]
nS2_nF2 = [entry for entry in nS2_sets if (entry['nFemInSet'] == 2)]
nS2_nF3 = [entry for entry in nS2_sets if (entry['nFemInSet'] == 3)]

print(len(nS2_nF1))
print(len(nS2_nF2))
print(len(nS2_nF3))
# 91 - 466 - 280
# rebalancing nF1 = 466*2 = 932 increase 9x. nF3 = 932 increase 2x. nF2 keeps at 466. Shall yield 2330 sets for nS2.

# next rebalance and reduce nS3 to be around 1165 sets

nS3_nF1 = [entry for entry in nS3_sets if (entry['nFemInSet'] == 1)]
nS3_nF2 = [entry for entry in nS3_sets if (entry['nFemInSet'] == 2)]
nS3_nF3 = [entry for entry in nS3_sets if (entry['nFemInSet'] == 3)]

print(len(nS3_nF1))
print(len(nS3_nF2))
print(len(nS3_nF3))
# 120 - 622 - 421
# rebalancing nF2 = 622/3 = 207. nF1 = 207*2 = 414 increase 2x. nF3 can be kept at 421. Shall yield 360 + 207 + 421 = 988 sets for nS3

# final ratio nS2/nS3 = 2216/988 = 2.2
# final ratio nF1/nF2/nF3 = (910+360)/(466+207)/(840+421) = 1270/673/1261 = 2:1:2 (0.4:0.2:0.4)

# rebalancing nF within nS2
# increase nF1 9x
copies = []
for entry in nS2_nF1:
    for _ in range(9):
        new_entry = copy.deepcopy(entry)
        copies.append(new_entry)

# Add copies to the original list
nS2_nF1.extend(copies)

print(len(nS2_nF1))

# increase nF3 2x
copies = []
for entry in nS2_nF3:
    for _ in range(2):
        new_entry = copy.deepcopy(entry)
        copies.append(new_entry)

# Add copies to the original list
nS2_nF3.extend(copies)

print(len(nS2_nF3))

# combine into new nS2
nS2_new = nS2_nF1 + nS2_nF2 + nS2_nF3

print(len(nS2_new))


# rebalancing nF within nS3
# randomly select one third of nF2
nS3_nF2_new = random.sample(nS3_nF2, 207)

print(len(nS3_nF2))
print(len(nS3_nF2_new))

# increase nF1 2x
copies = []
for entry in nS3_nF1:
    for _ in range(2):
        new_entry = copy.deepcopy(entry)
        copies.append(new_entry)

# Add copies to the original list
nS3_nF1.extend(copies)

print(len(nS3_nF1))

# combine into new nS3
nS3_new = nS3_nF1 + nS3_nF2_new + nS3_nF3

print(len(nS3_new))

# both
rebalance_sample = nS2_new + nS3_new

print(len(rebalance_sample))

# remove composition vars and save
for entry in rebalance_sample:
    if 'nFemInSet' in entry:
        del entry['nFemInSet']
    if 'nSelfInSet' in entry:
        del entry['nSelfInSet']
    for startup in entry.get('startups', []):
        if 'isfemale' in startup:
            del startup['isfemale']
        if 'Evaluator' in startup:
            del startup['Evaluator']
        if 'Value' in startup:
            del startup['Value']
        if 'Selfevaluate' in startup:
            del startup['Selfevaluate']


with open('startup_data_rebalance.json', 'w') as f:
    json.dump(rebalance_sample, f, indent=4)