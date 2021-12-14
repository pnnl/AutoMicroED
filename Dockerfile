# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
FROM czentye/matplotlib-minimal

COPY . AutoMicroED
WORKDIR AutoMicroED

CMD ["python","run_all.py","docker_input_files/mrc_file.list","docker_input_files/args_file.txt"]

VOLUME ["/tmp"]

