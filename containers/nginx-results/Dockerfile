FROM nginx:1.17

RUN mkdir -p /scripts
COPY index.html run_nginx.sh /scripts/
COPY default.conf /etc/nginx/conf.d/
CMD ["/scripts/run_nginx.sh"]