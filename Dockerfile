FROM mirror.gcr.io/python:3-slim

# 作業ディレクトリを作成
WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

# GitHubの「app」フォルダの中身を、Docker内の「/app」に丸ごとコピー
COPY app/ .

# Flaskが起動するポートをRenderに合わせる設定
ENV FLASK_APP=app.py
ENV PORT=10000

# 起動コマンド（ポートを10000番に指定）
CMD ["flask", "run", "--host=0.0.0.0", "--port=10000"]
