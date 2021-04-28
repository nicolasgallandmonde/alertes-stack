FROM nicogalland/python-base-data-eng-light:latest

RUN pip install \
    slackclient \
    dagster \
    dagster-graphql \
    dagit \
    dagster-postgres \
    dagstermill \
    GitPython \
    streamlit

ENV DAGSTER_HOME=/opt/dagster/dagster_home

RUN mkdir -p $DAGSTER_HOME

COPY dagster.yaml $DAGSTER_HOME

COPY entrypoint.sh /opt/dagster/
RUN chmod +x /opt/dagster/entrypoint.sh

WORKDIR $DAGSTER_HOME

ENTRYPOINT ["/opt/dagster/entrypoint.sh"]
