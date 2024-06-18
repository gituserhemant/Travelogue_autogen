FROM python:3.8-slim

WORKDIR /app

COPY . /app

RUN pip cache purge

RUN pip install -r requirements.txt

RUN pip install -U langchain-community

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]