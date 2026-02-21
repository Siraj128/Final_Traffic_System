const express = require('express');
const router = express.Router();
const db = require('../db');
const auth = require('../middleware/auth');

// @route   GET /api/vehicles/my
// @desc    Get current user's vehicles
// @access  Private
router.get('/my', auth, async (req, res) => {
    console.log(`[DEBUG] GET /vehicles/my Request from User: ${req.user.id}`);
    try {
        // Query vehicles (Schema uses vehicle_id)
        const query = 'SELECT id AS vehicle_id, user_id, plate_number, vehicle_type, is_primary, rto_slot, created_at FROM vehicles WHERE user_id = $1 ORDER BY rto_slot ASC, created_at DESC';
        const result = await db.query(query, [req.user.id]);

        console.log(`[DEBUG] Found ${result.rows.length} vehicles for User ${req.user.id}:`, result.rows);
        res.json({ success: true, data: result.rows });
    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

// @route   POST /api/vehicles/add
// @desc    Add a vehicle
// @access  Private
router.post('/add', auth, async (req, res) => {
    const { plate_number, vehicle_type } = req.body;

    if (!plate_number) {
        return res.status(400).json({ msg: 'Plate number is required' });
    }

    const normalizedPlate = plate_number.toUpperCase().replace(/[\s-]/g, '');

    try {
        // 1. Upsert Vehicle (Claim it)
        const upsertQuery = `
            INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary)
            VALUES ($1, $2, $3, FALSE)
            ON CONFLICT (plate_number) 
            DO UPDATE SET user_id = $1;
        `;
        await db.query(upsertQuery, [req.user.id, normalizedPlate, vehicle_type || 'Car']);

        // 2. Link Rewards (Update Traffic DB)
        try {
            const updateTrafficLink = `
                UPDATE user_rewards
                SET user_id = $1 
                WHERE v1_plate = $2 OR v2_plate = $2
            `;
            await db.trafficQuery(updateTrafficLink, [req.user.id, normalizedPlate]);
        } catch (err) {
            console.warn("Traffic DB Link warning:", err.message);
        }

        // 3. Return the vehicle object
        const newVeh = await db.query('SELECT id AS vehicle_id, plate_number, vehicle_type, is_primary, rto_slot FROM vehicles WHERE plate_number = $1', [normalizedPlate]);
        res.json({ success: true, data: newVeh.rows[0] });

    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

module.exports = router;
