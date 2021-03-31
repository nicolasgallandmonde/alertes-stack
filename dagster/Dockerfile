FROM nicogalland/python-base-data-eng-light:latest

RUN pip install \
    dagster \
    dagster-graphql \
    dagit \
    dagster-postgres \
    dagstermill \
    GitPython \
    slackclient

ENV DAGSTER_HOME=/opt/dagster/dagster_home

RUN mkdir -p $DAGSTER_HOME

COPY dagster.yaml $DAGSTER_HOME

COPY entrypoint.sh /opt/dagster/
RUN chmod +x /opt/dagster/entrypoint.sh

WORKDIR $DAGSTER_HOME

RUN apt install openssh-server -y --fix-missing
# authorize SSH connection with root account
RUN sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config

ENTRYPOINT ["/opt/dagster/entrypoint.sh"]
