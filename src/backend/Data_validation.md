Follow these steps to run the pipeline:
*note before you start, you will need to have 3 terminal windows open
1. Open docker
2. cd into scripts
3. run chmod +x setup_dev.sh
4. run ./setup_dev.sh
5. Run the following bunch of commands (just copy paste the entire thing into your terminal)

openssl genrsa -out mosquitto/config/certs/ca.key 2048
openssl req -new -x509 -days 365 \
  -key mosquitto/config/certs/ca.key \
  -out mosquitto/config/certs/ca.crt \
  -subj "/CN=SCEMAS-CA"
openssl genrsa -out mosquitto/config/certs/server.key 2048
openssl req -new -key mosquitto/config/certs/server.key \
  -out mosquitto/config/certs/server.csr \
  -subj "/CN=localhost"
openssl x509 -req \
  -in mosquitto/config/certs/server.csr \
  -CA mosquitto/config/certs/ca.crt \
  -CAkey mosquitto/config/certs/ca.key \
  -CAcreateserial \
  -out mosquitto/config/certs/server.crt \
  -days 365


6. Run: docker compose up mosquitto
7. open a new terminal window (we'll say this is terminal 2)
8. cd into backend
9. Run python main.py
10. open a third terminal window (we'll say this is terminal 3)
11. cd into src
12. run simulator.py (python simulator.py)
13. Watch data be sent (check supabase. The tables sensor_readings and validation_events should be continuosly updating)