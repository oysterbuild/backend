uvicorn main:app --reload

alembic init alembic

alembic revision --autogenerate -m "added relations"
alembic upgrade head

update the alembic.ini i.e update the sqlalchemy.url and also change env.py to Base.metadata