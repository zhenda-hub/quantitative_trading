# quantitative_trading

## pip-tools

```cmd
.venv\Scripts\activate
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



```bash
pip install pip-tools

pip-compile requirements.in

# 会删除多余包, 包严格一致
pip-sync requirements.txt
pip-compile --upgrade


```

## pipdeptree

```bash
pip install pipdeptree
pipdeptree
```



## st
```bash
streamlit run your_app.py

```
