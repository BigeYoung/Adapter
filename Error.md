```sh
$ minikube stop
$ minikube delete
$ minikube start #...
$ cd middleware-k8s/kubernetes/helm/
$ helmfile apply
```
等待一段时间后...
```sh
$ kubectl get all
NAME                                                                  READY   STATUS    RESTARTS   AGE
pod/consul-consul-connect-injector-webhook-deployment-c775dfd58qmz2   1/1     Running   0          22m
pod/consul-consul-hxrp8                                               1/1     Running   0          22m
pod/consul-consul-server-0                                            1/1     Running   0          22m
pod/consul-consul-sync-catalog-f7fbb84b5-mfq6g                        1/1     Running   10         22m

NAME                                         TYPE           CLUSTER-IP     EXTERNAL-IP             PORT(S)                                                                   AGE
service/consul                               ExternalName   <none>         consul.service.consul   <none>                                                                    29s
service/consul-consul-connect-injector-svc   ClusterIP      10.100.58.30   <none>                  443/TCP                                                                   22m
service/consul-consul-dns                    ClusterIP      10.103.72.54   <none>                  53/TCP,53/UDP                                                             22m
service/consul-consul-server                 ClusterIP      None           <none>                  8500/TCP,8301/TCP,8301/UDP,8302/TCP,8302/UDP,8300/TCP,8600/TCP,8600/UDP   22m
service/consul-consul-ui                     NodePort       10.105.4.105   <none>                  80:32500/TCP                                                              22m
service/kubernetes                           ClusterIP      10.96.0.1      <none>                  443/TCP                                                                   85m

NAME                           DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
daemonset.apps/consul-consul   1         1         1       1            1           <none>          22m

NAME                                                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/consul-consul-connect-injector-webhook-deployment   1/1     1            1           22m
deployment.apps/consul-consul-sync-catalog                          1/1     1            1           22m

NAME                                                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/consul-consul-connect-injector-webhook-deployment-c775dfd56   1         1         1       22m
replicaset.apps/consul-consul-sync-catalog-f7fbb84b5                          1         1         1       22m

NAME                                    READY   AGE
statefulset.apps/consul-consul-server   1/1     22m
```

client端的配置参照了[Consul Clients Outside Kubernetes](https://www.consul.io/docs/k8s/installation/deployment-configurations/clients-outside-kubernetes)这个教程，绑定了bridge网络，关联`.kube`和`.minikube`两个文件夹到主机，从记录来看加入k8s应该是成功了（因为如果不关联这两个文件夹会报错说找不到k8s）。

```sh
$ docker-compose up --build
consul_1  | ==> Starting Consul agent...
consul_1  |            Version: 'v1.8.0'
consul_1  |            Node ID: 'e26f39cb-3f85-c032-2b73-4599cb14678e'
consul_1  |          Node name: 'e774ab845105'
consul_1  |         Datacenter: 'dc1' (Segment: '')
consul_1  |             Server: false (Bootstrap: false)
consul_1  |        Client Addr: [127.0.0.1] (HTTP: 8500, HTTPS: -1, gRPC: -1, DNS: 8600)
consul_1  |       Cluster Addr: 172.17.0.2 (LAN: 8301, WAN: 8302)
consul_1  |            Encrypt: Gossip: false, TLS-Outgoing: false, TLS-Incoming: false, Auto-Encrypt-TLS: false
consul_1  | 
consul_1  | ==> Log data will now stream in as it occurs:
consul_1  | 
consul_1  |     2020-07-05T16:04:25.538Z [INFO]  agent.client.serf.lan: serf: EventMemberJoin: e774ab845105 172.17.0.2
consul_1  |     2020-07-05T16:04:25.538Z [INFO]  agent: Started DNS server: address=127.0.0.1:8600 network=udp
consul_1  |     2020-07-05T16:04:25.538Z [INFO]  agent: Started DNS server: address=127.0.0.1:8600 network=tcp
consul_1  |     2020-07-05T16:04:25.540Z [INFO]  agent: Started HTTP server: address=127.0.0.1:8500 network=tcp
consul_1  |     2020-07-05T16:04:25.541Z [INFO]  agent: started state syncer
consul_1  | ==> Consul agent running!
consul_1  |     2020-07-05T16:04:25.541Z [INFO]  agent: Retry join is supported for the following discovery methods: cluster=LAN discovery_methods="aliyun aws azure digitalocean gce k8s linode mdns os packet scaleway softlayer tencentcloud triton vsphere"
consul_1  |     2020-07-05T16:04:25.542Z [INFO]  agent: Joining cluster...: cluster=LAN
consul_1  |     2020-07-05T16:04:25.542Z [WARN]  agent.client.manager: No servers available
consul_1  |     2020-07-05T16:04:25.542Z [ERROR] agent.anti_entropy: failed to sync remote state: error="No known Consul servers"
consul_1  |     2020-07-05T16:04:25.567Z [INFO]  agent: Discovered servers: cluster=LAN cluster=LAN servers=172.18.0.7
consul_1  |     2020-07-05T16:04:25.567Z [INFO]  agent: (LAN) joining: lan_addresses=[172.18.0.7]
```

但是仍然会报"No servers available"

另外，当使用`ingress`时出错（之前出的错一直没解决，来回`disable`和`delete`了很多次都不行）
```sh
$ minikube addons enable ingress
🌟  The 'ingress' addon is enabled
$ kubectl apply -f ingress.yaml
Error from server (InternalError): error when creating "ingress.yaml": Internal error occurred: failed calling webhook "validate.nginx.ingress.kubernetes.io": Post https://ingress-nginx-controller-admission.kube-system.svc:443/extensions/v1beta1/ingresses?timeout=30s: dial tcp 10.110.85.183:443: connect: connection refused
```
