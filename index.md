---
layout: home
title: Instagram Fake Account Detector
---

The Instagram Fake Account Detector is a Streamlit application for reviewing
public profile and post signals. It combines supervised model predictions with
transparent evidence such as account metadata, image signals, content patterns,
network indicators, and public source checks.

## Run the application

The interactive Python application must run on a Python-capable host. From the
project directory:

```bash
./.venv/bin/python -m streamlit run app.py
```

See the [project README](https://github.com/Root-Tester/instgram_fake_account_detector/blob/main/README.md)
for setup, SDK usage, model notes, and limitations.

Results are heuristic evidence, not proof of identity or fraud. Do not use the
tool to bypass access controls or make decisions without human review.
