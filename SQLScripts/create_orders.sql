DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
  orderID bigint unsigned NOT NULL AUTO_INCREMENT,
  orderDateTime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  part int NOT NULL,
  customer int NOT NULL,
  quantity int NOT NULL,
  PRIMARY KEY (orderID)
)

DROP TABLE IF EXISTS shipments;

CREATE TABLE shipments (
  transactionNumber bigint NOT NULL AUTO_INCREMENT,
  shipper VARCHAR(50) NOT NULL,
  orderID bigint unsigned NOT NULL,
  address int NOT NULL,
  PRIMARY KEY(transactionNumber),
  FOREIGN KEY (orderID) REFERENCES orders(orderID) ON DELETE CASCADE
)