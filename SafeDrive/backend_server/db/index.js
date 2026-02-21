
const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});

// --- Unified Cloud Pool (Neon) ---
const cloudPool = new Pool({
    user: process.env.CLOUD_DB_USER,
    host: process.env.CLOUD_DB_HOST,
    database: process.env.CLOUD_DB_NAME,
    password: process.env.CLOUD_DB_PASS,
    port: process.env.CLOUD_DB_PORT,
    ssl: { rejectUnauthorized: false } // Required for Neon
});

cloudPool.on('error', (err, client) => {
    console.error('❌ [DATABASE] Neon Cloud Connection Error:', err.message);
});

module.exports = {
    // Default 'query' now points to Cloud (Auth, Wallet, etc.)
    query: (text, params) => cloudPool.query(text, params),
    // 'trafficQuery' kept for backward compatibility with existing reward/rto logic
    trafficQuery: (text, params) => cloudPool.query(text, params),
    pool: cloudPool, // All references now hit the cloud
    cloudPool
};
