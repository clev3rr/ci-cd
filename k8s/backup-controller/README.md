# DatabaseBackup controller

Контролер лабораторної роботи № 5 створює та підтримує `CronJob` для резервного копіювання PostgreSQL.

## Запуск у kind

```powershell
docker build -t lab4-backup-controller:local .\k8s\backup-controller\controller
kind load docker-image lab4-backup-controller:local --name lab4

kubectl --context kind-lab4 apply -f .\k8s\backup-controller\manifests\databasebackup-crd.yaml
kubectl --context kind-lab4 create namespace demo
kubectl --context kind-lab4 -n demo apply -f .\k8s\backup-controller\manifests\postgres-backups-pvc.yaml
kubectl --context kind-lab4 -n demo apply -f .\k8s\backup-controller\manifests\controller.yaml
kubectl --context kind-lab4 -n demo apply -f .\k8s\backup-controller\manifests\databasebackup.yaml
```

Перед застосуванням маніфестів потрібно створити Secret `users-db-connection` з ключами `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` та `PGPASSWORD`.

Контролер працює в namespace `demo`, читає ресурси `DatabaseBackup` і синхронізує однойменний `CronJob`. Контейнер `pg_dump` використовує Secret через `envFrom`, а архів записується на PVC `postgres-backups` у форматі custom.

## Перевірка

```powershell
kubectl --context kind-lab4 -n demo get databasebackup,cronjob,job,pvc,pods
kubectl --context kind-lab4 -n demo logs deployment/databasebackup-controller
kubectl --context kind-lab4 -n demo create job backup-manual --from=cronjob/users-db-backup
kubectl --context kind-lab4 -n demo logs job/backup-manual
```

RBAC контролера обмежено namespace `demo`: він має доступ до `databasebackups` і `cronjobs`, але не має доступу до Secret та impersonation.
