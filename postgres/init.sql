CREATE TABLE IF NOT EXISTS plants (
    id SERIAL PRIMARY KEY,
    qr_code VARCHAR(100),
    species VARCHAR(100),
    variety VARCHAR(100),
    germination_date DATE,
    planting_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
