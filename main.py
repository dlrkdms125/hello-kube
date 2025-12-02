from kubernetes import client, config, watch
import time
import sys
import os
import requests

def load_kube_config():
    # 깃헙 액션 OIDC 토큰 사용
    oidc_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOEKN")
    k8s_api_server = os.environ.get("K8S_API_SERVER")
    k8s_ca_cert = "/tmp/ca.crt"

    # CA 업로드(깃헙 액션 시크릿으로 넣기)
    with open(k8s_ca_cert, "w") as f:
        f.write(os.environ.get("K8S_CA_CERT"))

    configuration = client.Configuration()
    configuration.host = k8s_api_server
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = k8s_ca_cert
    configuration.api_key = {"authorization": "Bearer "+oidc_token}

    client.Configuration.set_default(configuration)

def main():
    load_kube_config()
    v1 = client.CoreV1Api()

    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": "hello"},
        "spec": {
            "containers": [{
                "name": "hello",
                "image": "busybox",
                "command": ["sh", "-c", "echo Hello world && sleep 1"]
            }],
            "restartPolicy": "Never"
        }
    }

    print("파드 생성중")
    v1.create_namespaced_pod(namespace="default", body=pod_manifest)

    # Pod 상태 모니터
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, namespace="default"):
        pod = event["object"]
        if pod.metadata.name == "hello":
            print(f"Pod status: {pod.status.phase}")
            if pod.status.phase in ["Succeeded", "Failed"]:
                break

    # 로그 출력
    print("Pod Logs:")
    logs = v1.read_namespaced_pod_log("hello", "default")
    print(logs)

    # 삭제
    print("Deleting Pod…")
    v1.delete_namespaced_pod("hello", "default")

if __name__ == "__main__":
    main()

