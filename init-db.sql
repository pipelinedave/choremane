-- Table for chores
CREATE TABLE IF NOT EXISTS chores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    interval_days INT NOT NULL,
    due_date DATE NOT NULL,
    done BOOLEAN DEFAULT FALSE,
    done_by VARCHAR(255),
    owner_email VARCHAR(255),
    is_private BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE
);

-- Table for chore logs
CREATE TABLE IF NOT EXISTS chore_logs (
    id SERIAL PRIMARY KEY,
    chore_id INT,
    done_by VARCHAR(255),
    done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50) NOT NULL,
    action_details JSON DEFAULT NULL,
    FOREIGN KEY (chore_id) REFERENCES chores (id) ON DELETE CASCADE
);
