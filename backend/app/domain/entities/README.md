# Domain entities

This directory contains provider-independent learning entities such as concepts, assessment items, assessment sessions, attempts, mastery states and recommendations.

The current first slice is implemented in `learning.py`. Entities validate their own invariants so invalid evidence cannot enter the learning policy silently.
