FROM nginx:1.17

RUN set -e ;\
    apt-get update ;\
    apt-get install -y --no-install-recommends python3 cron;\
    apt-get clean

RUN mkdir -p /scripts
COPY index.html run_nginx.sh clean_results.py /scripts/
COPY default.conf /etc/nginx/conf.d/

COPY crontab /etc/cron.d/clean_results
RUN chmod 0644 /etc/cron.d/clean_results
RUN service cron start

CMD ["/scripts/run_nginx.sh"]