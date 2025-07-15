--BigQuery products table
CREATE TABLE IF NOT EXISTS `your_project_id.your_dataset_id.your_table_name` (
  asin STRING NOT NULL,
  product_name STRING,
  product_url STRING,
  is_available STRING,
  brand STRING,
  brand_url STRING,
  seller STRING,
  seller_url STRING,
  rating FLOAT64,
  review_count INT64,
  past_count STRING,
  discount STRING,
  price FLOAT64,
  mrp FLOAT64,
  offers ARRAY<STRING>,
  features ARRAY<STRING>,
  overview STRING,
  together ARRAY<STRUCT<
    product_name STRING,
    product_price FLOAT64
  >>,
  summary STRING,
  mentions ARRAY<STRING>
);