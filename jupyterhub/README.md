# Update JupyterHub installation

Update values.yaml to your liking.
Run these commands as user ubuntu:

Jupyter-Test Cluster:
```
k-jupyter-test
helm upgrade --cleanup-on-fail   --install jhub jupyterhub/jupyterhub   --namespace jupyter-test   --version=0.11.1   --values values.yaml
```

Jupyter-JSC Live Cluster:
```
k-jupyter-jsc
helm upgrade --cleanup-on-fail   --install jhub jupyterhub/jupyterhub   --namespace jupyterjsc   --version=0.11.1   --values values.yaml
```
