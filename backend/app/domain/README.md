# Learning domain

This area holds provider-independent AdaptEd learning behavior.

It owns concepts, prerequisites, assessment sessions, attempts, mastery states, gap classification, adaptive item selection and recommendation rules. Domain behavior must be testable without a database, web server or live model call.

The first implementation is `services/learning_engine.py`. Its `LearningEngine.evaluate()` entry point calculates a mastery state and next action from attempt evidence, while `entities/learning.py` contains the immutable domain values exchanged by the service.
