FROM python:latest

ENV TZ=Asia/Shanghai
ENV PYTHONIOENCODING utf-8
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo 'Asia/Shanghai' >/etc/timezone+
#-----------------------------

RUN mkdir -p /opt/automation/fabcli
WORKDIR /opt/automation/fabcli

COPY requirements.txt  .
COPY requirements-dev.txt  .
RUN pip3 install --upgrade pip && \
    pip3 install  -r requirements.txt --proxy http://proxy.tsp.cn-north-1.aws.unicom.cloud.bmw:8080

COPY ./  /opt/automation/fabcli

RUN chmod +x ./kubectl
RUN cp -rf ./kubectl  /usr/local/bin
RUN cp -rf .kube  ~/

RUN pip3 install --editable .

ENTRYPOINT [ "fabcli" ]
CMD ["--help"]

