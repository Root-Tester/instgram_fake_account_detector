"""Generate a reproducible starter dataset for post-content model development.

The output is synthetic and weakly labeled. It is useful for pipeline testing,
not for claiming real-world model accuracy.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

REAL_TEMPLATES = [
    "Community volunteers met Saturday to restore the public garden.",
    "The local library announced its updated opening hours for this month.",
    "Our newsroom published a report on the annual climate survey.",
    "The museum opens a new exhibition next week. Tickets are available on the official website.",
    "The city council shared the agenda for its next public meeting.",
    "A quiet morning walk and a few photographs from the coast.",
    "The school team celebrated its regional championship with supporters.",
    "The health department released an official public information bulletin.",
    "Applications for the public service internship are listed on the agency website.",
    "Thank you to everyone who joined our community clean-up event.",
]

FAKE_TEMPLATES = [
    "URGENT! Guaranteed income job vacancy. No experience required. DM now to apply.",
    "Congratulations, you won a prize! Send a processing fee or gift card payment today.",
    "Official account notice: verify your account immediately using the link in our bio.",
    "Exclusive crypto investment offer. Transfer bitcoin to our wallet for guaranteed returns.",
    "Limited-time giveaway! Share this post, tag friends, and send a payment to claim your reward.",
    "Work from home and earn easy money. Pay a small registration fee to start today.",
    "Breaking news! Send your details and payment now before this secret offer expires.",
    "Government grant available now. Contact this account and pay the release charge.",
    "You have been selected as a winner. DM your password and wallet address to receive funds.",
    "Act now: your account will be closed unless you confirm your information through this link.",
]

MODIFIERS = [
    " Learn more from the official source.",
    " Details are available in the profile link.",
    " Please check the date and location before sharing.",
    " #community #update",
    " Contact the listed organization directly for confirmation.",
]


def generate_dataset(output: str | Path, rows: int = 50_000, seed: int = 42) -> None:
    if rows < 2:
        raise ValueError("rows must be at least 2")
    random_generator = random.Random(seed)
    path = Path(output)
    with path.open("w", encoding="utf-8") as handle:
        for index in range(rows):
            label = index % 2
            templates = FAKE_TEMPLATES if label else REAL_TEMPLATES
            text = random_generator.choice(templates) + random_generator.choice(MODIFIERS)
            row = {
                "id": f"synthetic-{index + 1:06d}",
                "text": text,
                "label": label,
                "label_name": "fake" if label else "real",
                "source_type": "synthetic_template",
            }
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    print(f"Generated {rows:,} synthetic labeled posts at {path}")
    print("Class balance: 50% real, 50% fake")
    print("Warning: do not use this synthetic set as evidence of real-world accuracy.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic labeled post text data.")
    parser.add_argument("--output", default="post_training_dataset.jsonl")
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    generate_dataset(arguments.output, arguments.rows, arguments.seed)
