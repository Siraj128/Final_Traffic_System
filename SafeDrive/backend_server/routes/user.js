const express = require('express');
const router = express.Router();
const db = require('../db');
const auth = require('../middleware/auth');

// Get My Profile (Uses Auth Middleware)
router.get('/me', auth, async (req, res) => {
    try {
        const query = 'SELECT user_id, name, full_name, email, mobile, avatar_url, total_earned_points, total_earned_points AS wallet_points, wallet_balance, wallet_balance AS balance, role, created_at FROM users WHERE user_id = $1';
        const result = await db.query(query, [req.user.id]);

        if (result.rows.length === 0) return res.status(404).json({ msg: 'User not found' });

        res.json(result.rows[0]);
    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

// Update Profile
router.put('/update', auth, async (req, res) => {
    const { name, avatar_url } = req.body;
    try {
        const query = `
            UPDATE users 
            SET name = COALESCE($1, name), 
                full_name = COALESCE($1, full_name), 
                avatar_url = COALESCE($2, avatar_url)
            WHERE user_id = $3
            RETURNING *
        `;
        const result = await db.query(query, [name, avatar_url, req.user.id]);
        res.json(result.rows[0]);
    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

module.exports = router;
