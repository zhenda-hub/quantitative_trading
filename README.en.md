# quantitative_trading

## pip-tools

```bash
pip install pip-tools

pip-compile requirements.in

# 会删除多余包, 包严格一致
pip-sync requirements.txt
pip-compile --upgrade


```



```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.in .
RUN pip install pip-tools \
    && pip-compile requirements.in \
    && pip-sync requirements.txt

COPY . .

CMD ["python", "main.py"]

```

## pipdeptree

```bash
pip install pipdeptree
pipdeptree
```

