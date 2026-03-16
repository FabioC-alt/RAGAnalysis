#!/usr/bin/env python3
import csv, random, re
from pathlib import Path

INPUT = "BlendedChunking/phrase_classification_data.csv"
OUTPUT = "BlendedChunking/phrase_classification_10000.csv"

# Read source
with open(INPUT, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = [r for r in reader]

if not data:
    raise SystemExit("Source CSV is empty")

# Build expanded AI vocabulary
ai_words = [
    "Transformer", "Attention", "Gradient", "Backpropagation", "Epoch", "Hyperparameter",
    "Quantization", "Fine-tuning", "Inference", "Hallucination", "Embeddings", "Latent",
    "Self-Attention", "Multi-head", "Tokenization", "Encoding", "Decoding", "Context",
    "Vector", "Similarity", "Prompt", "Few-shot", "Zero-shot", "RLHF", "Optimization",
    "Architecture", "Layer", "Node", "Neuron", "Weight", "Bias", "Activation", "Softmax"
]

# Write synthetic dataset generator script
with open(INPUT, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = [r for r in reader]

vocab = set()
for r in data:
    vocab.update(re.findall(r"\w+", r['Text']))
vocab.update(ai_words)
vocab = sorted(list([w for w in vocab if len(w) > 2]))

templates = [
    "The {0} mechanism allows the model to focus on {1} within the {2} sequence.",
    "During {0}, the {1} is updated using {2} and stochastic gradient descent.",
    "{0} is a common technique to reduce {1} latency in {2} environments.",
    "A {0} represents the {1} of a given {2} in high-dimensional space.",
    "We used {0} to improve the {1} of our {2} for specific domain tasks.",
    "The {0} layer applies {1} to the {2} sum of previous outputs.",
    "Managing {0} is crucial when designing {1} for large-scale {2} processing.",
    "Evaluating {0} requires a robust {1} to minimize {2} in outputs."
]

def special_char_ratio(text):
    s = sum(1 for c in text if not c.isalnum() and not c.isspace())
    return s / max(1, len(text))

def avg_word_len(text):
    words = text.split()
    return sum(len(w) for w in words) / max(1, len(words))

def verb_density(text):
    # Approximation without heavy NLP
    verbs = {"is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "can", "could", "shall", "should", "will", "would", "may", "might", "must", "train", "compute", "process", "retrieve", "generate", "optimize", "learn"}
    words = [w.strip('.,!?:;()[]"\'').lower() for w in text.split()]
    vc = sum(1 for w in words if w in verbs)
    return vc / max(1, len(words))

out = []
seen_texts = set()
n_target = 10000

while len(out) < n_target:
    # Weighted choice: 30% Syntactic (identifiers), 70% Semantic (sentences)
    is_id_style = random.random() < 0.3
    label = "Syntactic" if is_id_style else "Semantic"
    
    if is_id_style:
        # Generate varied identifier styles
        style = random.choice(["snake", "camel", "pascal"])
        parts = random.sample(vocab, random.randint(1, 3))
        if style == "snake":
            text = "_".join(p.lower() for p in parts)
        elif style == "camel":
            text = parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
        else: # pascal
            text = "".join(p.capitalize() for p in parts)
    else:
        # Generate Semantic sentences using templates
        tpl = random.choice(templates)
        words_fill = random.sample(vocab, 3)
        text = tpl.format(*words_fill)
        # Randomly append or prepend 
        if random.random() < 0.2:
            text = random.choice(vocab) + ": " + text
            
    if text in seen_texts:
        continue
    seen_texts.add(text)
    
    tc = len(re.findall(r"\w+", text))
    scr = round(special_char_ratio(text), 3)
    vd = round(verb_density(text), 3)
    awl = round(avg_word_len(text), 2)

    out.append({
        'Text': text,
        'Token_Count': tc,
        'Special_Char_Ratio': scr,
        'Verb_Density': vd,
        'Avg_Word_Length': awl,
        'Is_Identifier_Style': 1 if is_id_style else 0,
        'Label': label,
    })

# Shuffle results to mix classes
random.shuffle(out)

Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    writer.writeheader()
    writer.writerows(out)

print("Wrote", OUTPUT)
