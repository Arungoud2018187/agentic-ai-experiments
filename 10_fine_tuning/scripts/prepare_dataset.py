"""Generate the generic and domain-specific fine-tuning datasets.

The generic corpus represents broad incident descriptions; the domain
corpus contains security-specific telemetry vocabulary.  Fine-tuning on
the domain corpus adapts a model pretrained on the generic corpus.
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

LABELS = ["benign", "ddos", "insider", "malware", "phishing"]

DOMAIN_INDICATORS = {
    "phishing": [
        "email impersonates the payroll portal and requests credentials",
        "credential harvesting page linked from a spoofed sender domain",
        "urgent password reset message with a shortened URL",
        "invoice attachment contains a link to a fake login page",
        "smishing campaign targets employees with MFA prompts",
        "business email compromise requests a wire transfer",
        "lookalike domain imitates the identity provider",
        "email gateway flags a display-name spoof",
        "user reports a suspicious DocuSign notification",
        "phishing kit clones the corporate SSO page",
    ],
    "malware": [
        "ransomware encrypted the shared finance drive",
        "trojan dropped a second-stage payload from a temp directory",
        "keylogger installed as a browser extension",
        "command and control beacon contacts a rare external domain",
        "worm spreads through removable media",
        "fileless malware injected into a running process",
        "credential stealer reads browser password stores",
        "remote access trojan persists through a scheduled task",
        "malicious macro executes when the document opens",
        "EDR quarantines a signed binary with a known malicious hash",
    ],
    "ddos": [
        "volumetric SYN flood saturates the edge router",
        "DNS amplification traffic spikes to 40 Gbps",
        "HTTP request flood exhausts the web tier",
        "botnet traffic causes service unavailable errors",
        "UDP reflection attack targets the public gateway",
        "application-layer attack overwhelms the login endpoint",
        "traffic spike from thousands of compromised hosts",
        "network link saturation triggers upstream scrubbing",
        "slowloris connections exhaust the connection pool",
        "NTP monlist reflection floods the perimeter",
    ],
    "insider": [
        "employee copied the customer database to a USB drive",
        "privileged account accessed payroll records after hours",
        "contractor exfiltrated source code before offboarding",
        "insider altered financial records to hide a transfer",
        "user shared admin credentials with a colleague",
        "departing employee downloaded sensitive documents",
        "analyst queried records outside their assigned region",
        "service account used from an unusual workstation",
        "employee disabled audit logging on a production host",
        "data hoarding detected in a personal cloud folder",
    ],
    "benign": [
        "scheduled backup completed successfully",
        "approved software update installed on endpoints",
        "password reset verified by the service desk",
        "authenticated vulnerability scan finished with no findings",
        "firewall rule change approved by the change board",
        "security awareness training completed by the team",
        "asset inventory sync ran on schedule",
        "MFA enrollment completed for a new employee",
        "routine log rotation removed old archives",
        "endpoint agent updated its signature database",
    ],
}

GENERIC_INDICATORS = {
    "phishing": [
        "an unusual email asks the recipient to click a link",
        "a message requests account verification",
        "the sender address looks different from the usual contact",
        "a user forwards a suspicious message to the help desk",
        "an email asks for a payment to a new bank account",
    ],
    "malware": [
        "a device is running slowly and files are missing",
        "an unknown program was installed without approval",
        "the computer restarts unexpectedly",
        "a user reports strange pop-ups",
        "an application tries to access protected folders",
    ],
    "ddos": [
        "the website is slow and sometimes unavailable",
        "many requests arrive from different locations",
        "the network link is congested",
        "users cannot reach the login page",
        "traffic volume is much higher than normal",
    ],
    "insider": [
        "an employee accessed data outside normal hours",
        "a USB device was connected to a workstation",
        "a user downloaded a large number of files",
        "a shared account was used by two people",
        "a departing employee copied documents",
    ],
    "benign": [
        "routine maintenance completed on schedule",
        "a software update was installed",
        "a user completed the required training",
        "a backup job finished successfully",
        "a support ticket was resolved",
    ],
}

PREFIXES = ["Alert:", "SOC ticket:", "Incident report:", "Telemetry:", "Case note:"]
CONTEXTS = [
    "detected on an endpoint",
    "reported by the service desk",
    "observed in the email gateway",
    "correlated with identity logs",
    "flagged during triage",
    "seen in the cloud audit trail",
]


def _generate(indicator_map, size, seed):
    rng = random.Random(seed)
    rows = []
    per_label = size // len(LABELS)
    remainder = size - per_label * len(LABELS)

    for label in LABELS:
        count = per_label + (1 if remainder > 0 else 0)
        remainder = max(0, remainder - 1)
        indicators = indicator_map[label]

        for _ in range(count):
            indicator = rng.choice(indicators)
            prefix = rng.choice(PREFIXES)
            context = rng.choice(CONTEXTS)
            text = f"{prefix} {indicator}; {context}."
            rows.append({"text": text, "label": label})

    rng.shuffle(rows)
    return rows


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def prepare(force=False, train_size=250, validation_size=80, generic_size=250):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    train_path = DATA_DIR / "train.jsonl"
    validation_path = DATA_DIR / "validation.jsonl"
    generic_path = DATA_DIR / "generic_train.jsonl"

    if train_path.exists() and validation_path.exists() and not force:
        print("Datasets already exist (use --force to regenerate).")
    else:
        train = _generate(DOMAIN_INDICATORS, train_size, seed=11)
        validation = _generate(DOMAIN_INDICATORS, validation_size, seed=29)
        generic = _generate(GENERIC_INDICATORS, generic_size, seed=47)

        _write_jsonl(train_path, train)
        _write_jsonl(validation_path, validation)
        _write_jsonl(generic_path, generic)
        print(f"Wrote {len(train)} train, {len(validation)} validation and {len(generic)} generic rows.")

    for path in (train_path, validation_path, generic_path):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        distribution = Counter(row["label"] for row in rows)
        print(f"{path.name}: {len(rows)} rows -> {dict(sorted(distribution.items()))}")

    return {
        "train": str(train_path),
        "validation": str(validation_path),
        "generic": str(generic_path),
    }


def load_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--train-size", type=int, default=250)
    parser.add_argument("--validation-size", type=int, default=80)
    parser.add_argument("--generic-size", type=int, default=250)
    args = parser.parse_args()
    prepare(args.force, args.train_size, args.validation_size, args.generic_size)


if __name__ == "__main__":
    main()
