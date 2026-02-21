
const { Client } = require('pg');

const DB_CONFIG = {
    user: 'postgres',
    host: 'localhost',
    database: 'safedrive_apps',
    password: 'Siraj.9892',
    port: 5432,
};

async function update() {
    const client = new Client(DB_CONFIG);
    try {
        await client.connect();

        const email = "testuser3@example.com";
        console.log(`Updating Points for ${email}...`);

        // 1. Get User ID
        const res = await client.query('SELECT user_id FROM users WHERE email = $1', [email]);
        if (res.rows.length === 0) {
            console.log("User not found!");
            return;
        }
        const userId = res.rows[0].user_id;

        // 2. Update Total Earned Points AND Wallet Balance
        await client.query('UPDATE users SET total_earned_points = 50000, wallet_balance = 500.0 WHERE user_id = $1', [userId]);
        console.log("  Updated total_earned_points = 50,000, wallet_balance = 500.0");

        // 3. Add Transaction History
        await client.query(`
            INSERT INTO transactions (user_id, type, amount, description, created_at)
            VALUES ($1, 'EARNED', 500.0, 'Welcome Bonus (Test)', NOW())
        `, [userId]);
        console.log("  Added Transaction: Welcome Bonus");

    } catch (e) { console.error(e); }
    finally { await client.end(); }
}

update();
