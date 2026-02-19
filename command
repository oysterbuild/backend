uvicorn main:app --reload

alembic init alembic

alembic revision --autogenerate -m "added relations"
alembic upgrade head

update the alembic.ini i.e update the sqlalchemy.url and also change env.py to Base.metadata





https://oysterbuild.pm, www.oysterbuild.pm, https://www.oysterbuild.pm {
    reverse_proxy app:8000
    log {
        output file /data/access.log
    }
}