# FROM public.ecr.aws/serverless/extensions/lambda-insights:12 AS lambda-insights
FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/runtime/
COPY bootstrap bootstrap
RUN chmod 755 bootstrap

ENV LAMBDA_TASK_ROOT=/var/task
ENV VIRTUAL_ENV=/opt/venv

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
COPY scan.py ${LAMBDA_TASK_ROOT}
ADD pyimagesearch ${LAMBDA_TASK_ROOT}/pyimagesearch

RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

WORKDIR /var/task/
RUN chmod 755 ${LAMBDA_TASK_ROOT}/scan.py

CMD [ "/var/task/scan.lambda_handler" ]