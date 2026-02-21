
const { Client } = require('pg');

const DB_CONFIG = {
    user: 'postgres', host: 'localhost', database: 'safedrive_apps', password: 'Siraj.9892', port: 5432,
};

async function inspect() {
    const client = new Client(DB_CONFIG);
    try {
        await client.connect();

        console.log("=== TABLE: users ===");
        const resUsers = await client.query("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'");
        console.log(resUsers.rows.map(r => r.column_name).join(", "));

        console.log("\n=== TABLE: vehicles ===");
        const resVehicles = await client.query("SELECT column_name FROM information_schema.columns WHERE table_name = 'vehicles'");
        console.log(resVehicles.rows.map(r => r.column_name).join(", "));

    } catch (e) { console.error(e); }
    finally { await client.end(); }
}
inspect();
