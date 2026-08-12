# Linting

## Install pre-commit in repo
```Bash
pip install pre-commit
pre-commit install
```

## Vscode setup
Install: https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter

Add these to your .vscode/settings.json
```Json
  "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "python.linting.flake8Enabled": true,
    "python.linting.enabled": true
```

## Avoid pre commit running
Add `--no-verify` 
e.g. 
```Bash
  git commit -m "Test" --no-verify
```