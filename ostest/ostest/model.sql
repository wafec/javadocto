CREATE TABLE endpoint_bkp (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  endpoint_id VARCHAR(64) NOT NULL,
  url TEXT,
  FOREIGN KEY (endpoint_id) REFERENCES endpoint(id)
);