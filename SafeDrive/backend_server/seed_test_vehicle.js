
const { Client } = require('pg');
const bcrypt = require('bcryptjs');

// Config
const DB_CONFIG = {
    user: 'postgres',
    host: 'localhost',
    database: 'safedrive_apps',
    password: 'Siraj.9892',
    port: 5432,
};

async function seed() {
    const client = new Client(DB_CONFIG);
    try {
        await client.connect();
        console.log("Connected to DB...");

        const email = "testuser3@example.com";
        const password = "password123";
        const salt = await bcrypt.genSalt(10);
        const hashed = await bcrypt.hash(password, salt);

        // 1. Insert User
        console.log(`Creating User: ${email}...`);

        let res = await client.query('SELECT user_id FROM users WHERE email = $1', [email]);
        let userId;

        if (res.rows.length > 0) {
            userId = res.rows[0].user_id;
            console.log(`  User already exists (ID: ${userId})`);
        } else {
            res = await client.query(
                `INSERT INTO users (name, email, password_hash, mobile, wallet_balance)
                 VALUES ($1, $2, $3, $4, $5) RETURNING user_id`,
                ["Test User 3", email, hashed, "9999999999", 500.0]
            );
            userId = res.rows[0].user_id;
            console.log(`  Created User ID: ${userId}`);
        }

        // 2. Insert Vehicle
        const plate = "MH12TEST03";
        console.log(`Adding Vehicle: ${plate}...`);

        res = await client.query('SELECT vehicle_id FROM vehicles WHERE plate_number = $1', [plate]);
        if (res.rows.length > 0) {
            console.log(`  Vehicle already exists.`);
        } else {
            await client.query(
                `INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary)
                 VALUES ($1, $2, $3, $4)`,
                [userId, plate, "Car", true]
            );
            console.log(`  Vehicle Added.`);
        }

        console.log("\nSUCCESS! Login with:");
        console.log(`Email: ${email}`);
        console.log(`Pass:  ${password}`);

    } catch (err) {
        console.error("ERROR:", err);
    } finally {
        await client.end();
    }
}

seed();
