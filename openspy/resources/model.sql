CREATE TABLE endpoint_backup (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  endpoint_id VARCHAR(64) NOT NULL,
  endpoint_url TEXT,
  reference_url TEXT
);