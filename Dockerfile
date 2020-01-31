FROM python:3.7
ADD ./code /code
VOLUME [ "/code" ]
WORKDIR /code
RUN pip install -r requirements.txt
CMD python main.py
