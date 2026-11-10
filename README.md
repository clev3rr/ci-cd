# Лабораторна робота №4 Вебзастосунок у Kubernetes

Односторінковий клієнт керує записами через REST API FastAPI. Сервер зберігає записи в PostgreSQL через SQLAlchemy. Окремий застосунок `migrate.py` застосовує міграції Alembic і завершується. У Kubernetes його запускає Job. PostgreSQL працює як StatefulSet і зберігає дані на постійному томі.

Ingress спрямовує `/` до клієнта на Nginx, а `/api` до FastAPI. Клієнт звертається до API за відносним шляхом `/api/items`. У каталозі `k8s/lab4` міститься Helm Chart, а `values.kind.yaml` задає локальні образи для kind.

## Розгортання у kind

Виконуйте команди PowerShell із кореня репозиторію. Потрібні Docker Desktop у режимі Linux containers, kind, kubectl і Helm 4.

Для нового стенда створіть кластер та встановіть Traefik.

```powershell
kind create cluster --name lab4 --image kindest/node:v1.37.0 --wait 3m
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik --version 42.3.2 --kube-context kind-lab4 -n traefik --create-namespace --set service.spec.type=ClusterIP --set ingressClass.name=traefik --set providers.kubernetesIngress.enabled=true --wait --timeout 5m
```

Зберіть образи та завантажте їх у кластер.

```powershell
docker build -t lab4-api:kind .
docker build -t lab4-frontend:local .\frontend
docker build -f Dockerfile.migrations -t lab4-migrations:local .
kind load docker-image lab4-api:kind lab4-frontend:local lab4-migrations:local --name lab4
```

Для першого встановлення створіть простір імен і Secret. PostgreSQL отримує пароль із ключа `postgres-password`. FastAPI і мігратор використовують рядок підключення з ключа `database-url`.

```powershell
kubectl --context kind-lab4 create namespace lab4
$dbPassword = Read-Host 'PostgreSQL password for this lab'
$encodedPassword = [Uri]::EscapeDataString($dbPassword)
$databaseUrl = "postgresql+psycopg://lab4:${encodedPassword}@lab4-postgres:5432/lab4"
kubectl --context kind-lab4 -n lab4 create secret generic lab4-db --from-literal="postgres-password=$dbPassword" --from-literal="database-url=$databaseUrl"
```

Встановіть або оновіть реліз і перевірте ресурси.

```powershell
helm upgrade --install lab4 .\k8s\lab4 --kube-context kind-lab4 -n lab4 -f .\k8s\lab4\values.kind.yaml --wait --wait-for-jobs --timeout 6m
kubectl --context kind-lab4 -n lab4 get pods,svc,job,pvc,ingress
```

У окремому вікні запустіть перенаправлення порту до Traefik та залиште його активним.

```powershell
kubectl --context kind-lab4 -n traefik port-forward svc/traefik 8083:80
```

Інтерфейс доступний за адресою [lab4.localhost:8083](http://lab4.localhost:8083/). Запит до API можна перевірити з іншого вікна.

```powershell
curl.exe -i --resolve lab4.localhost:8083:127.0.0.1 http://lab4.localhost:8083/api/items
```

## Перевірка та пакування Helm Chart

```powershell
helm lint .\k8s\lab4 --strict
helm template lab4 .\k8s\lab4 -n lab4 -f .\k8s\lab4\values.kind.yaml
New-Item -ItemType Directory -Force -Path .\dist
helm package .\k8s\lab4 --destination .\dist
```

Архів `dist/lab4-0.1.0.tgz` можна передати в `helm upgrade --install` замість каталогу `k8s/lab4`. Для розгортання з опублікованих образів використовуйте основний `values.yaml` без локальних перевизначень із `values.kind.yaml`.

## GitHub Actions

CI піднімає окрему базу PostgreSQL, застосовує міграції та запускає `pytest`. Після тестів CI збирає образи сервера, клієнта й мігратора. У гілці `main` CI публікує образи в Docker Hub, використовуючи GitHub Secrets `DOCKER_USERNAME` та `DOCKER_PASSWORD`. Для гілок `feature/*` і `bugfix/*` CI зберігає образи як артефакти.

Задача `package-helm` перевіряє чарт і завантажує архів як артефакт `helm-chart`. Версії чарта та застосунку задано в `k8s/lab4/Chart.yaml`.
