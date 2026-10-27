# Domain services

This directory contains mastery, gap-detection, adaptive-policy and recommendation behavior.

`learning_engine.py` currently provides the pure `LearningEngine.evaluate()` entry point. It has no database, web framework, network, or live AI dependency.

`question_classifier.py` provides deterministic Bloom BT1–BT6 and independent
Easy/Medium/Hard suggestions through `QuestionClassifier.classify()`. The
result includes a confidence and reason for the Bloom suggestion.
