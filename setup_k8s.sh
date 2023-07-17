# Setups kubernetes with env variables.

echo GCP_PROJECT=$GCP_PROJECT
echo GCP_ZONE=$GCP_ZONE
echo GCP_CLUSTER=$GCP_CLUSTER
gcloud config set project ${GCP_PROJECT}
gcloud config set compute/zone ${GCP_ZONE}
# setup docker for pushing containers
gcloud auth configure-docker
gcloud container clusters get-credentials $GCP_CLUSTER