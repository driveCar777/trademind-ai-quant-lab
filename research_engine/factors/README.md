# Factor definitions

Locked candidate universe for Factor Discovery V0.1.

- `space.py` builds the search space. Changing it is a new version.
- `compute.py` is causal: `feature[t]` uses `CausalView` through `t`.
- Worker does not invent candidates.
