import logging
import os
import time
from datetime import datetime, timezone

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException


GROUP = "backup.example.com"
VERSION = "v1alpha1"
PLURAL = "databasebackups"
POSTGRES_IMAGE = os.getenv("POSTGRES_IMAGE", "postgres:16")
RECONCILE_INTERVAL = int(os.getenv("RECONCILE_INTERVAL", "15"))
WATCH_NAMESPACE = os.getenv("WATCH_NAMESPACE", "demo")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("database-backup-controller")


def owner_reference(resource):
    metadata = resource["metadata"]
    return [{
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": "DatabaseBackup",
        "name": metadata["name"],
        "uid": metadata["uid"],
        "controller": True,
        "blockOwnerDeletion": True,
    }]


def cronjob_spec(resource):
    spec = resource.get("spec", {})
    secret_name = spec["connectionSecretName"]
    pvc_name = spec["backupPVCName"]
    schedule = spec["schedule"]
    time_zone = spec.get("timeZone", "Etc/UTC")
    return {
        "schedule": schedule,
        "timeZone": time_zone,
        "concurrencyPolicy": "Forbid",
        "successfulJobsHistoryLimit": 3,
        "failedJobsHistoryLimit": 3,
        "jobTemplate": {
            "spec": {
                "backoffLimit": 1,
                "template": {
                    "spec": {
                        "restartPolicy": "OnFailure",
                        "containers": [{
                            "name": "pg-dump",
                            "image": POSTGRES_IMAGE,
                            "command": ["/bin/sh", "-ec"],
                            "args": [
                                "stamp=$(date -u +%Y%m%dT%H%M%SZ); "
                                "tmp=/backups/.${stamp}.dump.tmp; "
                                "out=/backups/${stamp}.dump; "
                                "pg_dump -Fc -f \"$tmp\"; "
                                "mv \"$tmp\" \"$out\"; "
                                "echo \"backup created: $out\""
                            ],
                            "envFrom": [{"secretRef": {"name": secret_name}}],
                            "volumeMounts": [{"name": "backups", "mountPath": "/backups"}],
                        }],
                        "volumes": [{
                            "name": "backups",
                            "persistentVolumeClaim": {"claimName": pvc_name},
                        }],
                    }
                },
            }
        },
    }


def reconcile(resource, batch_api):
    metadata = resource["metadata"]
    namespace = metadata["namespace"]
    name = metadata["name"]
    resource_spec = resource.get("spec", {})
    secret_name = resource_spec["connectionSecretName"]
    pvc_name = resource_spec["backupPVCName"]
    desired = cronjob_spec(resource)
    body = client.V1CronJob(
        api_version="batch/v1",
        kind="CronJob",
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            owner_references=owner_reference(resource),
        ),
        spec=client.V1CronJobSpec(
            schedule=desired["schedule"],
            time_zone=desired["timeZone"],
            concurrency_policy=desired["concurrencyPolicy"],
            successful_jobs_history_limit=desired["successfulJobsHistoryLimit"],
            failed_jobs_history_limit=desired["failedJobsHistoryLimit"],
            job_template=client.V1JobTemplateSpec(
                spec=client.V1JobSpec(
                    backoff_limit=1,
                    template=client.V1PodTemplateSpec(
                        spec=client.V1PodSpec(
                            restart_policy="OnFailure",
                            containers=[client.V1Container(
                                name="pg-dump",
                                image=POSTGRES_IMAGE,
                                command=["/bin/sh", "-ec"],
                                args=desired["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]["args"],
                                env_from=[client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=secret_name))],
                                volume_mounts=[client.V1VolumeMount(name="backups", mount_path="/backups")],
                            )],
                            volumes=[client.V1Volume(name="backups", persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name))],
                        )
                    ),
                )
            ),
        ),
    )
    try:
        existing = batch_api.read_namespaced_cron_job(name, namespace)
        existing.spec = body.spec
        existing.metadata.owner_references = body.metadata.owner_references
        batch_api.replace_namespaced_cron_job(name, namespace, existing)
        log.info("reconciled CronJob %s/%s", namespace, name)
    except ApiException as exc:
        if exc.status == 404:
            batch_api.create_namespaced_cron_job(namespace, body)
            log.info("created CronJob %s/%s", namespace, name)
        else:
            raise


def list_resources(api):
    return api.list_namespaced_custom_object(
        GROUP, VERSION, WATCH_NAMESPACE, PLURAL
    ).get("items", [])


def main():
    config.load_incluster_config()
    custom_api = client.CustomObjectsApi()
    batch_api = client.BatchV1Api()
    last_resource_version = None

    while True:
        try:
            resources = list_resources(custom_api)
            for resource in resources:
                reconcile(resource, batch_api)
                last_resource_version = resource.get("metadata", {}).get("resourceVersion", last_resource_version)
            log.info("reconciliation complete, resources=%d resourceVersion=%s", len(resources), last_resource_version)
            time.sleep(RECONCILE_INTERVAL)
        except ApiException as exc:
            log.error("Kubernetes API error: %s", exc)
            time.sleep(5)
        except Exception:
            log.exception("unexpected controller error")
            time.sleep(5)


if __name__ == "__main__":
    main()
