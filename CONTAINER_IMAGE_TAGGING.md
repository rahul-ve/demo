## Container image versions with tags

### lower env

- using Semantic version

- tags:
    - sem-ver+suffix    - vX.Y.Z-abc,  vX.Y.Z-alpha1, vX.Y.Z-beta2 ...
    - branch name (commit hash is common but creates a lot of noise)
    - strict sem-ver
        - full -  vX.Y.Z
        - major - vX
        - minor  (optional)  - vX.Y
    - latest    OR dev-latest


### higher env

- promote when all tested and ok

- tags
    - strict sem-ver
        - full -  vX.Y.Z
        - major - vX
        - minor (optional)  - vX.Y
    - latest   OR prod-latest
