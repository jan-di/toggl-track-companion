import web_prod

# pylint: disable=invalid-name

worker_exit = web_prod.worker_exit
on_exit = web_prod.on_exit

bind = "0.0.0.0:5000"
accesslog = "-"
