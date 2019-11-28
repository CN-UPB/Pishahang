
kubectl run my-app --image=pgscramble/gst-cn-transcoder:latest --port=9000 --env="runtime=nvidia"


kubectl expose deployment my-app --type=LoadBalancer --port=8080 --target-port=80

kubectl get pods


----
kubectl delete deployment my-app
kubectl delete svc my-app
kubectl run my-app --image=transcoder-cn:latest --port=80 --env="runtime=nvidia"
kubectl expose deployment my-app --type=LoadBalancer --port=8080 --target-port=80
kubectl get svc

---

kubectl delete deployment my-app
kubectl delete svc my-app
kubectl run my-app --image=pgscramble/transcoder-cn:beta2 --port=80 --env="runtime=nvidia"
kubectl expose deployment my-app --type=LoadBalancer --port=8080 --target-port=80
kubectl get svc
kubectl get pods
