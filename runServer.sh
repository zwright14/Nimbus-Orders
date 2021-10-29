docker run -p 5000:5000 \
-e DBHOST=$DBHOST \
-e DBUSER=$DBUSER \
-e DBPASSWORD=$DBPASSWORD \
orders-app
