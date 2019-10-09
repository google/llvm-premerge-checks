#!/bin/bash
set -eux

# basic setup of the reverse proxy based on
# https://kubernetes.github.io/ingress-nginx/deploy/
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/mandatory.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud-generic.yaml

# install jetstack based on
# https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nginx-ingress-with-cert-manager-on-digitalocean-kubernetes
kubectl apply -f https://raw.githubusercontent.com/jetstack/cert-manager/release-0.8/deploy/manifests/00-crds.yaml
kubectl label namespace kube-system certmanager.k8s.io/disable-validation="true"
helm repo add jetstack https://charts.jetstack.io
helm install --name cert-manager --namespace kube-system jetstack/cert-manager --version v0.8.0
