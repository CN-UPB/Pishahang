###################################################################################
# Requires external Postgres DB to be running, can be another container.          #
# Link the database container to this one changing the DATABASE_HOST respectively #
# At last build this container                                                    #
# On run please run tests with "python tests.py" as a container argument,         #
# and after run migrations on the database with "python manage.py db upgrade",    #
# only then run the container normally.                                           #
###################################################################################

FROM python:2.7
ADD requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y \
        python-psycopg2 \
        postgresql-client*

RUN pip install -r /tmp/requirements.txt

ADD . /code
WORKDIR /code

ENV POSTGRES_PASSWORD sonatatest
ENV POSTGRES_USER postgres
ENV POSTGRES_DB gatekeeper
ENV DATABASE_HOST postgres
ENV DATABASE_PORT 5432
ENV PORT 5900

EXPOSE 6000

# Run Server
CMD ["python", "manage.py", "runserver", "--host", "0.0.0.0"]
