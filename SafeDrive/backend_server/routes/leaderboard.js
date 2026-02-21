const express = require('express');
const router = express.Router();
const db = require('../db');

// Get Top 10 Drivers
router.get('/top', async (req, res) => {
    try {
        const query = 'SELECT name, wallet_balance, total_earned_points FROM users ORDER BY total_earned_points DESC LIMIT 10';
        const result = await db.query(query);

        const leaderboard = result.rows.map((user, index) => ({
            rankPosition: index + 1,
            ownerName: user.name || 'Unknown',
            walletPoints: parseInt(user.total_earned_points || 0),
            rankScore: (parseInt(user.total_earned_points || 0) / 10),
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || 'User')}`
        }));

        res.json(leaderboard);
    } catch (err) {
        console.error(err.message);
        res.status(500).json({ msg: 'Server Error' });
    }
});

// Get My Rank (Simplified)
router.get('/:plateNumber', async (req, res) => {
    try {
        // Return dummy rank for now to prevent errors
        res.json({
            rankPosition: 1,
            ownerName: "You",
            walletPoints: 500,
            rankScore: 50.0
        });
    } catch (err) {
        res.status(500).json({ msg: 'Server Error' });
    }
});

module.exports = router;
