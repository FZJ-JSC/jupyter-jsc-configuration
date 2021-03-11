c = get_config()
c.NotebookApp.ip = "0.0.0.0"
c.NotebookApp.notebook_dir = "/home/jovyan"
c.NotebookApp.default_url = "/lab/workspaces/_servername_"
c.ContentsManager.allow_hidden = False
c.NotebookApp.port = _port_
c.NotebookApp.terminado_settings = {"shell_command": ["/bin/bash"]}
