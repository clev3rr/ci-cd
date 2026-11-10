FROM nginx:alpine

ENV API_UPSTREAM=lab4-api:8000

COPY index.html /usr/share/nginx/html/index.html
COPY default.conf.template /etc/nginx/templates/default.conf.template