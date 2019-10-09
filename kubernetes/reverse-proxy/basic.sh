#!/bin/bash
set -eux

# basic setup of the reverse proxy based on
# https://kubernetes.github.io/ingress-nginx/deploy/
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/mandatory.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud-generic.yaml

# install certmanager based on
# http://docs.cert-manager.io/en/latest/getting-started/install/kubernetes.html

kubectl create namespace cert-manager
kubectl label namespace kube-system certmanager.k8s.io/disable-validation="true"
kubectl create clusterrolebinding cluster-admin-binding \
  --clusterrole=cluster-admin \
  --user=$(gcloud config get-value core/account)
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v0.10.1/cert-manager.yaml

