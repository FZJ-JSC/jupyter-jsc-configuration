c = get_config()
c.NotebookApp.ip = "0.0.0.0"
c.NotebookApp.notebook_dir = "_home_"
c.NotebookApp.default_url = "/lab/workspaces/_servername_"
c.ContentsManager.allow_hidden = False
c.NotebookApp.port = _port_
c.NotebookApp.terminado_settings = {"shell_command": ["/bin/bash"]}
c.SingleUserNotebookApp.hub_api_url = "http://_remotenode_:_remoteport_/hub/api"
c.SingleUserNotebookApp.hub_activity_url = (
    "http://_remotenode_:_remoteport_/hub/api/users/_username_/activity"
)
