#!/bin/sh

dagster-daemon run &
dagit -h "0.0.0.0" -p "3000" -w "/opt/dagster/app/workspace.yaml"
