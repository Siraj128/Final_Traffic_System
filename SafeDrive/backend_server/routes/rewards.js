const express = require('express');
const router = express.Router();
const db = require('../db');

/**
 * 💸 [ANPR REWARD ENDPOINT]
 * Receives points from the AI Python scripts.
 * Logic: 
 * 1. Normalize Plate.
 * 2. If Registered -> Update user points + wallet.
 * 3. If Unregistered -> Store as "Ghost Data" in user_rewards (Cloud DB).
 */
router.post('/credit', async (req, res) => {
    const { plate_number, points, reason, junction_id } = req.body;

    if (!plate_number || !points) {
        return res.status(400).json({ success: false, message: "Missing plate or points" });
    }

    const normalizedPlate = plate_number.toUpperCase().replace(/[\s-]/g, '');
    console.log(`📡 [REWARDS] Received Reward Request: ${normalizedPlate} (+${points} pts)`);

    try {
        // 1. Check if user exists (via vehicles table)
        const vehicleRes = await db.query(
            'SELECT user_id FROM vehicles WHERE plate_number = $1',
            [normalizedPlate]
        );

        if (vehicleRes.rows.length > 0) {
            const userId = vehicleRes.rows[0].user_id;

            // Update user balance
            const earnedWallet = (points / 100) * 0.50; // Ratio from settings.py

            const updateQuery = `
                UPDATE users 
                SET total_earned_points = total_earned_points + $1,
                    wallet_balance = wallet_balance + $2
                WHERE user_id = $3
                RETURNING total_earned_points, wallet_balance
            `;
            await db.query(updateQuery, [points, earnedWallet, userId]);

            // Log Transaction
            const txnQuery = `
                INSERT INTO transactions (user_id, type, amount, description)
                VALUES ($1, 'EARNED', $2, $3)
            `;
            await db.query(txnQuery, [userId, points, `${reason || 'Traffic Compliance'} (Junction: ${junction_id || 'Unknown'})`]);

            console.log(`✅ [REWARDS] Credited User ${userId} for plate ${normalizedPlate}`);
            return res.json({ success: true, message: "Reward credited to user wallet", ghost: false });
        } else {
            // 2. GHOST / RTO DATA: Check Cloud DB Registry first (Phone-based)
            const rtoQuery = `
                SELECT "phone_number", "email", "owner_name", "driver_license_id", "v1_plate", "v1_type", "v2_plate", "v2_type" 
                FROM "rto_registry" 
                WHERE REPLACE(REPLACE("v1_plate", '-', ''), ' ', '') = $1 
                   OR REPLACE(REPLACE("v2_plate", '-', ''), ' ', '') = $1
            `;
            const rtoRes = await db.trafficQuery(rtoQuery, [normalizedPlate]);

            let targetPhone, targetEmail, targetName, targetLicense;
            if (rtoRes.rows.length > 0) {
                const row = rtoRes.rows[0];
                targetPhone = row.phone_number;
                targetEmail = row.email;
                targetName = row.owner_name;
                targetLicense = row.driver_license_id;
                console.log(`🔍 [REWARDS] Found in RTO Registry: ${targetPhone} (${targetName})`);
            } else {
                targetPhone = `ghost_${normalizedPlate}`;
                targetEmail = `ghost_${normalizedPlate}@traffic.com`;
                targetName = "Ghost Owner";
                targetLicense = "GHOST-LKUP";
                console.log(`👻 [REWARDS] Not in RTO. Using Ghost ID: ${targetPhone}`);
            }

            const rto = rtoRes.rows[0] || {};
            const isV2 = rto.v2_plate && rto.v2_plate.toUpperCase().replace(/[\s-]/g, '') === normalizedPlate;

            const v1_p = isV2 ? 0 : points;
            const v2_p = isV2 ? points : 0;

            const ghostQuery = `
                INSERT INTO "user_rewards" 
                ("phone_number", "email", "owner_name", "driver_license_id", "v1_plate", "v1_type", "v2_plate", "v2_type", "vehicle_type", "total_points", "v1_points", "v2_points", "last_updated", "updated_at") 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()) 
                ON CONFLICT ("phone_number") DO UPDATE SET 
                    "email" = EXCLUDED."email", 
                    "owner_name" = EXCLUDED."owner_name", 
                    "driver_license_id" = EXCLUDED."driver_license_id", 
                    "v1_points" = "user_rewards"."v1_points" + EXCLUDED."v1_points", 
                    "v2_points" = "user_rewards"."v2_points" + EXCLUDED."v2_points", 
                    "total_points" = ("user_rewards"."v1_points" + EXCLUDED."v1_points") + ("user_rewards"."v2_points" + EXCLUDED."v2_points"),
                    "v1_type" = EXCLUDED."v1_type", 
                    "v2_type" = EXCLUDED."v2_type", 
                    "vehicle_type" = EXCLUDED."vehicle_type", 
                    "last_updated" = NOW(), 
                    "updated_at" = NOW()`;

            await db.trafficQuery(ghostQuery, [
                targetPhone, targetEmail, targetName, targetLicense,
                rto.v1_plate || normalizedPlate, rto.v1_type || 'Car',
                rto.v2_plate || null, rto.v2_type || 'Car',
                rto.v1_type || 'Car', // vehicle_type ($9)
                (v1_p + v2_p), // total_points ($10)
                v1_p, // v1_points ($11)
                v2_p // v2_points ($12)
            ]);

            return res.json({ success: true, message: `Points recorded for ${isV2 ? 'V2' : 'V1'} (${normalizedPlate})`, ghost: true });
        }

    } catch (err) {
        console.error("❌ [REWARDS] Processing Error:", err.message);
        res.status(500).json({ success: false, message: "Internal Server Error" });
    }
});

// Get Leaderboard (Rewritten for Postgres)
router.get('/leaderboard', async (req, res) => {
    try {
        const query = `
            SELECT name, total_earned_points as rewards, wallet_balance 
            FROM users 
            ORDER BY total_earned_points DESC 
            LIMIT 10
        `;
        const result = await db.query(query);
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).send('Server Error');
    }
});

module.exports = router;
