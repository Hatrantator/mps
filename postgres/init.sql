CREATE TABLE IF NOT EXISTS farms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS floors (
    id SERIAL PRIMARY KEY,
    farm_id INT NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    level INT,  -- optional numeric floor number
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pots (
    id SERIAL PRIMARY KEY,
    floor_id INT NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    location_code VARCHAR(50), -- e.g. "A1", "Row3-Col2"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plants (
    id SERIAL PRIMARY KEY,
    pot_id INT NOT NULL REFERENCES pots(id) ON DELETE SET NULL,
    qr_code VARCHAR(100) UNIQUE NOT NULL,
    species VARCHAR(100),
    variety VARCHAR(100),
    germination_date DATE,
    planting_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS harvest_dates (
    id SERIAL PRIMARY KEY,
    plant_id INT NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    harvest_date DATE NOT NULL,
    yield_weight DECIMAL(10,2), -- optional yield per harvest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
