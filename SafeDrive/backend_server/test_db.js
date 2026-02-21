
const { Pool } = require('pg');

const pool = new Pool({
    user: 'safedrive_user', // New User
    host: '127.0.0.1',
    database: 'safedrive_apps',
    password: 'safedrive',
    port: 5432,
});

async function runTest() {
    console.log("Testing safedrive_user connecting to safedrive_apps...");
    try {
        const res = await pool.query('SELECT NOW()');
        console.log('✅ Connection Success:', res.rows[0]);
    } catch (err) {
        console.error('❌ Connection Failed:', err.message);
    } finally {
        await pool.end();
    }
}

runTest();
