# xApp-to-xApp Communication in O-RAN through RMR (RTS based)

<img width="511" height="635" alt="xAPP-xAPP-RMR - With RTS" src="https://github.com/user-attachments/assets/2109a936-7dea-43bf-9a90-4907ddf5e7a4" />


This repository demonstrates **xApp-to-xApp communication using Return-To-Sender (RTS)** with the O-RAN SC RMR (RIC Message Router).

- `hello` sends `PING` messages (`mtype=10000`)
- `hello-b` receives them and sends the response back using **`rmr_rts_msg()`**
- the reply is returned to the **originating xApp automatically**, based on the sender identity embedded in the received RMR message

The demo runs inside a Kubernetes-based Near-RT RIC environment using two xApps deployed in the `ricxapp` namespace.

## What makes this repo different

This repository is intentionally different from the **type-based routing** version.

### Type-based routing
- Request route is explicit: `mtype=10000 -> hello-b`
- Reply route is also explicit: `mtype=10001 -> hello`
- Bidirectional flow depends on a predefined static return route

### RTS-based 
- Request route is explicit: `mtype=10000 -> hello-b`
- Reply route is **not explicitly mapped back to `hello`**
- `hello-b` uses **`rmr_rts_msg()`** to return the response to the original sender
- Reply delivery depends on the sender identity carried in the incoming RMR message, exposed in this demo as:

```text
src=hello.ricxapp:4560
```

This means the return path is driven by the **message origin**, not by a separate static reply route.

## Routing Model Used

This demo uses **RMR Return-To-Sender (RTS)** for the response path.

To make RTS work reliably in Kubernetes, each xApp advertises a stable and routable source identity using `RMR_SRC_ID`.

For this demo:

- request path: `mtype=10000` → routed to `hello-b`
- response path: `hello-b` → returned automatically to the originating sender using `rmr_rts_msg()`

This demonstrates a sender-aware request-response pattern using RMR.

## Repository Structure

- `app/hello.py`: sender xApp
- `app/hello_b.py`: RTS responder xApp
- `app/common.py`: shared RMR helpers
- `k8s/*.yaml`: Kubernetes manifests for `ricxapp`
- `Dockerfile`: container image

## Prerequisites

Before running this demo, confirm:

1. Docker works
2. `kubectl` points to your `kind-ric` cluster
3. the `ricxapp` namespace exists
4. Kubernetes can see locally loaded images
5. the Near-RT RIC environment is already running

## Run Guide

### 1) Build the image

```bash
docker build -t hello-xapp-rmr:latest .
```

### 2) Load the image into kind

```bash
kind load docker-image hello-xapp-rmr:latest --name ric
```

### 3) Confirm your RIC namespace exists

```bash
kubectl get ns | grep ricxapp
```

### 4) Apply the route table and services

```bash
kubectl apply -f k8s/hello-routes-configmap.yaml
kubectl apply -f k8s/hello-service.yaml
kubectl apply -f k8s/hello-b-service.yaml
```

### 5) Deploy the two xApps

```bash
kubectl apply -f k8s/hello-deployment.yaml
kubectl apply -f k8s/hello-b-deployment.yaml
```

### 6) Watch the pods

```bash
kubectl get pods -n ricxapp -w
```

Wait until both are `Running`.

### 7) Check logs

In terminal 1:

```bash
kubectl logs -n ricxapp deploy/hello -f
```

In terminal 2:

```bash
kubectl logs -n ricxapp deploy/hello-b -f
```

## Sample Output

### Sender xApp (`hello`)

```text
PING sent: mtype=10000 seq=1 state=0 tp_state=0
PONG received: mtype=10001 payload={"type": "pong", "got": "..."} state=0 tp_state=0

PING sent: mtype=10000 seq=2 state=0 tp_state=0
PONG received: mtype=10001 payload={"type": "pong", "got": "..."} state=0 tp_state=0
```

### Responder xApp (`hello-b`)

```text
PING received: mtype=10000 payload={"type": "ping", "seq": 1} src=hello.ricxapp:4560 state=0 tp_state=0
PONG RTS sent: mtype=10001 state=0 tp_state=0

PING received: mtype=10000 payload={"type": "ping", "seq": 2} src=hello.ricxapp:4560 state=0 tp_state=0
PONG RTS sent: mtype=10001 state=0 tp_state=0
```

## Why RTS matters

RTS is useful when a responder needs to return a message to the **originating sender** without relying on a separately defined return route.

In this demo, the responder does not need an explicit `mtype=10001 -> hello` reply mapping to identify the sender. Instead, it uses the sender identity already embedded in the received RMR message.

This makes the request-response pattern more sender-aware and closer to dynamic reply behavior in distributed RMR-based systems.

## Notes

- This demo uses a static request route table via `RMR_SEED_RT`
- `RMR_RTG_SVC=-1` disables Route Manager for standalone testing
- the RTS response path depends on `RMR_SRC_ID` being stable and routable
- the Python implementation uses the official `ricxappframe.rmr` bindings
- this demo is intended for a **single replica per xApp**
- if you later scale replicas, a StatefulSet + stable per-pod identity is a better fit for strict instance-level RTS behavior

## References

RMR (RIC Message Router) User Guide — O-RAN Software Community:  
https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-lib-rmr/en/latest/user-guide.html
