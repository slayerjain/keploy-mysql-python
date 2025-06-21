## Instructions for Use

```
sudo docker compose down -v   # removes the named volume → clean slate
sudo docker compose up -d db  # first start ⇒ init scripts run

pip install -r requirements.txt

keploy record -c "python main.py"

```

Then do API calls to the running server, e.g. with Postman or curl.

```
 curl localhost:8000/run 
 ```