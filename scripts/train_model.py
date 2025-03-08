import pandas as pd
import choix
import numpy as np
import collections
import json

# Load dataset
df = pd.read_csv("data/gifgif-dataset-20150121-v1.csv")

# Extract unique GIF IDs and map to integers
gif_ids = set(df["left"]).union(set(df["right"]))
gif_to_int = {gif: idx for idx, gif in enumerate(gif_ids)}
int_to_gif = {idx: gif for gif, idx in gif_to_int.items()}

# Process pairwise comparisons for each emotion
data = collections.defaultdict(list)

for _, row in df.iterrows():
    emotion, left, right, choice = row["metric"], row["left"], row["right"], row["choice"]
    
    if left not in gif_to_int or right not in gif_to_int:
        continue  # Skip unknown GIFs

    left_idx, right_idx = gif_to_int[left], gif_to_int[right]

    if choice == "left":
        data[emotion].append((left_idx, right_idx))
    elif choice == "right":
        data[emotion].append((right_idx, left_idx))

# Compute rankings with Bradley-Terry Model
emotion_rankings = {}

for emotion, pairs in data.items():
    num_gifs = len(gif_ids)

    if len(pairs) < 3:  # Skip emotions with too few comparisons
        continue

    # Train Bradley-Terry model
    params = choix.opt_pairwise(num_gifs, pairs)

    # Normalize rankings for stability
    scores = np.exp(params - np.mean(params))  # Normalize to avoid extreme values
    ranked_gifs = np.argsort(scores)[::-1]  # Highest first

    # Select top 5 GIFs for the emotion
    top_gifs = [int_to_gif[i] for i in ranked_gifs[:5] if i in int_to_gif]

    if len(top_gifs) < 5:  # If fewer than 5 exist, pad with random GIFs
        remaining_gifs = [gif for gif in gif_ids if gif not in top_gifs]
        top_gifs.extend(np.random.choice(remaining_gifs, 5 - len(top_gifs), replace=False))

    emotion_rankings[emotion] = top_gifs

# Save JSON output
with open("gif_metadata.json", "w") as f:
    json.dump(emotion_rankings, f, indent=4)

print("✅ GIF rankings saved to gif_metadata.json")
